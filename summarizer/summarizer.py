"""Extractive text summarizer (baseline + TextRank stub)."""
from collections import Counter
from typing import List

from .preprocessing import preprocess
from .validation import validate_method, validate_num_sentences, validate_text


class TextSummarizer:
    def __init__(self, method: str = "frequency"):
        self.method = validate_method(method)

    def summarize(self, text: str, num_sentences: int = 3) -> str:
        """Return the top `num_sentences` sentences, in original order."""
        text = validate_text(text)
        num_sentences = validate_num_sentences(num_sentences)

        parsed = preprocess(text)
        if len(parsed) <= num_sentences:
            return " ".join(s for s, _ in parsed)

        if self.method == "frequency":
            scores = self._frequency_scores(parsed)
        else:
            scores = self._textrank_scores(parsed)

        top = sorted(range(len(parsed)), key=lambda i: scores[i], reverse=True)
        keep = sorted(top[:num_sentences])
        return " ".join(parsed[i][0] for i in keep)

    @staticmethod
    def _frequency_scores(parsed) -> List[float]:
        """Score each sentence by the normalized frequency of its words."""
        freq = Counter(w for _, tokens in parsed for w in tokens)
        if not freq:
            return [0.0] * len(parsed)
        max_freq = max(freq.values())
        scores = []
        for _, tokens in parsed:
            if not tokens:
                scores.append(0.0)
                continue
            # Average (not sum) so long sentences don't automatically win
            scores.append(sum(freq[w] / max_freq for w in tokens) / len(tokens))
        return scores

    @staticmethod
    def _textrank_scores(parsed) -> List[float]:
        # TODO (Day 4): TF-IDF vectors -> cosine similarity matrix
        #               -> networkx.from_numpy_array -> nx.pagerank
        raise NotImplementedError("TextRank is planned for Day 4.")
