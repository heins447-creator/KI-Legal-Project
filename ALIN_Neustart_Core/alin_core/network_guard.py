"""App-interne Outbound-Sperre fuer ALIN."""

from __future__ import annotations

import json
import socket
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "Config" / "phase0_ap07_network_guard_v1.json"


class NetworkBlockedError(PermissionError):
    """Wird ausgelöst, wenn ein Outbound-Zugriff blockiert wird."""


def load_network_policy(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))["policy"]


def normalize_host(host: str) -> str:
    return host.strip().lower().rstrip(".")


def check_outbound_allowed(
    host: str,
    port: int,
    *,
    update_click: bool = False,
    policy: dict[str, Any] | None = None,
) -> None:
    active_policy = policy or load_network_policy()
    normalized_host = normalize_host(host)
    update_hosts = {normalize_host(item) for item in active_policy.get("update_hosts", [])}

    if (
        update_click
        and active_policy.get("update_channel_requires_explicit_click") is True
        and normalized_host in update_hosts
    ):
        return

    raise NetworkBlockedError(
        f"Outbound-Verbindung blockiert: {normalized_host}:{port}"
    )


def _extract_host_port(address) -> tuple[str, int]:
    if isinstance(address, tuple) and len(address) >= 2:
        return str(address[0]), int(address[1])
    return str(address), 0


@contextmanager
def enforce_network_guard(policy: dict[str, Any] | None = None) -> Iterator[None]:
    """Blockiert socket.connect und socket.create_connection im Kontext."""

    original_socket_connect = socket.socket.connect
    original_create_connection = socket.create_connection

    def guarded_socket_connect(sock, address):
        host, port = _extract_host_port(address)
        check_outbound_allowed(host, port, policy=policy)
        return original_socket_connect(sock, address)

    def guarded_create_connection(address, timeout=None, source_address=None, all_errors=False):
        host, port = _extract_host_port(address)
        check_outbound_allowed(host, port, policy=policy)
        return original_create_connection(address, timeout, source_address, all_errors)

    socket.socket.connect = guarded_socket_connect
    socket.create_connection = guarded_create_connection
    try:
        yield
    finally:
        socket.socket.connect = original_socket_connect
        socket.create_connection = original_create_connection
