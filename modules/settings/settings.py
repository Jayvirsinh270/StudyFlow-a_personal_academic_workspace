"""
Settings Module — helper functions.
"""


def _bool_pref(value, default=False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def parse_preference_value(value, default=False) -> bool:
    """Public helper: parse a stored preference value into a bool."""
    return _bool_pref(value, default)
