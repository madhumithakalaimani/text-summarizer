"""End-to-end tests: real files -> pipeline -> summary, and the CLI."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from summarizer.pipeline import SummaryResult, summarize_path, summarize_text
from summarizer.preprocessing import split_sentences
from summarizer.validation import InvalidInputError

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"
LONG_ARTICLE = SAMPLES / "article_long.txt"
METHODS = ["frequency", "textrank"]


def run_main(*args):
    """Run main.py as a real subprocess from the repo root."""
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


@pytest.mark.parametrize("method", METHODS)
def test_single_file_end_to_end(method):
    results = summarize_path(LONG_ARTICLE, num_sentences=3, method=method)
    assert len(results) == 1
    result = results[0]
    assert isinstance(result, SummaryResult)
    assert result.ok and result.error is None

    text = LONG_ARTICLE.read_text(encoding="utf-8")
    assert result.summary
    assert len(result.summary) < len(text)
    kept = split_sentences(result.summary, include_headings=False)
    assert 1 <= len(kept) <= 3


@pytest.mark.parametrize("method", METHODS)
def test_summary_keeps_original_sentence_order(method):
    text = LONG_ARTICLE.read_text(encoding="utf-8")
    original = split_sentences(text, include_headings=False)
    summary = summarize_text(text, num_sentences=3, method=method)
    kept = split_sentences(summary, include_headings=False)
    positions = [original.index(s) for s in kept]
    assert positions == sorted(positions)


@pytest.mark.parametrize("method", METHODS)
def test_whole_sample_folder(method):
    results = summarize_path(SAMPLES, num_sentences=2, method=method)
    assert len(results) == 7
    assert all(r.ok for r in results)
    assert all(r.summary for r in results)


def test_bad_article_is_skipped_and_the_rest_still_run(tmp_path):
    valid = LONG_ARTICLE.read_text(encoding="utf-8")
    mixed = tmp_path / "mixed.json"
    mixed.write_text(json.dumps(["too short", valid]), encoding="utf-8")

    results = summarize_path(mixed, num_sentences=2)
    assert len(results) == 2
    assert not results[0].ok
    assert results[0].error
    assert results[0].summary is None
    assert results[1].ok
    assert results[1].summary


def test_bad_options_raise_invalid_input_error():
    with pytest.raises(InvalidInputError):
        summarize_path(LONG_ARTICLE, num_sentences=0)
    with pytest.raises(InvalidInputError):
        summarize_path(LONG_ARTICLE, method="bogus")
    with pytest.raises(InvalidInputError):
        summarize_text("too short")


def test_missing_file_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        summarize_path(SAMPLES / "does_not_exist.txt")


def test_cli_single_file_matches_pipeline():
    completed = run_main("data/samples/article_long.txt", "2", "textrank")
    assert completed.returncode == 0
    expected = summarize_path(LONG_ARTICLE, num_sentences=2, method="textrank")[0].summary
    assert completed.stdout.strip() == expected.strip()


def test_cli_folder_prints_a_header_per_article():
    completed = run_main("data/samples", "2")
    assert completed.returncode == 0
    assert completed.stdout.count("===") >= 7


def test_cli_folder_with_a_bad_article_exits_1_but_summarizes_the_rest(tmp_path):
    (tmp_path / "good.txt").write_text(
        LONG_ARTICLE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "bad.txt").write_text("too short", encoding="utf-8")

    completed = run_main(str(tmp_path), "2")
    assert completed.returncode == 1
    assert "Skipped" in completed.stderr
    assert completed.stdout.strip()
