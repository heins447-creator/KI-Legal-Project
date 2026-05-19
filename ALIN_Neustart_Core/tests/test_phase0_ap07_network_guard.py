import socket

import pytest

from alin_core.network_guard import NetworkBlockedError, check_outbound_allowed, enforce_network_guard


def test_outbound_is_blocked_by_default():
    with pytest.raises(NetworkBlockedError):
        check_outbound_allowed("example.invalid", 443)


def test_update_host_requires_click_and_allowlist():
    policy = {
        "default_outbound": "deny",
        "update_channel_requires_explicit_click": True,
        "update_hosts": ["updates.alin.invalid"],
    }
    check_outbound_allowed("updates.alin.invalid", 443, update_click=True, policy=policy)


def test_socket_create_connection_is_blocked():
    with enforce_network_guard():
        with pytest.raises(NetworkBlockedError):
            socket.create_connection(("example.invalid", 443), timeout=1)
