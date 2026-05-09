"""Text helpers for Bale bot message limits."""

BALE_REPLY_MAX_CHARS = 4096


def split_reply_text(text: str, max_len: int = BALE_REPLY_MAX_CHARS) -> list[str]:
    if len(text) <= max_len:
        return [text] if text else [""]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + max_len])
        start += max_len
    return chunks
