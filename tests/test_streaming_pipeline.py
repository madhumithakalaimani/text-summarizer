"""Tests for streaming: articles and summaries are produced one at a time."""
import csv
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from summarizer.data_loader import (
    DataLoadError,
    iter_articles,
    iter_directory,
    iter_path,
    load_articles,
    load_directory,
)
from summarizer.pipeline import iter_summaries, summarize_path
from summarizer.validation import InvalidInputError
from tests.sample_articles import CITY_TRANSIT

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
METHODS = ["frequency", "textrank"]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "main.py"), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    return path


def bad_row_csv(tmp_path):
    """Two good rows followed by a row that has no text."""
    return write_csv(
        tmp_path / "bad_rows.csv",
        [["id", "text"], ["1", CITY_TRANSIT], ["2", CITY_TRANSIT], ["3"]],
    )


# ---- Loader ----------------------------------------------------------------

def test_iter_articles_returns_an_iterator_not_a_list():
    result = iter_articles(SAMPLES / "articles.csv")
    assert isinstance(result, Iterator)
    assert not isinstance(result, list)


def test_iter_articles_gives_the_same_articles_as_load_articles():
    for name in ("articles.csv", "articles.json", "article_long.txt"):
        path = SAMPLES / name
        assert list(iter_articles(path)) == load_articles(path)


def test_iter_directory_and_iter_path_match_load_directory():
    expected = load_directory(SAMPLES)
    assert len(expected) == 7
    assert list(iter_directory(SAMPLES)) == expected
    assert list(iter_path(SAMPLES)) == expected
    csv_path = SAMPLES / "articles.csv"
    assert list(iter_path(csv_path)) == load_articles(csv_path)


def test_csv_rows_are_read_one_at_a_time(tmp_path):
    articles = iter_articles(bad_row_csv(tmp_path))
    assert next(articles).id == "1"
    assert next(articles).id == "2"
    with pytest.raises(DataLoadError, match="no text field"):
        next(articles)


def test_bad_paths_raise_before_any_article_is_read(tmp_path):
    (tmp_path / "notes.pdf").write_text("x", encoding="utf-8")
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        iter_articles(tmp_path / "missing.txt")
    with pytest.raises(DataLoadError):
        iter_articles(tmp_path / "notes.pdf")
    with pytest.raises(DataLoadError):
        iter_articles(tmp_path)  # a folder is not a file
    with pytest.raises(FileNotFoundError):
        iter_directory(tmp_path / "missing_folder")
    with pytest.raises(DataLoadError):
        iter_directory(empty)


# ---- Pipeline --------------------------------------------------------------

def test_iter_summaries_yields_results_one_at_a_time(tmp_path):
    results = iter_summaries(bad_row_csv(tmp_path), num_sentences=1)
    assert isinstance(results, Iterator)
    first = next(results)
    assert first.ok and first.article_id == "1"
    assert next(results).article_id == "2"
    with pytest.raises(DataLoadError):
        next(results)


@pytest.mark.parametrize("method", METHODS)
def test_summarize_path_gives_the_same_results_as_iter_summaries(method):
    streamed = list(iter_summaries(SAMPLES, num_sentences=2, method=method))
    assert len(streamed) == 7
    assert summarize_path(SAMPLES, num_sentences=2, method=method) == streamed


def test_iter_summaries_reports_an_invalid_article_and_carries_on(tmp_path):
    path = write_csv(
        tmp_path / "mixed.csv",
        [
            ["id", "text"],
            ["1", CITY_TRANSIT],
            ["2", "Too short to summarize."],
            ["3", CITY_TRANSIT],
        ],
    )
    results = list(iter_summaries(path, num_sentences=1))
    assert [r.ok for r in results] == [True, False, True]
    assert results[1].error
    assert results[1].summary is None


def test_iter_summaries_rejects_bad_options_and_paths_immediately(tmp_path):
    path = SAMPLES / "articles.csv"
    with pytest.raises(InvalidInputError):
        iter_summaries(path, num_sentences=0)
    with pytest.raises(InvalidInputError):
        iter_summaries(path, method="bogus")
    with pytest.raises(FileNotFoundError):
        iter_summaries(tmp_path / "missing.csv")


# ---- Command line ----------------------------------------------------------

def test_cli_prints_finished_summaries_before_a_bad_row_error(tmp_path):
    result = run_cli(str(bad_row_csv(tmp_path)), "1")
    assert result.returncode == 1
    assert "=== 1 (bad_rows.csv) ===" in result.stdout
    assert "=== 2 (bad_rows.csv) ===" in result.stdout
    assert "no text field" in result.stderr


def test_cli_single_article_is_printed_without_a_header():
    result = run_cli(str(SAMPLES / "article_long.txt"), "2")
    assert result.returncode == 0
    assert "===" not in result.stdout
    assert result.stdout.strip() != ""
