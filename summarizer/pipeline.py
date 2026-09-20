"""One entry point that ties loading, validation, preprocessing and summarization together.

The CLI (main.py) and any UI should call these functions instead of
repeating the load / validate / summarize steps.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .data_loader import load_articles, load_directory
from .summarizer import TextSummarizer
from .validation import InvalidInputError, validate_method, validate_num_sentences


@dataclass
class SummaryResult:
    """Outcome for one article: a summary, or the reason it was skipped."""

    article_id: object
    title: Optional[str]
    source: object
    summary: Optional[str] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


def summarize_text(text: str, num_sentences: int = 3, method: str = "frequency") -> str:
    """Summarize one text string. Raises InvalidInputError on bad input."""
    return TextSummarizer(method=method).summarize(text, num_sentences=num_sentences)


def summarize_path(path, num_sentences: int = 3, method: str = "frequency") -> List[SummaryResult]:
    """Summarize every article in a file or folder.

    Bad options raise InvalidInputError; a missing file raises FileNotFoundError;
    an unreadable file raises DataLoadError. An article that fails validation is
    reported in its SummaryResult (error set) and the rest still run.
    """
    method = validate_method(method)
    num_sentences = validate_num_sentences(num_sentences)

    path = Path(path)
    articles = load_directory(path) if path.is_dir() else load_articles(path)

    summarizer = TextSummarizer(method=method)
    results: List[SummaryResult] = []
    for article in articles:
        result = SummaryResult(
            article_id=article.id, title=article.title, source=article.source
        )
        try:
            result.summary = summarizer.summarize(
                article.text, num_sentences=num_sentences
            )
        except InvalidInputError as error:
            result.error = str(error)
        results.append(result)
    return results
