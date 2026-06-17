from __future__ import annotations

import hashlib
import json
import re
import secrets
from datetime import UTC, datetime

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def utc_now_str() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_run_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"run-{stamp}-{secrets.token_hex(3)}"


def make_event_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"evt-{stamp}-{secrets.token_hex(4)}"


def validate_safe_id(value: str, label: str) -> str:
    if not value or not SAFE_ID_RE.match(value) or value in {".", ".."}:
        raise ValueError(f"unsafe {label}: {value!r}")
    return value


def compact(value: str | None, limit: int = 140) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."
