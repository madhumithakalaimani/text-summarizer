"""Data pipeline: load articles from .txt, .md, .csv and .json files."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

SUPPORTED_EXTENSIONS = (".txt", ".md", ".csv", ".json")
TEXT_FIELDS = ("text", "content", "article", "body")
TITLE_FIELDS = ("title", "headline")

# Allow very long text fields (the csv module stops at 128 KB by default)
csv.field_size_limit(10_000_000)


class DataLoadError(ValueError):
    """Raised when a file cannot be read or has an unexpected structure."""


@dataclass
class Article:
    id: str
    title: str
    text: str
    source: str


def _pick(record, names):
    """Return the first matching field (case-insensitive) as a stripped
    string, skipping fields that are missing or blank so a later, populated
    field is still used."""
    lowered = {str(key).strip().lower(): value for key, value in record.items()}
    for name in names:
        value = lowered.get(name)
        if value is None:
            continue
        stripped = str(value).strip()
        if stripped:
            return stripped
    return None


def _to_article(record, index, source):
    if isinstance(record, str):
        return Article(str(index), "", record.strip(), source)
    if not isinstance(record, dict):
        raise DataLoadError(
            f"{source}: item {index} must be an object or a string, "
            f"got {type(record).__name__}"
        )
    text = _pick(record, TEXT_FIELDS)
    if text is None:
        raise DataLoadError(
            f"{source}: item {index} has no text field "
            f"(expected one of {', '.join(TEXT_FIELDS)})"
        )
    article_id = _pick(record, ("id",)) or str(index)
    title = _pick(record, TITLE_FIELDS) or ""
    return Article(article_id, title, text, source)


def _read_text(path):
    text = path.read_text(encoding="utf-8-sig").strip()
    yield Article(path.stem, path.stem, text, path.name)


def _read_csv(path):
    # Rows are read one at a time, so a huge CSV never sits in memory.
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=1):
            yield _to_article(row, index, path.name)


def _read_json(path):
    # The json module cannot read a file piece by piece, so the whole file is
    # parsed at once. The articles are still handed out one at a time.
    with path.open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and isinstance(data.get("articles"), list):
        data = data["articles"]
    elif isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise DataLoadError(
            f"{path.name}: expected a list of articles or an object, "
            f"got {type(data).__name__}"
        )
    for index, item in enumerate(data, start=1):
        yield _to_article(item, index, path.name)


_READERS = {
    ".txt": _read_text,
    ".md": _read_text,
    ".csv": _read_csv,
    ".json": _read_json,
}


def _stream_file(path, reader):
    """Yield articles from one file; read problems become DataLoadError."""
    count = 0
    try:
        for article in reader(path):
            count += 1
            yield article
    except UnicodeDecodeError as error:
        raise DataLoadError(f"{path.name} is not valid UTF-8 text: {error}") from error
    except json.JSONDecodeError as error:
        raise DataLoadError(f"{path.name} is not valid JSON: {error}") from error
    except (OSError, csv.Error) as error:
        raise DataLoadError(f"{path.name} could not be read: {error}") from error
    if count == 0:
        raise DataLoadError(f"No articles found in {path.name}")


def iter_articles(path) -> Iterator[Article]:
    """Yield the articles of one file, one at a time.

    A missing file, a folder or an unsupported type is reported right away.
    Problems inside the file (bad JSON, a bad row, invalid UTF-8) are raised
    as DataLoadError when the reader reaches them.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise DataLoadError(f"Not a file: {path}")
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise DataLoadError(
            f"Unsupported file type '{extension}' for {path.name}. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return _stream_file(path, _READERS[extension])


def _stream_files(paths):
    for path in paths:
        yield from iter_articles(path)


def iter_directory(folder) -> Iterator[Article]:
    """Yield the articles of every supported file in a folder (not recursive)."""
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")
    paths = [
        path
        for path in sorted(folder.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not paths:
        raise DataLoadError(f"No supported files found in {folder}")
    return _stream_files(paths)


def iter_path(path) -> Iterator[Article]:
    """Yield the articles of a file or of every supported file in a folder."""
    path = Path(path)
    return iter_directory(path) if path.is_dir() else iter_articles(path)


def load_articles(path):
    """Load all articles from one file. Returns a list of Article objects."""
    return list(iter_articles(path))


def load_directory(folder):
    """Load every supported file in a folder (not recursive) into a list."""
    return list(iter_directory(folder))
