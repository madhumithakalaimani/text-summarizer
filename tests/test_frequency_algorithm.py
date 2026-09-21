"""Direct tests for the frequency scoring algorithm."""
import pytest

from summarizer.summarizer import TextSummarizer

score = TextSummarizer._frequency_scores


def test_one_score_per_sentence():
    parsed = [("A.", ["cat"]), ("B.", ["dog"]), ("C.", ["cat", "dog"])]
    assert len(score(parsed)) == 3


def test_empty_vocabulary_gives_all_zero_scores():
    parsed = [("A.", []), ("B.", []), ("C.", [])]
    assert score(parsed) == [0.0, 0.0, 0.0]


def test_sentence_without_tokens_scores_zero():
    parsed = [("A.", ["cat", "cat"]), ("B.", [])]
    scores = score(parsed)
    assert scores[0] == pytest.approx(1.0)
    assert scores[1] == 0.0


def test_words_are_normalized_by_the_most_frequent_word():
    # cat appears 3 times (max), dog once -> dog weighs 1/3
    parsed = [("A.", ["cat", "dog"]), ("B.", ["cat"]), ("C.", ["cat"])]
    scores = score(parsed)
    assert scores[0] == pytest.approx((1 + 1 / 3) / 2)
    assert scores[1] == pytest.approx(1.0)
    assert scores[2] == pytest.approx(1.0)


def test_repeated_word_inside_one_sentence_counts_toward_frequency():
    # cat appears twice (max), dog once
    parsed = [("A.", ["cat", "cat"]), ("B.", ["dog"])]
    scores = score(parsed)
    assert scores[0] == pytest.approx(1.0)
    assert scores[1] == pytest.approx(0.5)


def test_long_sentence_does_not_win_just_by_being_long():
    long_rare = ["one", "two", "three", "four"]
    parsed = [("Long.", long_rare), ("Short.", ["common"]), ("Also.", ["common"])]
    scores = score(parsed)
    assert scores[0] == pytest.approx(0.5)
    assert scores[1] > scores[0]


def test_scores_stay_between_zero_and_one():
    parsed = [
        ("A.", ["cat", "dog", "bird"]),
        ("B.", ["cat", "cat", "fish"]),
        ("C.", []),
        ("D.", ["dog"]),
    ]
    assert all(0.0 <= s <= 1.0 for s in score(parsed))


def test_identical_sentences_get_equal_scores():
    parsed = [("A.", ["cat", "dog"]), ("B.", ["cat", "dog"]), ("C.", ["bird"])]
    scores = score(parsed)
    assert scores[0] == pytest.approx(scores[1])
