"""Flask API for the text summarizer.

Run it with:  python app.py   (or: flask --app app run)

Endpoints:
  GET  /health     -> {"status": "ok"}
  POST /summarize  -> JSON in, JSON out (see README, section "API")
"""
import json
import os

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from summarizer.pipeline import summarize_text
from summarizer.preprocessing import NLTKDataError
from summarizer.validation import (
    InvalidInputError,
    validate_method,
    validate_num_sentences,
)

DEFAULT_NUM_SENTENCES = 3
DEFAULT_METHOD = "frequency"
MAX_REQUEST_BYTES = 5 * 1024 * 1024  # room for the 1,000,000 character text limit


def _error(message, status):
    return jsonify({"error": message}), status


def create_app():
    """Build the Flask app (a factory, so tests get a fresh one)."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/summarize")
    def summarize():
        if not request.is_json:
            return _error("Content-Type must be application/json.", 415)
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return _error("Request body must be a valid JSON object.", 400)
        if "text" not in data:
            return _error("Missing required field: text.", 400)
        try:
            method = validate_method(data.get("method", DEFAULT_METHOD))
            num_sentences = validate_num_sentences(
                data.get("num_sentences", DEFAULT_NUM_SENTENCES)
            )
            summary = summarize_text(
                data["text"], num_sentences=num_sentences, method=method
            )
        except InvalidInputError as exc:
            return _error(str(exc), 400)
        except NLTKDataError as exc:
            app.logger.error("NLTK data unavailable: %s", exc)
            return _error(
                "Summarizer is temporarily unavailable: required language "
                "data could not be loaded.",
                503,
            )
        return jsonify(
            {
                "summary": summary,
                "method": method,
                "num_sentences": num_sentences,
                "original_words": len(data["text"].split()),
                "summary_words": len(summary.split()),
            }
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        # Keep the standard headers (for example Allow on a 405), send JSON.
        response = exc.get_response()
        response.data = json.dumps({"error": exc.description})
        response.content_type = "application/json"
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        app.logger.exception("Unexpected error while handling %s", request.path)
        return _error("Internal server error.", 500)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
