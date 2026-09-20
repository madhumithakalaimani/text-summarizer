import json
from pathlib import Path

import pytest

from summarizer.data_loader import DataLoadError, load_articles, load_directory

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples"


def test_data_load_error_is_a_value_error():
    assert issubclass(DataLoadError, ValueError)


def test_load_txt_file(tmp_path):
    f = tmp_path / "story.txt"
    f.write_text("First sentence. Second sentence.", encoding="utf-8")
    [article] = load_articles(f)
    assert article.id == "story"
    assert article.title == "story"
    assert article.text == "First sentence. Second sentence."
    assert article.source == "story.txt"


def test_load_md_file(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("Some markdown text.", encoding="utf-8")
    [article] = load_articles(f)
    assert article.text == "Some markdown text."
    assert article.source == "notes.md"


def test_load_text_strips_bom_and_whitespace(tmp_path):
    f = tmp_path / "bom.txt"
    f.write_bytes(b"\xef\xbb\xbf  Hello there.  \n")
    [article] = load_articles(f)
    assert article.text == "Hello there."


def test_load_csv(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text(
        'id,title,text\n1,First,"Hello, world."\n2,Second,Another article.\n',
        encoding="utf-8",
    )
    articles = load_articles(f)
    assert len(articles) == 2
    assert articles[0].id == "1"
    assert articles[0].title == "First"
    assert articles[0].text == "Hello, world."
    assert articles[0].source == "data.csv"
    assert articles[1].text == "Another article."


def test_csv_field_names_are_case_insensitive(tmp_path):
    f = tmp_path / "caps.csv"
    f.write_text("ID,Headline,Content\n7,Big News,Body of the story.\n", encoding="utf-8")
    [article] = load_articles(f)
    assert article.id == "7"
    assert article.title == "Big News"
    assert article.text == "Body of the story."


def test_csv_missing_text_field_raises(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("id,title\n1,No text here\n", encoding="utf-8")
    with pytest.raises(DataLoadError, match="no text field"):
        load_articles(f)


def test_csv_with_only_header_raises(tmp_path):
    f = tmp_path / "empty.csv"
    f.write_text("id,title,text\n", encoding="utf-8")
    with pytest.raises(DataLoadError, match="No articles found"):
        load_articles(f)


def test_load_json_list(tmp_path):
    f = tmp_path / "list.json"
    f.write_text(
        json.dumps(
            [
                {"id": "a", "title": "T1", "text": "One."},
                {"id": "b", "title": "T2", "text": "Two."},
            ]
        ),
        encoding="utf-8",
    )
    articles = load_articles(f)
    assert [a.id for a in articles] == ["a", "b"]
    assert [a.title for a in articles] == ["T1", "T2"]
    assert [a.text for a in articles] == ["One.", "Two."]


def test_load_json_articles_key(tmp_path):
    f = tmp_path / "wrapped.json"
    f.write_text(json.dumps({"articles": [{"text": "One."}, {"text": "Two."}]}), encoding="utf-8")
    articles = load_articles(f)
    assert [a.id for a in articles] == ["1", "2"]
    assert [a.title for a in articles] == ["", ""]


def test_load_json_single_object(tmp_path):
    f = tmp_path / "single.json"
    f.write_text(json.dumps({"title": "Solo", "text": "Only one."}), encoding="utf-8")
    [article] = load_articles(f)
    assert article.id == "1"
    assert article.title == "Solo"
    assert article.text == "Only one."


def test_load_json_list_of_strings(tmp_path):
    f = tmp_path / "strings.json"
    f.write_text(json.dumps(["  First.  ", "Second."]), encoding="utf-8")
    articles = load_articles(f)
    assert [a.text for a in articles] == ["First.", "Second."]
    assert [a.id for a in articles] == ["1", "2"]
    assert [a.title for a in articles] == ["", ""]


@pytest.mark.parametrize("field", ["text", "content", "article", "body"])
def test_json_accepts_alternate_text_fields(tmp_path, field):
    f = tmp_path / "alt.json"
    f.write_text(json.dumps([{field: "Some words."}]), encoding="utf-8")
    [article] = load_articles(f)
    assert article.text == "Some words."


def test_json_invalid_raises(tmp_path):
    f = tmp_path / "broken.json"
    f.write_text("{not json", encoding="utf-8")
    with pytest.raises(DataLoadError, match="not valid JSON"):
        load_articles(f)


def test_json_wrong_top_level_type_raises(tmp_path):
    f = tmp_path / "number.json"
    f.write_text("42", encoding="utf-8")
    with pytest.raises(DataLoadError, match="expected a list"):
        load_articles(f)


def test_json_item_wrong_type_raises(tmp_path):
    f = tmp_path / "items.json"
    f.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(DataLoadError, match="must be an object or a string"):
        load_articles(f)


def test_json_missing_text_field_raises(tmp_path):
    f = tmp_path / "notext.json"
    f.write_text('[{"title": "x"}]', encoding="utf-8")
    with pytest.raises(DataLoadError, match="no text field"):
        load_articles(f)


def test_unsupported_extension_raises(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(DataLoadError, match="Unsupported file type"):
        load_articles(f)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        load_articles(tmp_path / "nope.txt")


def test_directory_passed_to_load_articles_raises(tmp_path):
    with pytest.raises(DataLoadError, match="Not a file"):
        load_articles(tmp_path)


def test_invalid_utf8_raises(tmp_path):
    f = tmp_path / "bad.txt"
    f.write_bytes(b"\xff\xfe\xfa bad")
    with pytest.raises(DataLoadError, match="not valid UTF-8"):
        load_articles(f)


def test_load_directory_mixed_files(tmp_path):
    (tmp_path / "b.txt").write_text("Bee.", encoding="utf-8")
    (tmp_path / "a.txt").write_text("Ay.", encoding="utf-8")
    (tmp_path / "c.csv").write_text("id,text\n1,Sea.\n", encoding="utf-8")
    (tmp_path / "ignored.pdf").write_text("nope", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.txt").write_text("Not recursive.", encoding="utf-8")
    articles = load_directory(tmp_path)
    assert [a.source for a in articles] == ["a.txt", "b.txt", "c.csv"]


def test_load_directory_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Folder not found"):
        load_directory(tmp_path / "missing")


def test_load_directory_without_supported_files_raises(tmp_path):
    (tmp_path / "ignored.pdf").write_text("nope", encoding="utf-8")
    with pytest.raises(DataLoadError, match="No supported files"):
        load_directory(tmp_path)


def test_load_directory_real_samples():
    articles = load_directory(SAMPLES)
    assert len(articles) == 7
    assert all(a.text.strip() for a in articles)
