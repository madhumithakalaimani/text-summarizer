"""Input validation for the text summarizer."""

MIN_WORDS = 20
MAX_CHARS = 1_000_000
VALID_METHODS = ("frequency", "textrank")


class InvalidInputError(ValueError):
    """Raised when input to the summarizer is invalid."""


def validate_text(text, min_words=MIN_WORDS, max_chars=MAX_CHARS):
    """Return the stripped text, or raise InvalidInputError."""
    if not isinstance(text, str):
        raise InvalidInputError(
            f"Text must be a string, got {type(text).__name__}."
        )
    cleaned = text.strip()
    if not cleaned:
        raise InvalidInputError("Text is empty.")
    if len(cleaned) > max_chars:
        raise InvalidInputError(
            f"Text is too long ({len(cleaned)} characters; maximum is {max_chars})."
        )
    word_count = len(cleaned.split())
    if word_count < min_words:
        raise InvalidInputError(
            f"Text is too short ({word_count} words; minimum is {min_words})."
        )
    return cleaned


def validate_num_sentences(num_sentences):
    """Return num_sentences if it is an int >= 1, else raise InvalidInputError."""
    if isinstance(num_sentences, bool) or not isinstance(num_sentences, int):
        raise InvalidInputError(
            f"num_sentences must be an integer, got {type(num_sentences).__name__}."
        )
    if num_sentences < 1:
        raise InvalidInputError("num_sentences must be at least 1.")
    return num_sentences


def validate_method(method):
    """Return the method name in lowercase, or raise InvalidInputError."""
    if not isinstance(method, str):
        raise InvalidInputError(
            f"method must be a string, got {type(method).__name__}."
        )
    normalized = method.strip().lower()
    if normalized not in VALID_METHODS:
        raise InvalidInputError(
            f"Unknown method '{method}'. Choose from: {', '.join(VALID_METHODS)}."
        )
    return normalized
