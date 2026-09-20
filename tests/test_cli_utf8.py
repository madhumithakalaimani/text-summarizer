"""The CLI must not crash on non-cp1252 characters when output is captured."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUPEE = "\u20b9"


def _run_cli(*args):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("PYTHONUTF8", "PYTHONIOENCODING")
    }
    return subprocess.run(
        [sys.executable, str(ROOT / "main.py"), *args],
        capture_output=True,
        cwd=str(ROOT),
        env=env,
    )


def test_cli_prints_non_ascii_summary_when_output_is_captured(tmp_path):
    sentence = "The price rose to " + RUPEE + "500 last week and analysts say demand is steady. "
    article = tmp_path / "rupee.txt"
    article.write_text(sentence * 3, encoding="utf-8")

    result = _run_cli(str(article), "1")

    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert RUPEE in result.stdout.decode("utf-8")


def test_cli_prints_non_ascii_summary_with_textrank(tmp_path):
    sentence = "The price rose to " + RUPEE + "500 last week and analysts say demand is steady. "
    article = tmp_path / "rupee.txt"
    article.write_text(sentence * 3, encoding="utf-8")

    result = _run_cli(str(article), "1", "textrank")

    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert RUPEE in result.stdout.decode("utf-8")
