"""Tests for the summarize_text caching added on Day 16."""
import pytest

from summarizer.pipeline import _cached_summarize_text, summarize_text
from summarizer.validation import InvalidInputError

TEXT = (
    "The city council approved a new budget for public parks on Monday. "
    "The budget adds money for playgrounds and walking trails across the city. "
    "Residents had asked for safer parks for many years. "
    "Council members said the parks budget will grow again next year. "
    "A local group will plant trees along the new walking trails. "
    "Work on the first playground starts in the spring."
)


def test_identical_calls_hit_the_cache():
    _cached_summarize_text.cache_clear()
    summarize_text(TEXT, 2, "frequency")
    summarize_text(TEXT, 2, "frequency")
    info = _cached_summarize_text.cache_info()
    assert info.hits >= 1


def test_cached_result_matches_uncached_result():
    _cached_summarize_text.cache_clear()
    first = summarize_text(TEXT, 2, "frequency")
    second = summarize_text(TEXT, 2, "frequency")
    assert first == second


def test_non_string_text_raises_invalid_input_error_not_type_error():
    with pytest.raises(InvalidInputError):
        summarize_text(["not", "a", "string"], 2, "frequency")
