"""Tests for hyphenated words and URL removal (Day 7 review fixes)."""
from summarizer.preprocessing import clean_text, split_sentences, tokenize


def test_tokenize_keeps_hyphenated_words():
    tokens = tokenize("A well-known example is not broken.")
    assert "well-known" in tokens
    assert "example" in tokens


def test_tokenize_still_drops_numbers_and_dashes():
    tokens = tokenize("Prices rose 5 percent -- sharply, in 2024, on 5G networks.")
    assert "--" not in tokens
    assert "5" not in tokens
    assert "2024" not in tokens
    assert all(t.replace("-", "").isalpha() for t in tokens)


def test_clean_text_keeps_period_after_url():
    text = "See https://example.com/a. Next sentence follows here."
    assert clean_text(text) == "See. Next sentence follows here."


def test_clean_text_removes_url_in_the_middle_of_a_sentence():
    text = "Read https://example.com/page for the full details."
    assert clean_text(text) == "Read for the full details."


def test_clean_text_removes_url_at_the_end():
    assert clean_text("More at https://example.com/x") == "More at"


def test_url_followed_by_period_keeps_sentence_boundary():
    text = "See https://example.com/a. Next sentence follows here."
    sentences = split_sentences(text)
    assert len(sentences) == 2
    assert sentences[1] == "Next sentence follows here."
