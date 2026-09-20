import pytest

from summarizer import TextSummarizer
from summarizer.preprocessing import clean_text, split_sentences, tokenize
from tests.sample_articles import ARTICLES, SHORT_ARTICLE


def test_clean_text_strips_urls_and_whitespace():
    assert clean_text("Hello   world\n https://x.com/a end") == "Hello world end"


def test_split_sentences():
    assert len(split_sentences(SHORT_ARTICLE)) == 2


def test_tokenize_removes_stopwords_and_punctuation():
    assert tokenize("The council met on Friday!") == ["council", "met", "friday"]


@pytest.mark.parametrize("name", ARTICLES)
def test_summary_is_shorter_and_uses_source_sentences(name):
    text = ARTICLES[name]
    summary = TextSummarizer().summarize(text, num_sentences=3)
    assert 0 < len(summary) < len(clean_text(text))
    for sentence in split_sentences(summary):
        assert sentence in clean_text(text)


def test_short_text_returned_unchanged():
    assert TextSummarizer().summarize(SHORT_ARTICLE, num_sentences=3) == SHORT_ARTICLE


def test_invalid_method_raises():
    with pytest.raises(ValueError):
        TextSummarizer(method="magic")
