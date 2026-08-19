"""
StudyFlow Design System — v3
Inspired by Notion, Linear, Todoist, and Microsoft Fluent.

CustomTkinter widgets accept (light_color, dark_color) tuples.
When ctk.set_appearance_mode() changes every widget auto-repaints.

Light mode overhaul: clear visual hierarchy with distinct surface layers.
  #F0F4F8 → window bg
  #FFFFFF  → primary surface / cards
  #F1F5F9  → secondary surface / input bg
  #E8EDF3  → chip / tag / inactive pill bg
  #E2E8F0  → borders

Spacing system: 4 / 8 / 16 / 24 / 32 px grid.
Radius system : 6 / 10 / 14 / 16 px.
"""

# ── Background Hierarchy ─────────────────────────────────────────────────────
BG_MAIN    = ("#F0F4F8", "#0F1117")         # outermost window — light blue-grey
BG_SURFACE = ("#FFFFFF", "#1A1D27")         # cards, panels — pure white on light
BG_SIDEBAR = ("#FFFFFF", "#13161F")         # sidebar — white with visible border
BG_HEADER  = ("#FFFFFF", "#161921")         # top bar
BG_INPUT   = ("#F1F5F9", "#1E2130")         # entry / search fields — visible inset
BG_HOVER   = ("#EFF6FF", "#1E2740")         # hover highlight
BG_CHIP    = ("#E8EDF3", "#1E2535")         # chips / tags — clearly distinct from white
BG_CARD    = ("#FFFFFF", "#1E2130")         # raised cards
BG_ROW     = ("#F8FAFC", "#181B26")         # alternating table rows
BG_OVERLAY = ("#F1F5F9", "#161A24")         # subtle overlay
BG_ACTIVE  = ("#EFF6FF", "#1E2F50")         # active nav item bg

# ── Text ─────────────────────────────────────────────────────────────────────
TEXT_PRIMARY   = ("#0F172A", "#F1F5F9")     # stronger dark ink for light mode
TEXT_SECONDARY = ("#475569", "#94A3B8")     # improved contrast on white
TEXT_MUTED     = ("#64748B", "#475569")     # still readable
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
BORDER         = ("#CBD5E1", "#1E2535")     # stronger border in light mode
BORDER_FOCUS   = ("#2563EB", "#3B82F6")
BORDER_STRONG  = ("#94A3B8", "#2D3554")     # even stronger for key separators

# ── Priority badge colors ─────────────────────────────────────────────────────
PRIORITY_HIGH   = "#DC2626"
PRIORITY_MEDIUM = "#D97706"
PRIORITY_LOW    = "#16A34A"

# ── Attendance status colors ──────────────────────────────────────────────────
ATTENDANCE_GOOD     = "#16A34A"
ATTENDANCE_WARNING  = "#D97706"
ATTENDANCE_CRITICAL = "#DC2626"

# ── Subject accent palette ────────────────────────────────────────────────────
SUBJECT_COLORS = [
    "#6366F1", "#2563EB", "#0284C7", "#0D9488",
    "#16A34A", "#65A30D", "#D97706", "#DC2626",
    "#DB2777", "#9333EA", "#7C3AED", "#EA580C",
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

# ── Shadow simulation ─────────────────────────────────────────────────────────
SHADOW_SM = ("#CBD5E1", "#0D1117")
SHADOW_MD = ("#94A3B8", "#0A0D14")

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
        return SUCCESS[0]
    if gpa >= 2.5:
        return WARNING[0]
    return DANGER[0]


def priority_color(priority: str) -> str:
    return {
        "high":   PRIORITY_HIGH,
        "medium": PRIORITY_MEDIUM,
        "low":    PRIORITY_LOW,
    }.get(priority, PRIORITY_MEDIUM)


def subject_color(subject: dict, index: int = 0) -> str:
    """Return subject accent colour, falling back to palette by index."""
    return subject.get("color") or SUBJECT_COLORS[index % len(SUBJECT_COLORS)]


