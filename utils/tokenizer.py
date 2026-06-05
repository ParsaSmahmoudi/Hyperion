"""Simple token estimation utility"""


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def truncate_to_limit(text: str, max_tokens: int) -> str:
    estimated = estimate_tokens(text)
    if estimated <= max_tokens:
        return text
    ratio = max_tokens / estimated
    truncated_len = int(len(text) * ratio)
    return text[:truncated_len] + "\n[truncated...]"
