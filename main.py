"""Usage: python main.py <file-or-folder> [num_sentences] [method]

method is "frequency" (default) or "textrank".
Supported inputs: .txt, .md, .csv, .json files, or a folder containing them.
"""
import sys

from summarizer.data_loader import DataLoadError
from summarizer.pipeline import iter_summaries
from summarizer.preprocessing import NLTKDataError
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


def _print_summary(result, show_header: bool) -> None:
    """Print one successful result's summary (with an optional header)."""
    if show_header:
        print(f"=== {result.title or result.article_id} ({result.source}) ===")
    print(result.summary)
    if show_header:
        print()
    sys.stdout.flush()


def _print_skipped(skipped) -> None:
    """Print all skipped articles together, grouped at the end, so a user
    scanning for failures does not have to read the whole batch output."""
    if not skipped:
        return
    print("Skipped:", file=sys.stderr, flush=True)
    for result in skipped:
        print(
            f"  {result.source} #{result.article_id}: {result.error}",
            file=sys.stderr,
            flush=True,
        )


def _print_results(results) -> int:
    """Print each summary as soon as it is ready; print all skipped articles
    together at the end. Returns how many were skipped.

    Headers on summaries are shown only when there is more than one article
    overall, so one result is held back until the next one arrives. If the
    reader fails part-way (for example on a bad row), the held-back result is
    still handled first.
    """
    skipped = []
    pending = None
    several = False

    def handle(result, show_header: bool) -> None:
        if not result.ok:
            skipped.append(result)
        else:
            _print_summary(result, show_header)

    try:
        for result in results:
            if pending is not None:
                several = True
                handle(pending, several)
            pending = result
    finally:
        if pending is not None:
            handle(pending, several)
        _print_skipped(skipped)
    return len(skipped)


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
    except (FileNotFoundError, DataLoadError, NLTKDataError) as error:
        sys.exit(f"Error: {error}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
