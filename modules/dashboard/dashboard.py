"""
Dashboard Module — helper functions.
"""


def _bool_setting(value, default=True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def should_show_dashboard_section(value, default=True) -> bool:
    """Public helper: return whether a dashboard section should be shown."""
    return _bool_setting(value, default)
