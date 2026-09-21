"""Performance benchmarks for the summarizer pipeline.

Uses pytest-benchmark to time frequency and textrank summarization
across short, medium and long inputs. Run with: pytest tests/test_benchmark_performance.py -v
"""
import pytest

from summarizer.pipeline import summarize_text

BASE_TEXT = (
    "The city council approved a new budget for public parks on Monday. "
    "The budget adds money for playgrounds and walking trails across the city. "
    "Residents had asked for safer parks for many years. "
    "Council members said the parks budget will grow again next year. "
    "A local group will plant trees along the new walking trails. "
    "Work on the first playground starts in the spring."
)

SHORT_TEXT = BASE_TEXT
MEDIUM_TEXT = BASE_TEXT * 5
LONG_TEXT = BASE_TEXT * 20

METHODS = ["frequency", "textrank"]
SIZES = [
    ("short", SHORT_TEXT),
    ("medium", MEDIUM_TEXT),
    ("long", LONG_TEXT),
]


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("size_name,text", SIZES, ids=[s[0] for s in SIZES])
def test_summarize_benchmark(benchmark, method, size_name, text):
    result = benchmark(summarize_text, text, 3, method)
    assert isinstance(result, str)
    assert len(result) > 0
