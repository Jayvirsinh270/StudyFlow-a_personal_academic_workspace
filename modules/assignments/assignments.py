"""
Assignments Module — helper functions.
"""

from datetime import datetime, date


def get_due_state_label(due_date: str | None) -> str:
    """Return a short, human-readable label for assignment urgency."""
    if not due_date:
        return "No due date"
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
        delta = (due - date.today()).days
    except ValueError:
        return "Needs review"
    if delta < 0:
        return "Overdue"
    if delta == 0:
        return "Due today"
    if delta == 1:
        return "Due tomorrow"
    if delta <= 7:
        return "Due soon"
    return "On track"
