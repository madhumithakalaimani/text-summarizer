"""Usage: python main.py article.txt [num_sentences]"""
import sys

from summarizer import TextSummarizer


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()
    print(TextSummarizer().summarize(text, num_sentences=n))


if __name__ == "__main__":
    main()
