import json
import logging
from pathlib import Path

from alin_core.logging_config import configure_json_logging, get_default_log_dir, log_event


def test_default_log_dir_uses_alin_logs():
    path = get_default_log_dir()
    assert "ALIN" in str(path)
    assert "Logs" in str(path)


def test_json_logging_writes_required_fields(tmp_path: Path):
    logger, log_path = configure_json_logging("alin.test.logging", log_dir=tmp_path)
    log_event(
        logger,
        event="pytest_logging_smoke",
        message="synthetic",
        context={"synthetic": True},
        level=logging.ERROR,
    )
    for handler in logger.handlers:
        handler.flush()

    payload = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["level"] == "ERROR"
    assert payload["event"] == "pytest_logging_smoke"
    assert payload["context"]["synthetic"] is True
