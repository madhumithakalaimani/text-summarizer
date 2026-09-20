"""Usage: python main.py <file-or-folder> [num_sentences] [method]

method is "frequency" (default) or "textrank".
Supported inputs: .txt, .md, .csv, .json files, or a folder containing them.
"""
import sys

from summarizer.data_loader import DataLoadError
from summarizer.pipeline import iter_summaries
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


def _print_result(result, show_header: bool) -> int:
    """Print one result. Returns 1 if the article was skipped, else 0."""
    if not result.ok:
        print(
            f"Skipped {result.source} #{result.article_id}: {result.error}",
            file=sys.stderr,
            flush=True,
        )
        return 1
    if show_header:
        print(f"=== {result.title or result.article_id} ({result.source}) ===")
    print(result.summary)
    if show_header:
        print()
    sys.stdout.flush()
    return 0


def _print_results(results) -> int:
    """Print each result as soon as it is ready. Returns how many were skipped.

    Headers are shown only when there is more than one article, so one result
    is held back until the next one arrives. If the reader fails part-way
    (for example on a bad row), the held-back result is still printed first.
    """
    failed = 0
    pending = None
    several = False
    try:
        for result in results:
            if pending is not None:
                several = True
                failed += _print_result(pending, several)
            pending = result
    finally:
        # Runs on a reader error too, so no finished summary is lost
        if pending is not None:
            failed += _print_result(pending, several)
    return failed


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
        failed = _print_results(
            iter_summaries(sys.argv[1], num_sentences=n, method=method)
        )
    except (FileNotFoundError, DataLoadError) as error:
        sys.exit(f"Error: {error}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
