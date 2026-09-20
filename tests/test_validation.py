import pytest

from summarizer.validation import (
    InvalidInputError,
    validate_method,
    validate_num_sentences,
    validate_text,
)

GOOD_TEXT = "word " * 25


def test_invalid_input_error_is_a_value_error():
    assert issubclass(InvalidInputError, ValueError)


def test_validate_text_strips_whitespace():
    assert validate_text("  " + GOOD_TEXT + "  ") == GOOD_TEXT.strip()


@pytest.mark.parametrize("bad", [None, 123, 4.5, ["text"], b"bytes"])
def test_validate_text_rejects_non_strings(bad):
    with pytest.raises(InvalidInputError, match="must be a string"):
        validate_text(bad)


@pytest.mark.parametrize("empty", ["", "   ", "\n\t "])
def test_validate_text_rejects_empty(empty):
    with pytest.raises(InvalidInputError, match="empty"):
        validate_text(empty)


def test_validate_text_rejects_too_short():
    with pytest.raises(InvalidInputError, match="too short"):
        validate_text("only a few words here")


def test_validate_text_accepts_exact_minimum():
    text = " ".join(["word"] * 20)
    assert validate_text(text) == text


def test_validate_text_rejects_too_long():
    with pytest.raises(InvalidInputError, match="too long"):
        validate_text("word " * 30, max_chars=50)


@pytest.mark.parametrize("value", [1, 3, 10])
def test_validate_num_sentences_accepts_positive_ints(value):
    assert validate_num_sentences(value) == value


@pytest.mark.parametrize("value", [0, -1])
def test_validate_num_sentences_rejects_less_than_one(value):
    with pytest.raises(InvalidInputError, match="at least 1"):
        validate_num_sentences(value)


@pytest.mark.parametrize("value", [True, False, "3", 2.0, None])
def test_validate_num_sentences_rejects_non_integers(value):
    with pytest.raises(InvalidInputError, match="must be an integer"):
        validate_num_sentences(value)


@pytest.mark.parametrize(
    "value, expected",
    [("frequency", "frequency"), ("TextRank", "textrank"), ("  FREQUENCY ", "frequency")],
)
def test_validate_method_normalizes(value, expected):
    assert validate_method(value) == expected


@pytest.mark.parametrize("bad", ["bert", "", "text rank"])
def test_validate_method_rejects_unknown(bad):
    with pytest.raises(InvalidInputError, match="Unknown method"):
        validate_method(bad)


@pytest.mark.parametrize("bad", [None, 5])
def test_validate_method_rejects_non_strings(bad):
    with pytest.raises(InvalidInputError, match="must be a string"):
        validate_method(bad)
