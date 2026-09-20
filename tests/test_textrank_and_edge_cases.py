"""Tests for TextRank, edge cases, headline splitting, and the CLI method option."""
import subprocess
import sys
from pathlib import Path

import pytest

from summarizer import TextSummarizer
from summarizer.preprocessing import preprocess, split_sentences
from tests.sample_articles import ARTICLES, CITY_TRANSIT

ROOT = Path(__file__).resolve().parent.parent
METHODS = ["frequency", "textrank"]

ONLY_STOPWORDS = (
    "The and of to in. Is it that for on. With as at by this. "
    "It is the and of. To in is it that. For on with as at."
)
IDENTICAL_SENTENCES = "Bike lanes make the city safer for everyone. " * 5
NO_SHARED_WORDS = (
    "Apples grow slowly. Rivers flow quickly. Mountains stand tall. "
    "Engines roar loudly. Poets write daily. Children laugh often. "
    "Farmers plant seeds. Doctors work nights. Pilots fly high. "
    "Bakers knead dough."
)
ONE_LONG_SENTENCE = (
    "The committee met on Monday afternoon to discuss the proposal, "
    "review the budget, hear from local residents, and consider the "
    "objections raised by several neighbouring councils before voting."
)
ODD_WHITESPACE = (
    "The city\tcouncil approved a plan on Tuesday.\n\n\nSupporters   argue "
    "that safer lanes will help.   Some shop owners worry about parking.\r\n"
    "Others expect more foot traffic from cyclists and visitors. "
    "Cost estimates remain uncertain for now."
)
HEADLINE_TEXT = (
    "City Council Approves Bike Plan\n"
    "The city council approved a plan on Tuesday to build new bike lanes. "
    "Supporters argue that safer lanes will encourage more people to cycle. "
    "Some shop owners worry about lost parking and sales."
)
WRAPPED_TEXT = (
    "The city council approved a plan on Tuesday to build\n"
    "new bike lanes across the whole city. Supporters argue that safer lanes\n"
    "will encourage more people to cycle."
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "main.py"), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )


# ---- TextRank behaviour ----------------------------------------------------

@pytest.mark.parametrize("name", ARTICLES)
def test_textrank_summary_is_shorter_and_uses_source_sentences(name):
    text = ARTICLES[name]
    summary = TextSummarizer(method="textrank").summarize(text, num_sentences=3)
    source_sentences = split_sentences(text)
    assert 0 < len(summary) < len(" ".join(source_sentences))
    for sentence in split_sentences(summary):
        assert sentence in source_sentences


@pytest.mark.parametrize("n", [1, 2, 3])
def test_textrank_returns_requested_number_of_sentences(n):
    summary = TextSummarizer(method="textrank").summarize(CITY_TRANSIT, num_sentences=n)
    assert len(split_sentences(summary)) == n


def test_textrank_keeps_original_sentence_order():
    source = split_sentences(CITY_TRANSIT)
    summary = TextSummarizer(method="textrank").summarize(CITY_TRANSIT, num_sentences=3)
    positions = [source.index(s) for s in split_sentences(summary)]
    assert positions == sorted(positions)


def test_textrank_is_deterministic():
    summarizer = TextSummarizer(method="textrank")
    first = summarizer.summarize(CITY_TRANSIT, num_sentences=3)
    second = summarizer.summarize(CITY_TRANSIT, num_sentences=3)
    assert first == second


def test_textrank_scores_one_per_sentence_and_sum_to_one():
    parsed = preprocess(CITY_TRANSIT)
    scores = TextSummarizer._textrank_scores(parsed)
    assert len(scores) == len(parsed)
    assert all(score >= 0 for score in scores)
    assert sum(scores) == pytest.approx(1.0)


def test_textrank_scores_are_zero_when_only_stopwords():
    parsed = preprocess("The and of. Is it that. For on with.")
    assert TextSummarizer._textrank_scores(parsed) == [0.0] * len(parsed)


def test_textrank_scores_are_zero_when_no_words_are_shared():
    parsed = preprocess("Apples grow slowly. Rivers flow quickly. Mountains stand tall.")
    assert TextSummarizer._textrank_scores(parsed) == [0.0] * len(parsed)


# ---- Edge cases (both methods) ---------------------------------------------

@pytest.mark.parametrize("method", METHODS)
def test_only_stopwords_returns_first_sentences(method):
    summary = TextSummarizer(method=method).summarize(ONLY_STOPWORDS, num_sentences=2)
    assert summary == "The and of to in. Is it that for on."


@pytest.mark.parametrize("method", METHODS)
def test_no_shared_words_returns_first_sentences(method):
    summary = TextSummarizer(method=method).summarize(NO_SHARED_WORDS, num_sentences=2)
    assert summary == "Apples grow slowly. Rivers flow quickly."


@pytest.mark.parametrize("method", METHODS)
def test_identical_sentences_do_not_crash(method):
    summary = TextSummarizer(method=method).summarize(IDENTICAL_SENTENCES, num_sentences=2)
    sentence = "Bike lanes make the city safer for everyone."
    assert summary == sentence + " " + sentence


@pytest.mark.parametrize("method", METHODS)
def test_single_long_sentence_is_returned_unchanged(method):
    summary = TextSummarizer(method=method).summarize(ONE_LONG_SENTENCE, num_sentences=3)
    assert summary == ONE_LONG_SENTENCE


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("name", ARTICLES)
def test_num_sentences_larger_than_count_returns_everything(method, name):
    text = ARTICLES[name]
    summary = TextSummarizer(method=method).summarize(text, num_sentences=1000)
    assert summary == " ".join(split_sentences(text))


@pytest.mark.parametrize("method", METHODS)
def test_unusual_whitespace_is_normalized(method):
    summary = TextSummarizer(method=method).summarize(ODD_WHITESPACE, num_sentences=2)
    for bad in ("\t", "\n", "\r", "  "):
        assert bad not in summary
    assert len(split_sentences(summary)) == 2


# ---- Headline splitting ----------------------------------------------------

def test_headline_becomes_its_own_sentence():
    sentences = split_sentences(HEADLINE_TEXT)
    assert len(sentences) == 4
    assert sentences[0] == "City Council Approves Bike Plan"
    assert sentences[1].startswith("The city council approved")


def test_hard_wrapped_lines_are_not_split_into_headlines():
    sentences = split_sentences(WRAPPED_TEXT)
    assert len(sentences) == 2
    assert sentences[0].endswith("across the whole city.")


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("n", [1, 2])
def test_headline_is_excluded_from_summary(method, n):
    summary = TextSummarizer(method=method).summarize(HEADLINE_TEXT, num_sentences=n)
    assert "City Council Approves Bike Plan" not in summary
    real = split_sentences(HEADLINE_TEXT, include_headings=False)
    result = split_sentences(summary)
    assert len(result) == n
    for sentence in result:
        assert sentence in real


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("n", [3, 5])
def test_short_headline_text_is_returned_without_headline(method, n):
    summary = TextSummarizer(method=method).summarize(HEADLINE_TEXT, num_sentences=n)
    assert "City Council Approves Bike Plan" not in summary
    assert summary.startswith("The city council approved a plan on Tuesday")
    assert "Some shop owners worry about lost parking and sales." in summary
    assert len(split_sentences(summary)) == 3


def test_split_sentences_can_omit_headings():
    sentences = split_sentences(HEADLINE_TEXT, include_headings=False)
    assert len(sentences) == 3
    assert "City Council Approves Bike Plan" not in sentences
    assert sentences[0].startswith("The city council approved")


# ---- CLI method option -----------------------------------------------------

def test_cli_textrank_method_runs():
    result = run_cli(str(ROOT / "data" / "samples" / "article_long.txt"), "3", "textrank")
    assert result.returncode == 0
    assert result.stdout.strip() != ""


def test_cli_unknown_method_exits_with_error():
    result = run_cli(str(ROOT / "data" / "samples" / "article_long.txt"), "3", "bogus")
    assert result.returncode == 1
    assert "Unknown method" in result.stderr


@pytest.mark.parametrize("method", METHODS)
def test_cli_omits_headline_from_summary(tmp_path, method):
    article = tmp_path / "headline_article.txt"
    article.write_text(HEADLINE_TEXT, encoding="utf-8")
    result = run_cli(str(article), "2", method)
    assert result.returncode == 0
    assert result.stdout.strip() != ""
    assert "City Council Approves Bike Plan" not in result.stdout
