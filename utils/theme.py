"""
StudyFlow Design System — v2
Inspired by Notion, Linear, Todoist, and Microsoft Fluent.

CustomTkinter widgets accept (light_color, dark_color) tuples.
When ctk.set_appearance_mode() changes every widget auto-repaints.

Spacing system: 8 / 16 / 24 / 32 px grid.
Radius system : 6 / 10 / 14 / 16 px.
"""

# ── Background Hierarchy ─────────────────────────────────────────────────────
BG_MAIN    = ("#F8FAFC", "#0F1117")         # outermost window
BG_SURFACE = ("#FFFFFF", "#1A1D27")         # cards, panels
BG_SIDEBAR = ("#F1F5F9", "#13161F")         # left nav
BG_HEADER  = ("#FFFFFF", "#161921")         # top bar
BG_INPUT   = ("#F8FAFC", "#1E2130")         # entry / search fields
BG_HOVER   = ("#EFF6FF", "#1E2740")         # hover / highlight
BG_CHIP    = ("#EEF2FF", "#1E2535")         # small pills / tags
BG_CARD    = ("#FFFFFF", "#1E2130")         # raised cards
BG_ROW     = ("#F8FAFC", "#181B26")         # alternating table rows
BG_OVERLAY = ("#F1F5F9", "#161A24")         # subtle overlay
BG_ACTIVE  = ("#EFF6FF", "#1E2F50")         # active nav item bg (non-accent)

# ── Text ─────────────────────────────────────────────────────────────────────
TEXT_PRIMARY   = ("#1E293B", "#F1F5F9")
TEXT_SECONDARY = ("#64748B", "#94A3B8")
TEXT_MUTED     = ("#94A3B8", "#475569")
TEXT_ON_ACCENT = ("#FFFFFF", "#FFFFFF")
TEXT_ON_DARK   = ("#FFFFFF", "#FFFFFF")

# ── Brand Accent ─────────────────────────────────────────────────────────────
ACCENT         = ("#2563EB", "#3B82F6")
ACCENT_HOVER   = ("#1D4ED8", "#2563EB")
ACCENT_LIGHT   = ("#EFF6FF", "#1E3A5F")
ACCENT_SUBTLE  = ("#DBEAFE", "#1E3259")

# ── Status Colors ────────────────────────────────────────────────────────────
SUCCESS        = ("#16A34A", "#22C55E")
SUCCESS_LIGHT  = ("#F0FDF4", "#052E16")
WARNING        = ("#D97706", "#F59E0B")
WARNING_LIGHT  = ("#FFFBEB", "#451A03")
DANGER         = ("#DC2626", "#EF4444")
DANGER_LIGHT   = ("#FEF2F2", "#450A0A")
INFO           = ("#0284C7", "#38BDF8")
INFO_LIGHT     = ("#F0F9FF", "#082F49")

# ── Border / Divider ─────────────────────────────────────────────────────────
BORDER         = ("#E2E8F0", "#1E2535")
BORDER_FOCUS   = ("#2563EB", "#3B82F6")
BORDER_STRONG  = ("#CBD5E1", "#2D3554")

# ── Priority badge colors ─────────────────────────────────────────────────────
PRIORITY_HIGH   = "#EF4444"
PRIORITY_MEDIUM = "#F59E0B"
PRIORITY_LOW    = "#22C55E"

# ── Attendance status colors ──────────────────────────────────────────────────
ATTENDANCE_GOOD     = "#22C55E"   # ≥ 75 %
ATTENDANCE_WARNING  = "#F59E0B"   # 60–74 %
ATTENDANCE_CRITICAL = "#EF4444"   # < 60 %

# ── Subject accent palette ────────────────────────────────────────────────────
SUBJECT_COLORS = [
    "#6366F1", "#3B82F6", "#0EA5E9", "#14B8A6",
    "#10B981", "#84CC16", "#F59E0B", "#EF4444",
    "#EC4899", "#A855F7", "#8B5CF6", "#F97316",
]

# ── Spacing (8-pt grid) ───────────────────────────────────────────────────────
PAD_XS  = 4
PAD_SM  = 8
PAD_MD  = 16
PAD_LG  = 24
PAD_XL  = 32

# ── Border radius ─────────────────────────────────────────────────────────────
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14
RADIUS_XL = 16

# ── Shadow simulation (for border highlights) ─────────────────────────────────
SHADOW_SM = ("#E2E8F0", "#0D1117")
SHADOW_MD = ("#CBD5E1", "#0A0D14")

# ── Typography scale ──────────────────────────────────────────────────────────
FONT_FAMILY  = "Segoe UI"
FONT_XS      = 10
FONT_SM      = 11
FONT_MD      = 13
FONT_LG      = 15
FONT_XL      = 18
FONT_2XL     = 22
FONT_3XL     = 28
FONT_DISPLAY = 48


# ── Helpers ───────────────────────────────────────────────────────────────────
def attendance_color(percentage: float) -> str:
    if percentage >= 75:
        return ATTENDANCE_GOOD
    if percentage >= 60:
        return ATTENDANCE_WARNING
    return ATTENDANCE_CRITICAL


def gpa_color(gpa: float) -> str:
    if gpa >= 3.5:
        return SUCCESS[1]
    if gpa >= 2.5:
        return WARNING[1]
    return DANGER[1]


def priority_color(priority: str) -> str:
    return {
        "high":   PRIORITY_HIGH,
        "medium": PRIORITY_MEDIUM,
        "low":    PRIORITY_LOW,
    }.get(priority, PRIORITY_MEDIUM)


def subject_color(subject: dict, index: int = 0) -> str:
    """Return subject accent colour, falling back to palette by index."""
    return subject.get("color") or SUBJECT_COLORS[index % len(SUBJECT_COLORS)]


def make_font(size: int = FONT_MD, weight: str = "normal") -> dict:
    """Return a CTkFont kwarg dict."""
    import customtkinter as ctk
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)
