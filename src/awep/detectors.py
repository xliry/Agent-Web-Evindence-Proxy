from __future__ import annotations

import re

from awep.models import QualityEvidence

ANTIBOT_PHRASES = {
    "captcha": "captcha",
    "verify you are human": "verify_you_are_human",
    "checking your browser": "checking_your_browser",
    "cloudflare": "cloudflare_interstitial",
    "access denied": "access_denied",
    "unusual traffic": "unusual_traffic",
    "too many requests": "too_many_requests",
}
LOGIN_PHRASES = ("sign in", "log in", "login required", "create an account")
JS_PHRASES = ("enable javascript", "please enable javascript", "javascript is disabled")


def classify_quality(
    status_code: int | None,
    title: str | None,
    text: str,
    html: str,
    content_type: str | None,
    error: str | None = None,
    redirect_count: int = 0,
) -> QualityEvidence:
    flags: list[str] = []
    reasons: list[str] = []
    if error:
        return QualityEvidence(status="error", flags=["network_error"], reasons=[error])
    lowered = f"{title or ''}\n{text}\n{html[:2000]}".lower()
    if status_code in {401, 403, 407, 429}:
        flags.append(f"http_{status_code}")
        reasons.append(f"HTTP status {status_code} indicates blocked or rate-limited access")
    if status_code == 503 and any(word in lowered for word in ("bot", "captcha", "cloudflare")):
        flags.append("http_503")
        reasons.append("HTTP 503 with anti-bot wording")
    if redirect_count:
        flags.append("redirected")
    for phrase, flag in ANTIBOT_PHRASES.items():
        if phrase in lowered:
            flags.append(flag)
    if any(re.search(rf"\b{re.escape(phrase)}\b", lowered) for phrase in LOGIN_PHRASES):
        flags.append("login_wall_text")
    if any(phrase in lowered for phrase in JS_PHRASES):
        flags.append("enable_javascript_text")
    if (
        content_type
        and "html" not in content_type.lower()
        and "text/plain" not in content_type.lower()
    ):
        flags.append("non_html")
    text_chars = len(text.strip())
    if text_chars < 80:
        flags.append("low_text_chars")
        reasons.append("Extracted text is very short")
    if html and html.lower().count("<script") >= 8 and text_chars < 500:
        flags.append("script_heavy")
        reasons.append("Page is script-heavy with little extracted text")
    unique_flags = sorted(set(flags))
    if "login_wall_text" in unique_flags:
        status = "login_required"
    elif "enable_javascript_text" in unique_flags:
        status = "js_required"
    elif any(flag.startswith("http_") for flag in unique_flags) or any(
        flag in unique_flags
        for flag in {
            "captcha",
            "verify_you_are_human",
            "checking_your_browser",
            "cloudflare_interstitial",
            "access_denied",
            "unusual_traffic",
            "too_many_requests",
        }
    ):
        status = "blocked"
    elif "low_text_chars" in unique_flags:
        status = "empty"
    else:
        status = "ok"
    return QualityEvidence(status=status, flags=unique_flags, reasons=reasons)
