"""Usage: python main.py <file-or-folder> [num_sentences] [method]

method is "frequency" (default) or "textrank".
Supported inputs: .txt, .md, .csv, .json files, or a folder containing them.
"""
import sys
from pathlib import Path

from summarizer import TextSummarizer
from summarizer.data_loader import DataLoadError, load_articles, load_directory
from summarizer.validation import (
    InvalidInputError,
    validate_method,
    validate_num_sentences,
)


def main() -> None:
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

    path = Path(sys.argv[1])
    try:
        articles = load_directory(path) if path.is_dir() else load_articles(path)
    except (FileNotFoundError, DataLoadError) as error:
        sys.exit(f"Error: {error}")

    summarizer = TextSummarizer(method=method)
    multiple = len(articles) > 1
    failed = 0
    for article in articles:
        try:
            summary = summarizer.summarize(article.text, num_sentences=n)
        except InvalidInputError as error:
            failed += 1
            print(f"Skipped {article.source} #{article.id}: {error}", file=sys.stderr)
            continue
        if multiple:
            print(f"=== {article.title or article.id} ({article.source}) ===")
        print(summary)
        if multiple:
            print()
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
