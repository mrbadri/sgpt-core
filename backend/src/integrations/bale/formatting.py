"""Text helpers for Bale bot message limits."""

import re

BALE_REPLY_MAX_CHARS = 4096


def markdown_to_bale_markdown(text: str) -> str:
    """Light cleanup so LLM output is safe for Bale Markdown parse_mode.

    The LLM is instructed to produce Bale-native Markdown directly (*bold*,
    _italic_, `code`).  This function only fixes the common mistake of
    double-asterisk/underscore that the model occasionally slips into.
    """
    # **bold** → *bold*  (must run before single-* rule)
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text, flags=re.DOTALL)
    # __bold__ → *bold*
    text = re.sub(r"__(.+?)__", r"*\1*", text, flags=re.DOTALL)
    # ~~strikethrough~~ → just unwrap (not supported)
    text = re.sub(r"~~(.+?)~~", r"\1", text, flags=re.DOTALL)
    # Markdown headers → bold line
    text = re.sub(r"^#{1,6}\s+(.*)", r"*\1*", text, flags=re.MULTILINE)
    # Collapse 3+ blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_reply_text(text: str, max_len: int = BALE_REPLY_MAX_CHARS) -> list[str]:
    if len(text) <= max_len:
        return [text] if text else [""]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + max_len])
        start += max_len
    return chunks
