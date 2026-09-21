"""Tests for the Flask API (app.py), using Flask's built-in test client."""
import pytest

import app as app_module
from app import create_app
from summarizer.pipeline import summarize_text

SAMPLE_TEXT = (
    "Solar power has grown quickly over the last decade. "
    "Panels are cheaper and more efficient than they used to be. "
    "Many countries now add more solar capacity than any other source. "
    "Batteries help store the energy for use at night. "
    "Households can cut their bills by installing rooftop systems. "
    "Engineers are also working on better ways to recycle old panels."
)


@pytest.fixture
def client():
    return create_app().test_client()


def post(client, payload):
    return client.post("/summarize", json=payload)


def assert_json_error(response, status):
    assert response.status_code == status
    assert response.is_json
    assert isinstance(response.get_json()["error"], str)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_summarize_defaults(client):
    response = post(client, {"text": SAMPLE_TEXT})
    assert response.status_code == 200
    body = response.get_json()
    assert body["method"] == "frequency"
    assert body["num_sentences"] == 3
    assert body["summary"].count(".") == 3
    assert body["original_words"] == len(SAMPLE_TEXT.split())
    assert body["summary_words"] == len(body["summary"].split())
    assert body["summary_words"] < body["original_words"]


def test_num_sentences_is_respected(client):
    body = post(client, {"text": SAMPLE_TEXT, "num_sentences": 1}).get_json()
    assert body["num_sentences"] == 1
    assert body["summary"].count(".") == 1


def test_num_sentences_larger_than_text_returns_whole_text(client):
    body = post(client, {"text": SAMPLE_TEXT, "num_sentences": 10}).get_json()
    assert body["summary_words"] == body["original_words"]


def test_textrank_matches_direct_call(client):
    response = post(client, {"text": SAMPLE_TEXT, "num_sentences": 2, "method": "textrank"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["method"] == "textrank"
    assert body["summary"] == summarize_text(SAMPLE_TEXT, 2, "textrank")


def test_method_is_case_insensitive_and_reported_in_lowercase(client):
    body = post(client, {"text": SAMPLE_TEXT, "method": "TextRank"}).get_json()
    assert body["method"] == "textrank"


@pytest.mark.parametrize("bad_text", [123, None, ["a"], "", "   ", "far too short"])
def test_bad_text_gives_400(client, bad_text):
    assert_json_error(post(client, {"text": bad_text}), 400)


def test_too_short_message_is_passed_through(client):
    response = post(client, {"text": "far too short"})
    assert "too short" in response.get_json()["error"]


def test_missing_text_gives_400(client):
    response = post(client, {"num_sentences": 2})
    assert_json_error(response, 400)
    assert "text" in response.get_json()["error"]


@pytest.mark.parametrize("bad_value", [0, -1, True, "3", 2.5, None])
def test_bad_num_sentences_gives_400(client, bad_value):
    response = post(client, {"text": SAMPLE_TEXT, "num_sentences": bad_value})
    assert_json_error(response, 400)
    assert "num_sentences" in response.get_json()["error"]


@pytest.mark.parametrize("bad_method", ["magic", 5])
def test_bad_method_gives_400(client, bad_method):
    assert_json_error(post(client, {"text": SAMPLE_TEXT, "method": bad_method}), 400)


def test_non_json_content_type_gives_415(client):
    response = client.post("/summarize", data="hello", content_type="text/plain")
    assert_json_error(response, 415)


def test_invalid_json_gives_400(client):
    response = client.post("/summarize", data="{not json", content_type="application/json")
    assert_json_error(response, 400)


def test_json_array_body_gives_400(client):
    assert_json_error(post(client, [SAMPLE_TEXT]), 400)


def test_unknown_route_gives_json_404(client):
    assert_json_error(client.get("/nope"), 404)


def test_wrong_method_gives_json_405_with_allow_header(client):
    response = client.get("/summarize")
    assert_json_error(response, 405)
    assert "POST" in response.headers["Allow"]


def test_oversized_body_gives_json_413(client):
    body = b'{"text": "' + b"a" * (6 * 1024 * 1024) + b'"}'
    response = client.post("/summarize", data=body, content_type="application/json")
    assert_json_error(response, 413)


def test_unexpected_error_gives_generic_500(client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(app_module, "summarize_text", boom)
    response = post(client, {"text": SAMPLE_TEXT})
    assert_json_error(response, 500)
    assert "secret" not in response.get_data(as_text=True)
