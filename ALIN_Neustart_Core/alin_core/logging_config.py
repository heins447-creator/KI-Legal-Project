"""Strukturiertes JSON-Logging fuer ALIN.

Die Standardablage liegt unter %LocalAppData%/ALIN/Logs. Fuer Tests kann
ein anderer Basisordner uebergeben werden.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_APP_NAME = "ALIN"
DEFAULT_LOG_FILE = "alin.jsonl"


class JsonLineFormatter(logging.Formatter):
    """Formatiert LogRecords als einzelne JSON-Zeilen."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
        }
        for key in ["event", "context"]:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def get_default_log_dir(app_name: str = DEFAULT_APP_NAME) -> Path:
    """Gibt den lokalen Standard-Logordner zurueck."""

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / app_name / "Logs"
    return Path.home() / "AppData" / "Local" / app_name / "Logs"


def configure_json_logging(
    logger_name: str = "alin",
    *,
    log_dir: Path | None = None,
    log_file: str = DEFAULT_LOG_FILE,
    level: int = logging.INFO,
) -> tuple[logging.Logger, Path]:
    """Konfiguriert einen Logger mit JSONL-Dateiausgabe."""

    target_dir = log_dir or get_default_log_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    log_path = target_dir / log_file

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False
    logger.handlers.clear()

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(JsonLineFormatter())
    logger.addHandler(handler)
    return logger, log_path


def log_event(
    logger: logging.Logger,
    *,
    event: str,
    message: str,
    context: dict[str, Any] | None = None,
    level: int = logging.INFO,
) -> None:
    """Schreibt ein strukturiertes Ereignis."""

    logger.log(level, message, extra={"event": event, "context": context or {}})
