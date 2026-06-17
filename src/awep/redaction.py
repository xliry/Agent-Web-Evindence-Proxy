from __future__ import annotations

from urllib.parse import parse_qsl, quote, urlsplit, urlunsplit

REDACTED = "[REDACTED]"
SECRET_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "proxy-authorization",
}
SECRET_QUERY_PARTS = ("key", "token", "secret", "password", "auth", "session", "signature", "sig")


def redact_headers(headers: dict[str, str] | None) -> dict[str, str]:
    return {
        name: REDACTED if name.lower() in SECRET_HEADERS else value
        for name, value in (headers or {}).items()
    }


def _is_secret_param(name: str) -> bool:
    lowered = name.lower()
    return any(part in lowered for part in SECRET_QUERY_PARTS)


def redact_url(url: str) -> str:
    parsed = urlsplit(url)
    pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        safe_value = REDACTED if _is_secret_param(key) else value
        pairs.append(f"{quote(key)}={quote(safe_value, safe='[]')}")
    query = "&".join(pairs)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))
