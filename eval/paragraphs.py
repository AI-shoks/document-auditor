import re


def split_paragraphs(text: str) -> list[str]:
    """Split document text into paragraphs on blank lines.

    Single source of truth for paragraph numbering — used both by the
    eval harness (to build the numbered prompt) and by show_paragraphs.py
    (so a human can pick the same paragraph numbers for ground truth).
    """
    parts = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in parts if p.strip()]


def number_paragraphs(text: str) -> str:
    paragraphs = split_paragraphs(text)
    return "\n\n".join(f"[P{i}] {p}" for i, p in enumerate(paragraphs, start=1))
