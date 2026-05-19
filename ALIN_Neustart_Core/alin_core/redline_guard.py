"""Technische Sperrpruefung fuer ALIN rote Linien."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REDLINES = ROOT / ".alin" / "redlines.json"
DEFAULT_SCHEMA = ROOT / ".alin" / "redlines.schema.json"


@dataclass(frozen=True)
class RedlineFinding:
    rule_id: str
    title: str
    severity: str
    pattern: str


@dataclass(frozen=True)
class RedlineDecision:
    allowed: bool
    findings: tuple[RedlineFinding, ...]

    @property
    def status(self) -> str:
        return "allowed" if self.allowed else "blocked"


def load_redlines(path: Path = DEFAULT_REDLINES) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_redlines_structure(redlines: dict[str, Any]) -> None:
    if redlines.get("schema_version") != "1.0":
        raise ValueError("redlines.schema_version muss 1.0 sein.")
    rules = redlines.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("redlines.rules fehlt oder ist leer.")
    seen: set[str] = set()
    for rule in rules:
        for key in ["id", "title", "severity", "blocker", "patterns"]:
            if key not in rule:
                raise ValueError(f"Redline-Regel ohne Pflichtfeld {key}.")
        if rule["id"] in seen:
            raise ValueError(f"Doppelte Redline-ID: {rule['id']}")
        seen.add(rule["id"])
        if rule["severity"] not in {"block", "warn"}:
            raise ValueError(f"Ungueltige severity: {rule['severity']}")
        if not isinstance(rule["patterns"], list) or not rule["patterns"]:
            raise ValueError(f"Regel ohne patterns: {rule['id']}")


def _action_text(action: dict[str, Any]) -> str:
    return json.dumps(action, ensure_ascii=False, sort_keys=True).lower()


def _path_outside_workspace(action: dict[str, Any], workspace_root: Path) -> bool:
    for raw_path in action.get("paths", []):
        path = Path(raw_path)
        resolved = path if path.is_absolute() else workspace_root / path
        try:
            resolved.resolve().relative_to(workspace_root.resolve())
        except ValueError:
            return True
    return False


def evaluate_action(
    action: dict[str, Any],
    *,
    workspace_root: Path = ROOT,
    redlines_path: Path = DEFAULT_REDLINES,
) -> RedlineDecision:
    redlines = load_redlines(redlines_path)
    validate_redlines_structure(redlines)
    text = _action_text(action)
    findings: list[RedlineFinding] = []

    for rule in redlines["rules"]:
        for pattern in rule["patterns"]:
            matched = False
            if pattern == "path_outside_workspace":
                matched = _path_outside_workspace(action, workspace_root)
            else:
                matched = pattern.lower() in text
            if matched:
                findings.append(
                    RedlineFinding(
                        rule_id=rule["id"],
                        title=rule["title"],
                        severity=rule["severity"],
                        pattern=pattern,
                    )
                )

    blocked = any(finding.severity == "block" for finding in findings)
    return RedlineDecision(allowed=not blocked, findings=tuple(findings))
