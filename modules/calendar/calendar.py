"""
Calendar Module — helper functions.
"""


def _build_day_summary(day_events: list, timetable_entries: list, day_name: str) -> str:
    """Return a short human-readable summary for the selected day."""
    ev = len(day_events)
    cls = len(timetable_entries)
    parts = []
    if ev:
        parts.append(f"{ev} event{'s' if ev != 1 else ''}")
    if cls:
        parts.append(f"{cls} class{'es' if cls != 1 else ''}")
    if not parts:
        return "Nothing scheduled — enjoy the free time!"
    summary = f"{' and '.join(parts)} planned for {day_name}."
    if ev and cls:
        return summary.replace("event and class", "event and 1 class") if ev == 1 and cls == 1 else summary
    return summary


# Public alias used by tests and external callers
build_day_plan_summary = _build_day_summary
