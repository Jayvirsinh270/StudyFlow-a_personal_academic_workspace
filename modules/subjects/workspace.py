"""
Subject Workspace — helper functions.
"""


def build_note_preview(content: str | None, max_length: int = 70) -> str:
    """Create a short preview for note cards from raw note content."""
    if content is None:
        return "No content yet"

    text = str(content).replace("\r\n", "\n").replace("\r", "\n")
    first_line = next((line.strip() for line in text.split("\n") if line.strip()), "")
    if not first_line:
        return "No content yet"

    cleaned = " ".join(first_line.split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip() + "..."
