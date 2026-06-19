from __future__ import annotations

import re

from awep.models import QualityEvidence

ANTIBOT_PHRASES = {
    "captcha": "captcha",
    "access denied": "access_denied",
    "unusual traffic": "unusual_traffic",
    "too many requests": "too_many_requests",
}
SOFT_ANTIBOT_PHRASES = ("anti-bot", "captcha", "cloudflare", "headless", "recaptcha")
STRONG_INTERSTITIAL_PHRASES = {
    "checking your browser": "checking_your_browser",
    "cf-chl": "cloudflare_interstitial",
    "cf_chl": "cloudflare_interstitial",
    "cloudflare challenge": "cloudflare_interstitial",
    "just a moment": "cloudflare_interstitial",
    "turnstile": "cloudflare_interstitial",
    "verify you are human": "verify_you_are_human",
}
WEAK_LOGIN_LINK_PHRASES = ("sign in", "log in", "sign up", "create an account")
HARD_LOGIN_WALL_PHRASES = (
    "login required",
    "sign in to continue",
    "please sign in to continue",
    "you must sign in",
    "you need to sign in",
    "authentication required",
    "requires authentication",
    "this page requires authentication",
)
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
    text_chars = len(text.strip())
    is_substantial_page = status_code == 200 and text_chars >= 1000 and bool((title or "").strip())
    if status_code in {401, 403, 407, 429}:
        flags.append(f"http_{status_code}")
        reasons.append(f"HTTP status {status_code} indicates blocked or rate-limited access")
    if status_code == 401:
        flags.append("login_wall_text")
        reasons.append("HTTP status 401 indicates authentication is required")
    if status_code == 503 and any(word in lowered for word in ("bot", "captcha", "cloudflare")):
        flags.append("http_503")
        reasons.append("HTTP 503 with anti-bot wording")
    if redirect_count:
        flags.append("redirected")
    has_soft_antibot = any(phrase in lowered for phrase in SOFT_ANTIBOT_PHRASES)
    if has_soft_antibot:
        flags.append("anti_bot_terms_present")
    for phrase, flag in STRONG_INTERSTITIAL_PHRASES.items():
        if phrase in lowered:
            flags.append(flag)
    for phrase, flag in ANTIBOT_PHRASES.items():
        if phrase in lowered and (not is_substantial_page or status_code in {403, 407, 429, 503}):
            flags.append(flag)
    has_hard_login = any(
        re.search(rf"\b{re.escape(phrase)}\b", lowered) for phrase in HARD_LOGIN_WALL_PHRASES
    )
    has_weak_login = any(
        re.search(rf"\b{re.escape(phrase)}\b", lowered) for phrase in WEAK_LOGIN_LINK_PHRASES
    )
    if has_hard_login:
        flags.append("login_wall_text")
    elif has_weak_login and not is_substantial_page:
        flags.append("login_wall_text")
    elif has_weak_login:
        flags.append("login_link_present")
    if any(phrase in lowered for phrase in JS_PHRASES):
        flags.append("enable_javascript_text")
    if (
        content_type
        and "html" not in content_type.lower()
        and "text/plain" not in content_type.lower()
    ):
        flags.append("non_html")
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
