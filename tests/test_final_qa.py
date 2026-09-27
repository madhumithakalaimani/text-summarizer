"""Final QA pass: cover previously-untested edge cases and defensive branches."""
import logging

import pytest

from summarizer.preprocessing import _has_resource
from summarizer.summarizer import TextSummarizer


def test_index_route_returns_200():
    from app import create_app

    client = create_app().test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_setup_logging_is_idempotent(tmp_path, monkeypatch):
    import summarizer.logging_config as lc

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(lc, "_configured", False)
    root = logging.getLogger()
    lc.setup_logging()
    handlers_after_first = list(root.handlers)
    lc.setup_logging()
    assert root.handlers == handlers_after_first
    for h in handlers_after_first[-2:]:
        root.removeHandler(h)


def test_has_resource_returns_false_when_missing(monkeypatch):
    import nltk

    def boom(path):
        raise LookupError("not found")

    monkeypatch.setattr(nltk.data, "find", boom)
    assert _has_resource("tokenizers/punkt") is False


def test_textrank_handles_empty_vocabulary(monkeypatch):
    import summarizer.summarizer as summarizer_module

    def boom(self, token_lists):
        raise ValueError("empty vocabulary")

    monkeypatch.setattr(
        summarizer_module.TfidfVectorizer, "fit_transform", boom
    )
    parsed = [("Cats meow.", ["cats", "meow"]), ("Dogs bark.", ["dogs", "bark"])]
    scores = TextSummarizer._textrank_scores(parsed)
    assert scores == [0.0, 0.0]
