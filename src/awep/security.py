from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

BLOCKED_METADATA = {ipaddress.ip_address("169.254.169.254")}


class UnsafeUrlError(ValueError):
    pass


def assert_url_safe(url: str, allow_private: bool = False) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError(f"blocked non-http scheme: {parsed.scheme or '<missing>'}")
    if not parsed.hostname:
        raise UnsafeUrlError("blocked URL without hostname")
    if allow_private:
        return
    for address in resolve_host(parsed.hostname):
        if is_private_address(address):
            raise UnsafeUrlError(f"blocked private or local address: {address}")


def resolve_host(hostname: str) -> list[ipaddress._BaseAddress]:
    try:
        literal = ipaddress.ip_address(hostname.strip("[]"))
        return [literal]
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"could not resolve host: {hostname}") from exc
    addresses = sorted({info[4][0] for info in infos})
    return [ipaddress.ip_address(address) for address in addresses]


def is_private_address(address: ipaddress._BaseAddress) -> bool:
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
        or address in BLOCKED_METADATA
    )
