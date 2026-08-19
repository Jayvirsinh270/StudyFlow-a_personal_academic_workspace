"""
Timetable Module — helper functions.
"""


def build_planner_focus_summary(today_entries: list, day_events: list) -> str:
    class_count = len(today_entries)
    event_count = len(day_events)
    if not class_count and not event_count:
        return "A calm day ahead — no classes or events planned yet."
    parts = []
    if class_count:
        parts.append(f"{class_count} class{'es' if class_count != 1 else ''}")
    if event_count:
        parts.append(f"{event_count} event{'s' if event_count != 1 else ''}")
    return f"Today's focus: {' and '.join(parts)} on your schedule."
