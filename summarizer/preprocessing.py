"""Basic text preprocessing: cleaning, sentence splitting, tokenization."""
import re
from functools import lru_cache
from typing import List, Tuple

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

_NLTK_RESOURCES = {
    "punkt": "tokenizers/punkt",
    "punkt_tab": "tokenizers/punkt_tab",
    "stopwords": "corpora/stopwords",
}


class NLTKDataError(RuntimeError):
    """Raised when required NLTK data is missing and could not be downloaded."""


def _has_resource(path: str) -> bool:
    try:
        nltk.data.find(path)
    except LookupError:
        return False
    return True


@lru_cache(maxsize=None)
def ensure_nltk_data() -> None:
    """Make sure the required NLTK data is installed, downloading it if needed.

    Raises NLTKDataError with a clear message if something is still missing
    afterwards (for example when there is no network connection). A failed
    call is not cached, so the next call tries the download again.
    """
    missing = []
    for name, path in _NLTK_RESOURCES.items():
        if _has_resource(path):
            continue
        try:
            nltk.download(name, quiet=True)
        except Exception:
            pass  # judged by the re-check below, whatever the network error was
        if not _has_resource(path):
            missing.append(name)
    if missing:
        raise NLTKDataError(
            "Required NLTK data is missing and could not be downloaded: "
            + ", ".join(missing)
            + ". Check your internet connection, or install it with: "
            "python -m nltk.downloader " + " ".join(missing)
        )


# Trailing punctuation that is left behind when a URL is removed, so that
# "See https://x.com. Next" keeps the period that ends the sentence.
_URL_TRAILING = ".,;:!?)]" + chr(34) + chr(39) + chr(0x201D) + chr(0x2019)
_URL_RE = re.compile(r"\s*https?://\S*[^\s" + re.escape(_URL_TRAILING) + "]")


def clean_text(text: str) -> str:
    """Normalize whitespace and strip URLs."""
    text = _URL_RE.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Characters that can end a sentence (quotes and brackets may follow the period)
_END_PUNCT = ".!?)" + chr(34) + chr(39) + chr(0x201D) + chr(0x2019)
_MAX_HEADING_WORDS = 12


def _is_heading(line: str, next_line: str) -> bool:
    """A short line with no closing punctuation, followed by a capitalized line."""
    words = line.split()
    return (
        0 < len(words) <= _MAX_HEADING_WORDS
        and line[-1] not in _END_PUNCT
        and next_line[:1].isupper()
    )


def _split_with_flags(text: str) -> List[Tuple[str, bool]]:
    """Split text into (sentence, is_heading) pairs.

    A headline (a short line with no closing punctuation, followed by a line
    that starts with a capital letter) becomes its own sentence instead of
    being glued to the first sentence after it.
    """
    ensure_nltk_data()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    sentences: List[Tuple[str, bool]] = []
    buffer: List[str] = []

    def flush() -> None:
        if buffer:
            for s in sent_tokenize(clean_text(" ".join(buffer))):
                sentences.append((s, False))
            buffer.clear()

    for i, line in enumerate(lines):
        if i + 1 < len(lines) and _is_heading(line, lines[i + 1]):
            flush()
            heading = clean_text(line)
            if heading:
                sentences.append((heading, True))
        else:
            buffer.append(line)
    flush()
    return sentences


def split_sentences(text: str, include_headings: bool = True) -> List[str]:
    """Split text into sentences; include_headings=False leaves headlines out."""
    pairs = _split_with_flags(text)
    return [s for s, is_heading in pairs if include_headings or not is_heading]


@lru_cache(maxsize=None)
def _stopword_set(language: str) -> frozenset:
    """Load the stopword list once per language instead of once per sentence."""
    ensure_nltk_data()
    return frozenset(stopwords.words(language))


def _is_word(token: str) -> bool:
    """True for alphabetic tokens, including hyphenated words like well-known."""
    return all(part.isalpha() for part in token.split("-"))


def tokenize(sentence: str, language: str = "english") -> List[str]:
    """Lowercase, tokenize, and drop stopwords and non-alphabetic tokens.

    Hyphenated words such as "well-known" are kept as one token.
    """
    ensure_nltk_data()
    stops = _stopword_set(language)
    return [
        w for w in word_tokenize(sentence.lower())
        if _is_word(w) and w not in stops
    ]


def preprocess(text: str, include_headings: bool = True) -> List[Tuple[str, List[str]]]:
    """Return a list of (original_sentence, tokens) pairs.

    Set include_headings=False to leave headlines out.
    """
    return [(s, tokenize(s)) for s in split_sentences(text, include_headings)]
