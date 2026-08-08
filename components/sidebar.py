"""
Sidebar Component — Premium redesign for StudyFlow.
Inspired by Notion, Linear, and Todoist sidebars.
"""

import customtkinter as ctk
from typing import Callable
from database import get_setting, set_setting, get_student_profile
from utils.theme import (
    BG_SIDEBAR, BG_HOVER, BG_CHIP, BG_CARD,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT, ACCENT_HOVER, BORDER,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    PAD_SM, PAD_MD, PAD_LG,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG,
)

# ── Nav definitions: (page_id, icon, label, section) ─────────────────────────
_NAV_SECTIONS = [
    {
        "label": "MAIN",
        "items": [
            ("dashboard",   "⊞",  "Dashboard"),
            ("subjects",    "⊟",  "Subjects"),
            ("assignments", "☑",  "Assignments"),
            ("attendance",  "◎",  "Attendance"),
        ]
    },
    {
        "label": "TOOLS",
        "items": [
            ("planner",     "▦",  "Planner"),
            ("timetable",   "▤",  "Timetable"),
            ("calendar",    "▦",  "Calendar"),
            ("pomodoro",    "◷",  "Focus Timer"),
        ]
    },
    {
        "label": "ACADEMIC",
        "items": [
            ("documents",   "≡",  "Documents"),
            ("cgpa",        "⊙",  "CGPA"),
        ]
    },
]

_BOTTOM_ITEMS = [
    ("settings", "⊕", "Settings"),
]


def _nav_font(size=FONT_MD) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size)


def _nav_bold(size=FONT_MD) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")


class Sidebar(ctk.CTkFrame):
    """Premium sidebar with grouped navigation, profile badge, and theme toggle."""

    def __init__(self, master, navigate_callback: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)

        self.navigate_callback = navigate_callback
        self.current_page = "dashboard"

        self.configure(
            width=240,
            corner_radius=0,
            fg_color=BG_SIDEBAR,
        )
        self.grid_propagate(False)
        self.pack_propagate(False)

        self._create_brand()
        self._create_nav()
        self._create_footer()

    # ── Brand ─────────────────────────────────────────────────────────────────
    def _create_brand(self):
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        # Logo mark
        logo = ctk.CTkFrame(
            brand,
            fg_color=ACCENT,
            corner_radius=RADIUS_MD,
            width=38, height=38,
        )
        logo.pack(side="left")
        logo.pack_propagate(False)
        ctk.CTkLabel(
            logo, text="S",
            font=_nav_bold(18),
            text_color=("#FFFFFF", "#FFFFFF"),
        ).place(relx=0.5, rely=0.5, anchor="center")

        # App name
        text_col = ctk.CTkFrame(brand, fg_color="transparent")
        text_col.pack(side="left", padx=(PAD_SM + 2, 0))

        ctk.CTkLabel(
            text_col, text="StudyFlow",
            font=_nav_bold(16),
            text_color=TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            text_col, text="Academic Workspace",
            font=_nav_font(FONT_XS),
            text_color=TEXT_SECONDARY, anchor="w",
        ).pack(anchor="w")

        # Thin divider below brand
        ctk.CTkFrame(self, fg_color=BORDER, height=1).pack(fill="x", padx=PAD_LG, pady=(PAD_SM, 0))

    # ── Navigation ────────────────────────────────────────────────────────────
    def _create_nav(self):
        self._nav_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=BG_HOVER,
            scrollbar_button_hover_color=ACCENT,
        )
        self._nav_scroll.pack(fill="both", expand=True, padx=PAD_SM, pady=(PAD_SM, 0))

        self.nav_buttons: dict[str, ctk.CTkButton] = {}

        for section in _NAV_SECTIONS:
            # Section label
            ctk.CTkLabel(
                self._nav_scroll,
                text=section["label"],
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_XS, weight="bold"),
                text_color=TEXT_MUTED, anchor="w",
            ).pack(fill="x", padx=PAD_MD, pady=(PAD_MD, PAD_XS if hasattr(self, '_PAD_XS') else 4))

            for page_id, icon, label in section["items"]:
                btn = self._make_nav_btn(page_id, icon, label)
                self.nav_buttons[page_id] = btn

        # Bottom nav items (settings) with divider
        ctk.CTkFrame(self._nav_scroll, fg_color=BORDER, height=1).pack(
            fill="x", padx=PAD_MD, pady=(PAD_MD, PAD_SM)
        )
        for page_id, icon, label in _BOTTOM_ITEMS:
            btn = self._make_nav_btn(page_id, icon, label)
            self.nav_buttons[page_id] = btn

        self._set_active_page("dashboard")

    def _make_nav_btn(self, page_id: str, icon: str, label: str) -> ctk.CTkButton:
        btn = ctk.CTkButton(
            self._nav_scroll,
            text=f" {icon}   {label}",
            font=_nav_font(FONT_MD),
            anchor="w",
            height=40,
            corner_radius=RADIUS_SM,
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            hover_color=BG_HOVER,
            command=lambda p=page_id: self._navigate_to(p),
        )
        btn.pack(fill="x", pady=2, padx=PAD_SM)
        return btn

    # ── Footer ────────────────────────────────────────────────────────────────
    def _create_footer(self):
        ctk.CTkFrame(self, fg_color=BORDER, height=1).pack(fill="x", padx=PAD_LG, pady=(0, PAD_SM))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=PAD_MD, pady=(0, PAD_LG))

        # Profile card
        self.profile_card = ctk.CTkFrame(
            footer,
            fg_color=BG_CHIP,
            corner_radius=RADIUS_MD,
        )
        self.profile_card.pack(fill="x", pady=(0, PAD_SM))
        self.profile_card.bind("<Button-1>", lambda e: self._navigate_to("settings"))

        # Avatar circle
        avatar_frame = ctk.CTkFrame(
            self.profile_card,
            fg_color=ACCENT,
            corner_radius=18,
            width=36, height=36,
        )
        avatar_frame.pack(side="left", padx=(PAD_SM, 0), pady=PAD_SM)
        avatar_frame.pack_propagate(False)
        self.avatar_lbl = ctk.CTkLabel(
            avatar_frame, text="S",
            font=_nav_bold(14),
            text_color=("#FFFFFF", "#FFFFFF"),
        )
        self.avatar_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Name + dept
        info = ctk.CTkFrame(self.profile_card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(PAD_SM, 0), pady=PAD_SM)

        self.profile_name_lbl = ctk.CTkLabel(
            info, text="Student",
            font=_nav_bold(FONT_SM),
            text_color=TEXT_PRIMARY, anchor="w",
        )
        self.profile_name_lbl.pack(anchor="w")

        self.profile_dept_lbl = ctk.CTkLabel(
            info, text="Set up profile →",
            font=_nav_font(FONT_XS),
            text_color=TEXT_MUTED, anchor="w",
        )
        self.profile_dept_lbl.pack(anchor="w")

        # Settings/chevron button
        ctk.CTkLabel(
            self.profile_card, text="›",
            font=_nav_bold(FONT_LG),
            text_color=TEXT_MUTED, width=24,
        ).pack(side="right", padx=PAD_SM)

        self._refresh_profile()

        # Theme toggle row
        theme_row = ctk.CTkFrame(footer, fg_color="transparent")
        theme_row.pack(fill="x", pady=(PAD_SM, 0))

        ctk.CTkLabel(
            theme_row, text="☽  Dark Mode",
            font=_nav_font(FONT_SM),
            text_color=TEXT_SECONDARY,
        ).pack(side="left")

        self.theme_switch = ctk.CTkSwitch(
            theme_row, text="",
            width=44, height=22,
            fg_color=BORDER,
            progress_color=ACCENT,
            button_color=BG_SIDEBAR,
            button_hover_color=ACCENT_HOVER,
            command=self._toggle_theme,
        )
        theme_mode = get_setting("theme_mode")
        if theme_mode == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()
        self.theme_switch.pack(side="right")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _refresh_profile(self):
        try:
            profile = get_student_profile()
            if profile and profile.get("name"):
                name = profile["name"]
                first = name.split()[0] if name.split() else name
                self.profile_name_lbl.configure(text=name[:22])
                self.avatar_lbl.configure(text=first[0].upper())

                dept = profile.get("department", "")
                sem = profile.get("semester", "")
                subtitle = dept or ""
                if sem:
                    subtitle += f"  •  Sem {sem}" if subtitle else f"Sem {sem}"
                if subtitle:
                    self.profile_dept_lbl.configure(text=subtitle[:28])
                else:
                    self.profile_dept_lbl.configure(text="Set up profile →")
        except Exception:
            pass

    def _navigate_to(self, page_id: str):
        self._set_active_page(page_id)
        self.navigate_callback(page_id)

    def _set_active_page(self, page_id: str):
        self.current_page = page_id
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == page_id:
                btn.configure(
                    fg_color=ACCENT,
                    text_color=("#FFFFFF", "#FFFFFF"),
                    hover_color=ACCENT_HOVER,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_MD, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY,
                    hover_color=BG_HOVER,
                    font=_nav_font(FONT_MD),
                )

    def _toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
            set_setting("theme_mode", "dark")
        else:
            ctk.set_appearance_mode("light")
            set_setting("theme_mode", "light")
        self._refresh_profile()
