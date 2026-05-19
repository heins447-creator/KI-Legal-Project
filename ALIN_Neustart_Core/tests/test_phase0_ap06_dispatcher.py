import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_dispatcher(*args: str):
    result = subprocess.run(
        [sys.executable, str(ROOT / "alin.py"), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, json.loads(result.stdout)


def test_dispatcher_health_defaults_to_dry_run():
    code, payload = run_dispatcher("health")
    assert code == 0
    assert payload["mode"] == "dry-run"
    assert payload["status"] == "ok"


def test_dispatcher_blocks_redline_violation():
    code, payload = run_dispatcher("--dry-run", "redline-check", "--note", "https://example.invalid")
    assert code == 2
    assert payload["allowed"] is False
