"""Day 11: error handling for missing NLTK data (network problems) and unexpected errors."""
import json
import sys
from types import SimpleNamespace

import pytest

import app as app_module
import main as main_module
from summarizer import preprocessing
from summarizer.pipeline import (
    SummaryResult,
    _summarize_stream,
    iter_summaries,
    summarize_text,
)
from summarizer.preprocessing import NLTKDataError, ensure_nltk_data
from summarizer.summarizer import TextSummarizer
from summarizer.validation import InvalidInputError

GOOD_TEXT = "The quick brown fox jumps over the lazy dog. " * 5


@pytest.fixture(autouse=True)
def fresh_nltk_cache():
    """ensure_nltk_data is cached, so start and finish every test with an empty cache."""
    ensure_nltk_data.cache_clear()
    yield
    ensure_nltk_data.cache_clear()


class FakeNltk:
    """Stands in for the NLTK data folder: nothing is installed until a download works."""

    def __init__(self, works=True):
        self.works = works
        self.installed = set()
        self.calls = []

    def has_resource(self, path):
        return path in self.installed

    def download(self, name, quiet=True):
        self.calls.append(name)
        if self.works:
            self.installed.add(preprocessing._NLTK_RESOURCES[name])
        return self.works


def install(monkeypatch, fake):
    monkeypatch.setattr(preprocessing, "_has_resource", fake.has_resource)
    monkeypatch.setattr(preprocessing.nltk, "download", fake.download)


# --- ensure_nltk_data -------------------------------------------------------


def test_missing_data_that_cannot_be_downloaded_raises_clear_error(monkeypatch):
    install(monkeypatch, FakeNltk(works=False))
    with pytest.raises(NLTKDataError) as info:
        ensure_nltk_data()
    message = str(info.value)
    for name in ("punkt_tab", "stopwords"):
        assert name in message
    assert "internet connection" in message
    assert "python -m nltk.downloader" in message


def test_download_that_raises_is_reported_as_nltk_data_error(monkeypatch):
    def broken_download(name, quiet=True):
        raise OSError("network is down")

    monkeypatch.setattr(preprocessing, "_has_resource", lambda path: False)
    monkeypatch.setattr(preprocessing.nltk, "download", broken_download)
    with pytest.raises(NLTKDataError):
        ensure_nltk_data()


def test_successful_download_passes(monkeypatch):
    fake = FakeNltk(works=True)
    install(monkeypatch, fake)
    ensure_nltk_data()
    assert sorted(fake.calls) == ["punkt", "punkt_tab", "stopwords"]


def test_installed_data_is_not_downloaded_again(monkeypatch):
    fake = FakeNltk(works=False)
    fake.installed = set(preprocessing._NLTK_RESOURCES.values())
    install(monkeypatch, fake)
    ensure_nltk_data()
    assert fake.calls == []


def test_failed_check_is_retried_not_cached(monkeypatch):
    fake = FakeNltk(works=False)
    install(monkeypatch, fake)
    with pytest.raises(NLTKDataError):
        ensure_nltk_data()
    fake.works = True  # the network is back
    ensure_nltk_data()
    assert len(fake.calls) == 6  # 3 failed downloads, then 3 retried


def test_summarize_text_raises_nltk_error_when_data_missing(monkeypatch):
    install(monkeypatch, FakeNltk(works=False))
    with pytest.raises(NLTKDataError):
        summarize_text(GOOD_TEXT)


# --- pipeline ---------------------------------------------------------------


def make_article(article_id, text):
    return SimpleNamespace(id=article_id, title=None, source="test", text=text)


class FakeSummarizer:
    def __init__(self, failures):
        self.failures = failures

    def summarize(self, text, num_sentences=3):
        if text in self.failures:
            raise self.failures[text]
        return "summary of " + text


def three_articles():
    return [make_article(1, "a"), make_article(2, "b"), make_article(3, "c")]


def test_unexpected_error_on_one_article_does_not_stop_the_batch():
    summarizer = FakeSummarizer({"b": RuntimeError("boom")})
    results = list(_summarize_stream(three_articles(), summarizer, 3))
    assert [r.ok for r in results] == [True, False, True]
    assert results[1].error == "Unexpected RuntimeError: boom"
    assert results[2].summary == "summary of c"


def test_invalid_input_error_message_is_unchanged():
    summarizer = FakeSummarizer({"b": InvalidInputError("too short")})
    results = list(_summarize_stream(three_articles(), summarizer, 3))
    assert [r.ok for r in results] == [True, False, True]
    assert results[1].error == "too short"


def test_nltk_data_error_stops_the_run():
    summarizer = FakeSummarizer({"b": NLTKDataError("no data")})
    stream = _summarize_stream(three_articles(), summarizer, 3)
    assert next(stream).ok
    with pytest.raises(NLTKDataError):
        next(stream)


def test_iter_summaries_survives_an_unexpected_error(tmp_path, monkeypatch):
    path = tmp_path / "articles.json"
    path.write_text(
        json.dumps([GOOD_TEXT + "first", GOOD_TEXT + "BOOM", GOOD_TEXT + "third"]),
        encoding="utf-8",
    )

    def flaky(self, text, num_sentences=3):
        if "BOOM" in text:
            raise ValueError("bad thing")
        return "ok"

    monkeypatch.setattr(TextSummarizer, "summarize", flaky)
    results = list(iter_summaries(path))
    assert [r.ok for r in results] == [True, False, True]
    assert "bad thing" in results[1].error


# --- CLI --------------------------------------------------------------------


def test_cli_reports_missing_nltk_data_and_exits(monkeypatch):
    def failing(path, num_sentences=3, method="frequency"):
        raise NLTKDataError("data missing")
        yield  # makes this a generator, like a reader that fails mid-run

    monkeypatch.setattr(main_module, "_use_utf8_output", lambda: None)
    monkeypatch.setattr(main_module, "iter_summaries", failing)
    monkeypatch.setattr(sys, "argv", ["main.py", "data.txt"])
    with pytest.raises(SystemExit) as info:
        main_module.main()
    assert str(info.value.code) == "Error: data missing"


def test_cli_prints_good_summaries_and_exits_1_when_one_article_failed(
    monkeypatch, capsys
):
    results = [
        SummaryResult(article_id=1, title=None, source="s", summary="fine summary"),
        SummaryResult(
            article_id=2, title=None, source="s", error="Unexpected RuntimeError: boom"
        ),
    ]

    def fake(path, num_sentences=3, method="frequency"):
        return iter(results)

    monkeypatch.setattr(main_module, "_use_utf8_output", lambda: None)
    monkeypatch.setattr(main_module, "iter_summaries", fake)
    monkeypatch.setattr(sys, "argv", ["main.py", "data.txt"])
    with pytest.raises(SystemExit) as info:
        main_module.main()
    assert info.value.code == 1
    captured = capsys.readouterr()
    assert "fine summary" in captured.out
    assert "Unexpected RuntimeError: boom" in captured.err


# --- API --------------------------------------------------------------------


def test_api_returns_503_when_nltk_data_is_missing(monkeypatch):
    def fail(text, num_sentences=3, method="frequency"):
        raise NLTKDataError("secret path details")

    monkeypatch.setattr(app_module, "summarize_text", fail)
    client = app_module.create_app().test_client()
    response = client.post("/summarize", json={"text": GOOD_TEXT})
    assert response.status_code == 503
    assert "temporarily unavailable" in response.get_json()["error"]
    assert "secret" not in response.get_data(as_text=True)


def test_api_503_then_recovers_when_download_works(monkeypatch):
    fake = FakeNltk(works=False)
    install(monkeypatch, fake)
    client = app_module.create_app().test_client()
    first = client.post("/summarize", json={"text": GOOD_TEXT})
    assert first.status_code == 503
    fake.works = True  # the network is back
    second = client.post("/summarize", json={"text": GOOD_TEXT})
    assert second.status_code == 200
    assert second.get_json()["summary"]
