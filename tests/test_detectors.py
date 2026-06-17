from pathlib import Path

import pytest

from awep.detectors import classify_quality
from awep.extraction import decode_body, extract_content


def classify_fixture(name: str):
    body = (Path(__file__).parent / "fixtures" / name).read_bytes()
    title, _markdown, text = extract_content(body, "text/html")
    return classify_quality(200, title, text, decode_body(body), "text/html")


@pytest.mark.parametrize(
    ("name", "status", "flag"),
    [
        ("normal.html", "ok", None),
        ("captcha.html", "blocked", "captcha"),
        ("login.html", "login_required", "login_wall_text"),
        ("empty.html", "empty", "low_text_chars"),
        ("js_required.html", "js_required", "enable_javascript_text"),
    ],
)
def test_classifies_fixtures(name: str, status: str, flag: str | None) -> None:
    quality = classify_fixture(name)
    assert quality.status == status
    if flag:
        assert flag in quality.flags


@pytest.mark.parametrize("status_code", [403, 429])
def test_blocked_http_statuses(status_code: int) -> None:
    quality = classify_quality(status_code, "Denied", "Access denied " * 30, "", "text/html")
    assert quality.status == "blocked"
    assert f"http_{status_code}" in quality.flags
