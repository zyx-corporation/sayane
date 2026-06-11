"""Unit tests for serve Network Policy host validation."""

from __future__ import annotations

import ipaddress
import pytest


# ---------- helpers (mirrors the logic in cli/app.py) ----------

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
ALL_INTERFACES_HOSTS = frozenset({"0.0.0.0", "::"})


def classify_host(host: str) -> str:
    """Return exposure classification for a host string."""
    lower = host.lower().strip()
    if lower in ALL_INTERFACES_HOSTS:
        return "all_interfaces"
    if lower in LOOPBACK_HOSTS:
        return "localhost"
    return "non_localhost"


def is_private_ip(addr: str) -> bool:
    """Check if addr is a private/reserved IP (including CGNAT)."""
    try:
        ip = ipaddress.ip_address(addr)
        # Exclude unspecified addresses (0.0.0.0, ::)
        if ip.is_unspecified:
            return False
        if isinstance(ip, ipaddress.IPv4Address):
            return (
                ip.is_private
                or ip.is_loopback
                or ip in ipaddress.IPv4Network("100.64.0.0/10")
            )
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False


def validate_host(host: str, allow_all: bool) -> tuple[bool, str]:
    """Validate host against Network Policy.

    Returns (allowed, error_message_or_empty_string).
    """
    lower = host.lower().strip()

    if lower in ALL_INTERFACES_HOSTS and not allow_all:
        return False, f"Refusing to bind to {host} without --allow-all-interfaces."

    return True, ""


# ---------- tests ----------


class TestClassifyHost:
    def test_localhost_127(self) -> None:
        assert classify_host("127.0.0.1") == "localhost"

    def test_localhost_ipv6(self) -> None:
        assert classify_host("::1") == "localhost"

    def test_localhost_name(self) -> None:
        assert classify_host("localhost") == "localhost"

    def test_private_ip(self) -> None:
        assert classify_host("192.168.33.32") == "non_localhost"

    def test_all_interfaces_v4(self) -> None:
        assert classify_host("0.0.0.0") == "all_interfaces"

    def test_all_interfaces_v6(self) -> None:
        assert classify_host("::") == "all_interfaces"

    def test_tailscale_ip(self) -> None:
        assert classify_host("100.64.0.1") == "non_localhost"


class TestIsPrivateIp:
    def test_loopback_v4(self) -> None:
        assert is_private_ip("127.0.0.1")

    def test_loopback_v6(self) -> None:
        assert is_private_ip("::1")

    def test_private_v4_class_c(self) -> None:
        assert is_private_ip("192.168.1.1")

    def test_private_v4_class_a(self) -> None:
        assert is_private_ip("10.0.0.1")

    def test_private_v4_class_b(self) -> None:
        assert is_private_ip("172.16.0.1")

    def test_cgnat_tailscale(self) -> None:
        assert is_private_ip("100.64.0.1")

    def test_public_ip(self) -> None:
        assert not is_private_ip("8.8.8.8")

    def test_public_ipv6(self) -> None:
        assert not is_private_ip("2001:4860:4860::8888")

    def test_ula_ipv6(self) -> None:
        assert is_private_ip("fd00::1")

    def test_hostname(self) -> None:
        assert not is_private_ip("noor.local")


class TestValidateHost:
    # --- allowed cases ---

    def test_default_localhost(self) -> None:
        ok, msg = validate_host("127.0.0.1", False)
        assert ok
        assert msg == ""

    def test_explicit_ipv6_localhost(self) -> None:
        ok, msg = validate_host("::1", False)
        assert ok
        assert msg == ""

    def test_localhost_name(self) -> None:
        ok, msg = validate_host("localhost", False)
        assert ok
        assert msg == ""

    def test_private_ip_allowed(self) -> None:
        ok, msg = validate_host("192.168.33.32", False)
        assert ok
        assert msg == ""

    def test_tailscale_ip_allowed(self) -> None:
        ok, msg = validate_host("100.64.0.1", False)
        assert ok
        assert msg == ""

    def test_all_interfaces_with_opt_in_v4(self) -> None:
        ok, msg = validate_host("0.0.0.0", True)
        assert ok
        assert msg == ""

    def test_all_interfaces_with_opt_in_v6(self) -> None:
        ok, msg = validate_host("::", True)
        assert ok
        assert msg == ""

    def test_hostname_allowed(self) -> None:
        ok, msg = validate_host("noor.local", False)
        assert ok
        assert msg == ""

    # --- rejected cases ---

    def test_all_interfaces_v4_rejected(self) -> None:
        ok, msg = validate_host("0.0.0.0", False)
        assert not ok
        assert "without --allow-all-interfaces" in msg

    def test_all_interfaces_v6_rejected(self) -> None:
        ok, msg = validate_host("::", False)
        assert not ok
        assert "without --allow-all-interfaces" in msg


class TestNetworkPolicyClassification:
    """Integration-style: verify classification × private detection combos."""

    def test_localhost_is_loopback_and_private(self) -> None:
        assert classify_host("127.0.0.1") == "localhost"
        assert is_private_ip("127.0.0.1")

    def test_private_lan_is_non_localhost_and_private(self) -> None:
        assert classify_host("192.168.33.32") == "non_localhost"
        assert is_private_ip("192.168.33.32")

    def test_public_ip_is_non_localhost_and_not_private(self) -> None:
        assert classify_host("8.8.8.8") == "non_localhost"
        assert not is_private_ip("8.8.8.8")

    def test_all_interfaces_is_neither_loopback_nor_private(self) -> None:
        assert classify_host("0.0.0.0") == "all_interfaces"
        assert not is_private_ip("0.0.0.0")
