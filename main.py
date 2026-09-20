"""Usage: python main.py <file-or-folder> [num_sentences] [method]

method is "frequency" (default) or "textrank".
Supported inputs: .txt, .md, .csv, .json files, or a folder containing them.
"""
import sys

from summarizer.data_loader import DataLoadError
from summarizer.pipeline import summarize_path
from summarizer.validation import (
    InvalidInputError,
    validate_method,
    validate_num_sentences,
)


def _use_utf8_output() -> None:
    """Write output as UTF-8 so redirected output cannot crash on Windows."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main() -> None:
    _use_utf8_output()
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    n = 3
    if len(sys.argv) > 2:
        try:
            n = validate_num_sentences(int(sys.argv[2]))
        except ValueError:
            sys.exit(
                "Error: num_sentences must be a whole number of at least 1 "
                f"(got {sys.argv[2]!r})."
            )

    method = "frequency"
    if len(sys.argv) > 3:
        try:
            method = validate_method(sys.argv[3])
        except InvalidInputError as error:
            sys.exit(f"Error: {error}")

    try:
        results = summarize_path(sys.argv[1], num_sentences=n, method=method)
    except (FileNotFoundError, DataLoadError) as error:
        sys.exit(f"Error: {error}")

    multiple = len(results) > 1
    failed = 0
    for result in results:
        if not result.ok:
            failed += 1
            print(
                f"Skipped {result.source} #{result.article_id}: {result.error}",
                file=sys.stderr,
            )
            continue
        if multiple:
            print(f"=== {result.title or result.article_id} ({result.source}) ===")
        print(result.summary)
        if multiple:
            print()
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
