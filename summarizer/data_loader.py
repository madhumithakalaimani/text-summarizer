"""Data pipeline: load articles from .txt, .md, .csv and .json files."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = (".txt", ".md", ".csv", ".json")
TEXT_FIELDS = ("text", "content", "article", "body")
TITLE_FIELDS = ("title", "headline")


class DataLoadError(ValueError):
    """Raised when a file cannot be read or has an unexpected structure."""


@dataclass
class Article:
    id: str
    title: str
    text: str
    source: str


def _pick(record, names):
    """Return the first matching field (case-insensitive) as a stripped string."""
    lowered = {str(key).strip().lower(): value for key, value in record.items()}
    for name in names:
        value = lowered.get(name)
        if value is not None:
            return str(value).strip()
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


def _load_text(path):
    text = path.read_text(encoding="utf-8-sig").strip()
    return [Article(path.stem, path.stem, text, path.name)]


def _load_csv(path):
    csv.field_size_limit(10_000_000)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return [_to_article(row, i, path.name) for i, row in enumerate(rows, start=1)]


def _load_json(path):
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
    return [_to_article(item, i, path.name) for i, item in enumerate(data, start=1)]


def load_articles(path):
    """Load all articles from one file. Returns a list of Article objects."""
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
    try:
        if extension in (".txt", ".md"):
            articles = _load_text(path)
        elif extension == ".csv":
            articles = _load_csv(path)
        else:
            articles = _load_json(path)
    except UnicodeDecodeError as error:
        raise DataLoadError(f"{path.name} is not valid UTF-8 text: {error}") from error
    except json.JSONDecodeError as error:
        raise DataLoadError(f"{path.name} is not valid JSON: {error}") from error
    if not articles:
        raise DataLoadError(f"No articles found in {path.name}")
    return articles


def load_directory(folder):
    """Load every supported file in a folder (not recursive)."""
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")
    articles = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            articles.extend(load_articles(path))
    if not articles:
        raise DataLoadError(f"No supported files found in {folder}")
    return articles
