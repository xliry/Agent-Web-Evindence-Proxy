from __future__ import annotations

import re

from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown


def extract_content(body: bytes, content_type: str | None) -> tuple[str | None, str, str]:
    decoded = decode_body(body)
    if is_html(content_type, decoded):
        soup = BeautifulSoup(decoded, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else None
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        markdown = html_to_markdown(str(soup), heading_style="ATX").strip()
        text = soup.get_text(" ", strip=True)
        return title, clean_text(markdown), clean_text(text)
    text = clean_text(decoded)
    return None, text, text


def decode_body(body: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace")


def is_html(content_type: str | None, decoded: str) -> bool:
    lowered = (content_type or "").lower()
    return "html" in lowered or "<html" in decoded[:500].lower()


def clean_text(value: str) -> str:
    value = value.replace("\x00", "")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\n\s*\n\s*\n+", "\n\n", value)
    return value.strip()
