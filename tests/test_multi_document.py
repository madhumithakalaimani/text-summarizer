from summarizer.pipeline import summarize_multiple
from summarizer.validation import InvalidInputError
import pytest


def test_summarize_multiple_combines_documents():
    docs = [
        "Cats are small mammals. Cats are popular pets. Cats like to sleep.",
        "Dogs are loyal animals. Dogs are popular pets. Dogs like to play.",
    ]
    result = summarize_multiple(docs, num_sentences=2)
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_summarize_multiple_single_document():
    docs = [
        "Paris is the capital of France. Paris has the Eiffel Tower. "
        "Paris is beautiful in every season. Paris draws millions of visitors "
        "each year. Paris is known for its museums and cafes."
    ]
    result = summarize_multiple(docs, num_sentences=1)
    assert isinstance(result, str)
    assert len(result.strip()) > 0


def test_summarize_multiple_empty_list_raises():
    with pytest.raises(InvalidInputError):
        summarize_multiple([])


def test_summarize_multiple_textrank_method():
    docs = [
        "The stock market rose today. Investors were optimistic. Trading volume was high.",
        "Tech stocks led the gains. Analysts praised the results. The rally continued into the afternoon.",
    ]
    result = summarize_multiple(docs, num_sentences=2, method="textrank")
    assert isinstance(result, str)
    assert len(result.strip()) > 0
