"""Direct tests for TextSummarizer.summarize() inputs and defaults."""
import pytest

from summarizer.summarizer import TextSummarizer
from summarizer.validation import InvalidInputError

TEXT = (
    "The city council approved a new budget for public parks on Monday. "
    "The budget adds money for playgrounds and walking trails across the city. "
    "Residents had asked for safer parks for many years. "
    "Council members said the parks budget will grow again next year. "
    "A local group will plant trees along the new walking trails. "
    "Work on the first playground starts in the spring."
)

METHODS = ["frequency", "textrank"]


def test_default_method_is_frequency():
    assert TextSummarizer().method == "frequency"


def test_method_name_is_normalized():
    assert TextSummarizer("  TextRank ").method == "textrank"


@pytest.mark.parametrize("bad", [None, 123, ["a", "b"]])
def test_non_string_text_raises(bad):
    with pytest.raises(InvalidInputError, match="must be a string"):
        TextSummarizer().summarize(bad)


@pytest.mark.parametrize("blank", ["", "   ", "\n\t "])
def test_empty_or_blank_text_raises(blank):
    with pytest.raises(InvalidInputError, match="empty"):
        TextSummarizer().summarize(blank)


@pytest.mark.parametrize("bad", [0, -1, True, 2.5, "3"])
def test_invalid_num_sentences_raises(bad):
    with pytest.raises(InvalidInputError):
        TextSummarizer().summarize(TEXT, bad)


@pytest.mark.parametrize("method", METHODS)
def test_default_returns_three_sentences(method):
    summary = TextSummarizer(method).summarize(TEXT)
    assert summary.count(".") == 3


@pytest.mark.parametrize("method", METHODS)
def test_one_sentence_requested_returns_one_sentence(method):
    summary = TextSummarizer(method).summarize(TEXT, 1)
    assert summary.count(".") == 1
    assert summary in TEXT


@pytest.mark.parametrize("method", METHODS)
def test_surrounding_whitespace_is_ignored(method):
    summarizer = TextSummarizer(method)
    padded = "  \n" + TEXT + "\n  "
    assert summarizer.summarize(padded) == summarizer.summarize(TEXT)


@pytest.mark.parametrize("method", METHODS)
def test_same_instance_gives_the_same_summary_twice(method):
    summarizer = TextSummarizer(method)
    assert summarizer.summarize(TEXT, 2) == summarizer.summarize(TEXT, 2)
