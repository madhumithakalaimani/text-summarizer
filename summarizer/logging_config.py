"""Logging setup shared by the CLI and the Flask API.

Call setup_logging() once at startup. It configures the root logger with
a rotating file handler (logs/app.log) and a console handler, so both the
CLI and the API log to the same place.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")
MAX_BYTES = 1_000_000  # 1 MB per file before rotating
BACKUP_COUNT = 3

_configured = False


def setup_logging(level=logging.INFO):
    """Configure root logging once. Safe to call multiple times."""
    global _configured
    if _configured:
        return
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s - %(message)s"
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _configured = True
