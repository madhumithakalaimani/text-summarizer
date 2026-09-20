"""Tests for the TextRank settings, its fallback and how ties are broken."""
import networkx as nx
import pytest

from summarizer import TextSummarizer
from summarizer.preprocessing import preprocess
from summarizer.summarizer import (
    TEXTRANK_DAMPING,
    TEXTRANK_MAX_ITER,
    TEXTRANK_TOLERANCE,
)
from tests.sample_articles import CITY_TRANSIT

METHODS = ["frequency", "textrank"]

SIX_SENTENCES = (
    "The council met on Monday. Residents spoke about the plan. "
    "Engineers described the new design. Shop owners raised concerns about parking. "
    "Cyclists supported the bike lanes. The vote is set for June."
)
CLUSTER_PLUS_OUTSIDER = (
    "Bike lanes make the city safer for every cyclist. "
    "City bike lanes reduce crashes for cyclists. "
    "Safer bike lanes encourage more cyclists in the city. "
    "Cyclists say city bike lanes feel safer. "
    "Volcanoes erupt violently near distant oceans."
)


def test_textrank_settings_are_the_standard_values():
    assert TEXTRANK_DAMPING == 0.85
    assert TEXTRANK_MAX_ITER >= 100
    assert 0 < TEXTRANK_TOLERANCE <= 1e-6


def test_textrank_passes_its_settings_to_pagerank(monkeypatch):
    captured = {}

    def fake_pagerank(graph, **kwargs):
        captured.update(kwargs)
        return {node: 1.0 / graph.number_of_nodes() for node in graph}

    monkeypatch.setattr(nx, "pagerank", fake_pagerank)
    TextSummarizer._textrank_scores(preprocess(CITY_TRANSIT))
    assert captured["alpha"] == TEXTRANK_DAMPING
    assert captured["max_iter"] == TEXTRANK_MAX_ITER
    assert captured["tol"] == TEXTRANK_TOLERANCE
    assert captured["weight"] == "weight"


def test_textrank_scores_are_zero_when_pagerank_does_not_converge(monkeypatch):
    def failing_pagerank(graph, **kwargs):
        raise nx.PowerIterationFailedConvergence(TEXTRANK_MAX_ITER)

    monkeypatch.setattr(nx, "pagerank", failing_pagerank)
    parsed = preprocess(CITY_TRANSIT)
    assert TextSummarizer._textrank_scores(parsed) == [0.0] * len(parsed)


def test_unrelated_sentence_gets_the_lowest_score():
    parsed = preprocess(CLUSTER_PLUS_OUTSIDER)
    assert len(parsed) == 5
    scores = TextSummarizer._textrank_scores(parsed)
    assert scores.index(min(scores)) == 4
    assert scores[4] < min(scores[:4])


def test_identical_sentences_get_equal_scores():
    parsed = preprocess("Bike lanes make the city safer for everyone. " * 5)
    scores = TextSummarizer._textrank_scores(parsed)
    assert scores == pytest.approx([0.2] * 5)


def _patch_scores(monkeypatch, method, scores_for):
    name = "_frequency_scores" if method == "frequency" else "_textrank_scores"
    monkeypatch.setattr(TextSummarizer, name, staticmethod(scores_for))


@pytest.mark.parametrize("method", METHODS)
def test_all_tied_scores_keep_the_earliest_sentences(monkeypatch, method):
    _patch_scores(monkeypatch, method, lambda parsed: [1.0] * len(parsed))
    summary = TextSummarizer(method=method).summarize(SIX_SENTENCES, num_sentences=2)
    assert summary == "The council met on Monday. Residents spoke about the plan."


@pytest.mark.parametrize("method", METHODS)
def test_partial_tie_keeps_the_earlier_of_the_tied_sentences(monkeypatch, method):
    _patch_scores(
        monkeypatch, method, lambda parsed: [0.0, 5.0, 5.0, 5.0, 0.0, 0.0]
    )
    summary = TextSummarizer(method=method).summarize(SIX_SENTENCES, num_sentences=2)
    assert summary == (
        "Residents spoke about the plan. Engineers described the new design."
    )
