"""Basic text preprocessing: cleaning, sentence splitting, tokenization."""
import re
from typing import List, Tuple

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

_NLTK_RESOURCES = {
    "punkt": "tokenizers/punkt",
    "punkt_tab": "tokenizers/punkt_tab",
    "stopwords": "corpora/stopwords",
}


def ensure_nltk_data() -> None:
    """Download required NLTK data the first time it's needed."""
    for name, path in _NLTK_RESOURCES.items():
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)


def clean_text(text: str) -> str:
    """Normalize whitespace and strip URLs."""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    ensure_nltk_data()
    return sent_tokenize(clean_text(text))


def tokenize(sentence: str, language: str = "english") -> List[str]:
    """Lowercase, tokenize, and drop stopwords and non-alphabetic tokens."""
    ensure_nltk_data()
    stops = set(stopwords.words(language))
    return [
        w for w in word_tokenize(sentence.lower())
        if w.isalpha() and w not in stops
    ]


def preprocess(text: str) -> List[Tuple[str, List[str]]]:
    """Return a list of (original_sentence, tokens) pairs."""
    return [(s, tokenize(s)) for s in split_sentences(text)]


# TODO (Day 4): add lemmatization with spaCy, e.g.
#   nlp = spacy.load("en_core_web_sm")
#   lemmas = [t.lemma_ for t in nlp(sentence) if not t.is_stop and t.is_alpha]
