"""One entry point that ties loading, validation, preprocessing and summarization together.

The CLI (main.py) and any UI should call these functions instead of
repeating the load / validate / summarize steps.
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional

from .data_loader import iter_path
from .preprocessing import NLTKDataError
from .summarizer import TextSummarizer
from .validation import InvalidInputError, validate_method, validate_num_sentences

logger = logging.getLogger(__name__)


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


def iter_summaries(
    path, num_sentences: int = 3, method: str = "frequency"
) -> Iterator[SummaryResult]:
    """Yield one SummaryResult at a time for every article in a file or folder.

    Nothing is collected in memory, so this suits large datasets. Bad options
    raise InvalidInputError, a missing file raises FileNotFoundError and a
    file of the wrong type raises DataLoadError right away. Problems inside a
    file (bad JSON, a row without text) raise DataLoadError when the reader
    reaches them, which stops the run. An article that fails validation, or
    hits an unexpected error, is reported in its SummaryResult (error set) and
    the rest still run. Missing NLTK data raises NLTKDataError and stops the
    run, because every article would fail the same way.
    """
    method = validate_method(method)
    num_sentences = validate_num_sentences(num_sentences)
    articles = iter_path(path)
    return _summarize_stream(articles, TextSummarizer(method=method), num_sentences)


def _summarize_stream(articles, summarizer, num_sentences):
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
        except NLTKDataError:
            # Every article would fail the same way, so stop the whole run
            raise
        except Exception as error:  # one unexpected failure must not stop the batch
            logger.debug(
                "Unexpected error for article %r", article.id, exc_info=True
            )
            result.error = f"Unexpected {type(error).__name__}: {error}"
        yield result


def summarize_path(
    path, num_sentences: int = 3, method: str = "frequency"
) -> List[SummaryResult]:
    """Summarize every article in a file or folder and return a list.

    Same rules as iter_summaries, but nothing is returned if the run stops
    with an error. Use iter_summaries for very large inputs.
    """
    return list(iter_summaries(path, num_sentences=num_sentences, method=method))
