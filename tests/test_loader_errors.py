"""Read errors must surface as DataLoadError, not raw tracebacks."""
import csv
from pathlib import Path

import pytest

from summarizer.data_loader import DataLoadError, load_articles


def test_permission_error_becomes_data_load_error(tmp_path, monkeypatch):
    article = tmp_path / "locked.txt"
    article.write_text("Some text.", encoding="utf-8")

    def deny(self, *args, **kwargs):
        raise PermissionError("access denied")

    monkeypatch.setattr(Path, "read_text", deny)

    with pytest.raises(DataLoadError) as info:
        load_articles(article)
    assert "locked.txt" in str(info.value)
    assert "could not be read" in str(info.value)


def test_csv_error_becomes_data_load_error(tmp_path, monkeypatch):
    article = tmp_path / "bad.csv"
    article.write_text("text\nhello\n", encoding="utf-8")

    def broken(*args, **kwargs):
        raise csv.Error("field larger than field limit")

    monkeypatch.setattr(csv, "DictReader", broken)

    with pytest.raises(DataLoadError) as info:
        load_articles(article)
    assert "bad.csv" in str(info.value)
    assert "could not be read" in str(info.value)


def test_invalid_utf8_still_reports_encoding_problem(tmp_path):
    article = tmp_path / "broken.txt"
    article.write_bytes(bytes([0xFF, 0xFF, 0xFF]) + b" not utf-8")

    with pytest.raises(DataLoadError) as info:
        load_articles(article)
    assert "not valid UTF-8" in str(info.value)
