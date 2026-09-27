"""Verify logging is configured and requests emit log records."""
import logging

from summarizer.logging_config import setup_logging


def test_setup_logging_adds_handlers(tmp_path, monkeypatch):
    import summarizer.logging_config as lc

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(lc, "_configured", False)
    root = logging.getLogger()
    handlers_before = list(root.handlers)
    setup_logging()
    assert len(root.handlers) >= len(handlers_before) + 2
    for h in root.handlers[-2:]:
        root.removeHandler(h)


def test_health_endpoint_logs(caplog):
    from app import create_app

    app = create_app()
    client = app.test_client()
    with caplog.at_level(logging.INFO):
        response = client.get("/health")
    assert response.status_code == 200
    assert any("health check requested" in record.message for record in caplog.records)


def test_summarize_endpoint_logs_success(caplog):
    from app import create_app

    app = create_app()
    client = app.test_client()
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/summarize",
            json={
                "text": (
                    "Cats are great pets that bring joy to many families "
                    "every single day. Dogs are loyal companions who love "
                    "long walks outside. Birds sing cheerful songs early "
                    "in the calm quiet morning."
                )
            },
        )
    assert response.status_code == 200
    assert any("summarize succeeded" in record.message for record in caplog.records)


def test_summarize_endpoint_logs_failure(caplog):
    from app import create_app

    app = create_app()
    client = app.test_client()
    with caplog.at_level(logging.INFO):
        response = client.post("/summarize", json={"text": 123})
    assert response.status_code == 400
    assert any("summarize failed" in record.message for record in caplog.records)
