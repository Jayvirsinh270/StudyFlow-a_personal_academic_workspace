"""
Dashboard Module — Premium redesign for StudyFlow.
Inspired by Notion, Linear, and Todoist dashboards.
"""

import json
import customtkinter as ctk
from datetime import datetime, date
from database import (
    get_timetable, get_subjects, get_student_profile,
    get_attendance, calculate_attendance_percentage,
    get_assignments, get_notes, get_setting, set_setting,
    get_cgpa_records, calculate_cgpa,
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_CHIP, BG_HOVER, BG_INPUT, BG_OVERLAY,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT, ACCENT_HOVER, ACCENT_LIGHT,
    SUCCESS, WARNING, DANGER,
    BORDER, PAD_XS, PAD_SM, PAD_MD, PAD_LG, PAD_XL,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL, FONT_2XL, FONT_3XL,
    attendance_color, priority_color,
)


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


def _font(size=FONT_MD, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def _bold(size=FONT_MD) -> ctk.CTkFont:
    return _font(size, "bold")


def _greeting() -> str:
    h = datetime.now().hour
    if h < 12:
        return "Good morning"
    if h < 17:
        return "Good afternoon"
    return "Good evening"


# ── Reusable section builder ───────────────────────────────────────────────────

def _card(parent, title: str = "", icon: str = "",
          action_text: str = "", action_cmd=None,
          pady=(PAD_MD, PAD_SM)) -> ctk.CTkFrame:
    card = ctk.CTkFrame(parent, fg_color=BG_SURFACE,
                        corner_radius=RADIUS_LG, border_width=1, border_color=BORDER)
    card.pack(fill="x", pady=pady)

    if title:
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, 0))

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left")
        if icon:
            ctk.CTkLabel(left, text=icon, font=_font(FONT_LG),
                         text_color=ACCENT[1]).pack(side="left", padx=(0, PAD_SM))
        ctk.CTkLabel(left, text=title, font=_bold(FONT_LG),
                     text_color=TEXT_PRIMARY).pack(side="left")

        if action_text and action_cmd:
            ctk.CTkButton(
                hdr, text=action_text, height=28, width=100,
                corner_radius=RADIUS_SM,
                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                text_color=("#FFFFFF", "#FFFFFF"),
                font=_bold(FONT_SM),
                command=action_cmd,
            ).pack(side="right")

        ctk.CTkFrame(card, fg_color=BORDER, height=1).pack(fill="x", padx=PAD_LG, pady=(PAD_SM, 0))

    return card


def _row_item(parent, title: str, subtitle: str, right_text: str,
              right_color: str = None, dot_color: str = None, icon: str = "") -> ctk.CTkFrame:
    row = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=RADIUS_SM)
    row.pack(fill="x", pady=3)

    if dot_color:
        ctk.CTkFrame(row, fg_color=dot_color, width=4, corner_radius=0).pack(side="left", fill="y")

    if icon:
        ctk.CTkLabel(row, text=icon, font=_font(FONT_MD),
                     text_color=ACCENT[1], width=30).pack(side="left", padx=(PAD_SM, 0))

    info = ctk.CTkFrame(row, fg_color="transparent")
    info.pack(side="left", fill="both", expand=True, padx=PAD_MD, pady=PAD_SM)

    if subtitle:
        ctk.CTkLabel(info, text=subtitle, font=_font(FONT_XS),
                     text_color=TEXT_MUTED, anchor="w").pack(anchor="w")
    ctk.CTkLabel(info, text=title, font=_bold(FONT_MD),
                 text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")

    if right_text:
        ctk.CTkLabel(row, text=right_text, font=_bold(FONT_SM),
                     text_color=right_color or TEXT_SECONDARY).pack(side="right", padx=PAD_MD)

    # Hover
    row.bind("<Enter>", lambda e: row.configure(fg_color=BG_HOVER))
    row.bind("<Leave>", lambda e: row.configure(fg_color=BG_CARD))
    return row


class Dashboard(ctk.CTkFrame):
    """Premium dashboard: stats, timetable, assignments, notes, streak."""

    def __init__(self, master, navigate_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.navigate_callback = navigate_callback
        self.configure(fg_color="transparent")

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=BG_CHIP,
            scrollbar_button_hover_color=ACCENT,
        )
        self._scroll.pack(fill="both", expand=True)

        self._create_layout()
        self._load_all()

    # ── Static skeleton ────────────────────────────────────────────────────────
    def _create_layout(self):
        s = self._scroll

        # ── Welcome banner ────────────────────────────────────────────────────
        self._welcome_card = ctk.CTkFrame(s, fg_color=ACCENT, corner_radius=RADIUS_XL)
        self._welcome_card.pack(fill="x", pady=(0, PAD_LG))

        banner = ctk.CTkFrame(self._welcome_card, fg_color="transparent")
        banner.pack(fill="x", padx=PAD_XL, pady=PAD_LG)

        left_banner = ctk.CTkFrame(banner, fg_color="transparent")
        left_banner.pack(side="left", fill="both", expand=True)

        self._welcome_lbl = ctk.CTkLabel(
            left_banner, text=f"{_greeting()}!",
            font=_bold(FONT_3XL),
            text_color=("#FFFFFF", "#FFFFFF"), anchor="w",
        )
        self._welcome_lbl.pack(anchor="w")

        self._subtitle_lbl = ctk.CTkLabel(
            left_banner, text="Your personal academic workspace",
            font=_font(FONT_MD),
            text_color=("#DBEAFE", "#DBEAFE"), anchor="w",
        )
        self._subtitle_lbl.pack(anchor="w", pady=(PAD_XS, 0))

        # Right: date badge
        right_banner = ctk.CTkFrame(banner, fg_color="transparent")
        right_banner.pack(side="right", anchor="ne")

        ctk.CTkLabel(
            right_banner,
            text=datetime.now().strftime("%A"),
            font=_bold(FONT_LG),
            text_color=("#DBEAFE", "#DBEAFE"), anchor="e",
        ).pack(anchor="e")
        ctk.CTkLabel(
            right_banner,
            text=datetime.now().strftime("%B %d, %Y"),
            font=_font(FONT_SM),
            text_color=("#DBEAFE", "#DBEAFE"), anchor="e",
        ).pack(anchor="e")

        # ── Reminders banner (hidden until needed) ────────────────────────────
        self._reminders_card = ctk.CTkFrame(
            s, fg_color=("#FEF3C7", "#451A03"), corner_radius=RADIUS_SM,
            border_width=1, border_color=WARNING,
        )
        self._reminders_inner = ctk.CTkFrame(self._reminders_card, fg_color="transparent")
        self._reminders_inner.pack(fill="x", padx=PAD_MD, pady=PAD_SM)

        # ── 4-stat grid ───────────────────────────────────────────────────────
        stat_row = ctk.CTkFrame(s, fg_color="transparent")
        stat_row.pack(fill="x", pady=(0, PAD_LG))
        for i in range(4):
            stat_row.grid_columnconfigure(i, weight=1)

        self._stat_cards: list[dict] = []
        specs = [
            ("Attendance",   "◎",  "#22C55E",   "Overall avg"),
            ("CGPA",         "⊙",  ACCENT[1],   "Cumulative"),
            ("Assignments",  "☑",  WARNING[1],  "Pending"),
            ("Subjects",     "⊟",  "#A855F7",   "This semester"),
        ]
        for col, (label, icon, color, sub) in enumerate(specs):
            card = ctk.CTkFrame(
                stat_row, fg_color=BG_SURFACE,
                corner_radius=RADIUS_LG, border_width=1, border_color=BORDER,
            )
            gap = (0, PAD_SM if col < 3 else 0)
            card.grid(row=0, column=col, padx=gap, sticky="nsew")

            # Icon circle
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=PAD_MD, pady=(PAD_MD, PAD_XS))

            icon_frame = ctk.CTkFrame(
                top, fg_color=BG_CHIP,
                corner_radius=RADIUS_SM, width=40, height=40,
            )
            icon_frame.pack(side="left")
            icon_frame.pack_propagate(False)
            ctk.CTkLabel(
                icon_frame, text=icon,
                font=_font(FONT_LG), text_color=color,
            ).place(relx=0.5, rely=0.5, anchor="center")

            val_lbl = ctk.CTkLabel(
                top, text="—",
                font=_bold(FONT_2XL), text_color=color,
            )
            val_lbl.pack(side="right")

            ctk.CTkLabel(
                card, text=label,
                font=_bold(FONT_SM), text_color=TEXT_PRIMARY,
            ).pack(anchor="w", padx=PAD_MD)
            ctk.CTkLabel(
                card, text=sub,
                font=_font(FONT_XS), text_color=TEXT_MUTED,
            ).pack(anchor="w", padx=PAD_MD, pady=(0, PAD_MD))

            self._stat_cards.append({"val": val_lbl, "color": color})

        # ── Quick Actions ─────────────────────────────────────────────────────
        self._actions_card = _card(s, "Quick Actions", icon="⊞")
        qa_grid = ctk.CTkFrame(self._actions_card, fg_color="transparent")
        qa_grid.pack(fill="x", padx=PAD_LG, pady=PAD_MD)
        for i in range(4):
            qa_grid.grid_columnconfigure(i, weight=1)

        qa_items = [
            ("Add Subject",   "⊟", "#6366F1", "subjects"),
            ("Assignment",    "☑", WARNING[1], "assignments"),
            ("Open Planner",  "▦", ACCENT[1],  "planner"),
            ("Focus Timer",   "◷", "#22C55E",  "pomodoro"),
        ]
        for i, (lbl, icon, color, page) in enumerate(qa_items):
            frame = ctk.CTkFrame(
                qa_grid, fg_color=BG_CARD,
                corner_radius=RADIUS_LG, border_width=1, border_color=BORDER,
                cursor="hand2",
            )
            gap = (0, PAD_SM if i < 3 else 0)
            frame.grid(row=0, column=i, padx=gap, sticky="nsew")

            inner = ctk.CTkFrame(frame, fg_color="transparent")
            inner.pack(padx=PAD_MD, pady=PAD_MD)

            icon_bg = ctk.CTkFrame(
                inner, fg_color=BG_CHIP,
                corner_radius=RADIUS_SM, width=44, height=44,
            )
            icon_bg.pack()
            icon_bg.pack_propagate(False)
            ctk.CTkLabel(
                icon_bg, text=icon,
                font=_font(FONT_XL), text_color=color,
            ).place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(
                inner, text=lbl,
                font=_bold(FONT_SM), text_color=TEXT_PRIMARY,
                wraplength=90, justify="center",
            ).pack(pady=(PAD_SM, 0))

            def _bind_hover(f, c):
                f.bind("<Enter>", lambda e, fr=f, cl=c: fr.configure(
                    fg_color=BG_HOVER, border_color=cl))
                f.bind("<Leave>", lambda e, fr=f: fr.configure(
                    fg_color=BG_CARD, border_color=BORDER))
                f.bind("<Button-1>", lambda e, pg=page: self._navigate(pg))
                for child in f.winfo_children():
                    child.bind("<Button-1>", lambda e, pg=page: self._navigate(pg))
            _bind_hover(frame, color)

        # ── Today's Schedule ──────────────────────────────────────────────────
        self._tt_card = _card(
            s, "Today's Schedule", icon="▦",
            action_text="Timetable", action_cmd=lambda: None,  # set after
        )
        self._tt_content = ctk.CTkFrame(self._tt_card, fg_color="transparent")
        self._tt_content.pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_MD))

        # ── Attendance Summary ────────────────────────────────────────────────
        self._att_card = _card(
            s, "Attendance Overview", icon="◎",
            action_text="View All", action_cmd=lambda: None,
        )
        self._att_content = ctk.CTkFrame(self._att_card, fg_color="transparent")
        self._att_content.pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_MD))

        # ── Upcoming Assignments ──────────────────────────────────────────────
        self._asgn_card = _card(
            s, "Upcoming Assignments", icon="☑",
            action_text="View All", action_cmd=lambda: None,
        )
        self._asgn_content = ctk.CTkFrame(self._asgn_card, fg_color="transparent")
        self._asgn_content.pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_MD))

        # ── Recent Notes ──────────────────────────────────────────────────────
        self._notes_card = _card(
            s, "Recent Notes", icon="≡",
            action_text="Open", action_cmd=lambda: None,
        )
        self._notes_content = ctk.CTkFrame(self._notes_card, fg_color="transparent")
        self._notes_content.pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_MD))

        # ── Study Streak ──────────────────────────────────────────────────────
        self._streak_card = _card(s, "Study Streak", icon="⚡")
        self._streak_content = ctk.CTkFrame(self._streak_card, fg_color="transparent")
        self._streak_content.pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_MD))

        # ── Charts row ────────────────────────────────────────────────────────
        charts_row = ctk.CTkFrame(s, fg_color="transparent")
        charts_row.pack(fill="x", pady=(0, PAD_LG))
        charts_row.grid_columnconfigure(0, weight=1)
        charts_row.grid_columnconfigure(1, weight=1)

        # Attendance chart card
        self._att_chart_card = ctk.CTkFrame(
            charts_row, fg_color=BG_SURFACE,
            corner_radius=RADIUS_LG, border_width=1, border_color=BORDER,
        )
        self._att_chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))
        ctk.CTkLabel(
            self._att_chart_card, text="◎  Attendance by Subject",
            font=_bold(FONT_LG), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_MD, 0))
        ctk.CTkFrame(self._att_chart_card, fg_color=BORDER, height=1).pack(fill="x", padx=PAD_LG, pady=(PAD_SM, 0))
        self._att_chart_container = ctk.CTkFrame(self._att_chart_card, fg_color="transparent")
        self._att_chart_container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)

        # CGPA chart card
        self._cgpa_chart_card = ctk.CTkFrame(
            charts_row, fg_color=BG_SURFACE,
            corner_radius=RADIUS_LG, border_width=1, border_color=BORDER,
        )
        self._cgpa_chart_card.grid(row=0, column=1, sticky="nsew", padx=(PAD_SM, 0))
        ctk.CTkLabel(
            self._cgpa_chart_card, text="⊙  GPA Progress",
            font=_bold(FONT_LG), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_MD, 0))
        ctk.CTkFrame(self._cgpa_chart_card, fg_color=BORDER, height=1).pack(fill="x", padx=PAD_LG, pady=(PAD_SM, 0))
        self._cgpa_chart_container = ctk.CTkFrame(self._cgpa_chart_card, fg_color="transparent")
        self._cgpa_chart_container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)

    # ── Load all data ─────────────────────────────────────────────────────────
    def _load_all(self):
        self._load_profile()
        self._load_stats()
        self._load_reminders()
        self._load_timetable()
        self._load_attendance()
        self._load_assignments()
        self._load_notes()
        self._load_streak()
        self._load_charts()

        # Wire up action buttons properly after navigate_callback is available
        for child in self._tt_card.winfo_children():
            pass  # already wired on creation

        # Visibility toggles
        if not _bool_setting(get_setting("show_quick_actions"), True):
            self._actions_card.pack_forget()
        if not _bool_setting(get_setting("show_reminders"), True):
            self._reminders_card.pack_forget()

    def _load_profile(self):
        profile = get_student_profile()
        if profile and profile.get("name"):
            first = profile["name"].split()[0]
            self._welcome_lbl.configure(text=f"{_greeting()}, {first}! 👋")
            self._subtitle_lbl.configure(text="Here's your academic overview for today")
        else:
            self._welcome_lbl.configure(text=f"{_greeting()}!")
            self._subtitle_lbl.configure(text="Set up your profile and start organizing your semester")

    def _load_stats(self):
        subjects = get_subjects()
        assignments = get_assignments()
        pending = [a for a in assignments if a.get("status") == "pending"]
        cgpa = calculate_cgpa() or 0.0

        pcts = [calculate_attendance_percentage(s["id"]) for s in subjects if get_attendance(s["id"])]
        avg_att = (sum(pcts) / len(pcts)) if pcts else 0

        values = [f"{avg_att:.0f}%", f"{cgpa:.2f}", str(len(pending)), str(len(subjects))]
        for card, val in zip(self._stat_cards, values):
            card["val"].configure(text=val)

    def _load_reminders(self):
        for w in self._reminders_inner.winfo_children():
            w.destroy()

        reminders = []
        today = date.today()
        for a in get_assignments():
            if a.get("status") != "completed" and a.get("due_date"):
                try:
                    due = datetime.strptime(a["due_date"], "%Y-%m-%d").date()
                    delta = (due - today).days
                    if delta <= 3:
                        urgency = "Due today!" if delta == 0 else (
                            f"Due in {delta}d" if delta > 0 else "Overdue!"
                        )
                        reminders.append(f"☑ {a['title']}: {urgency}")
                except Exception:
                    pass

        for s in get_subjects():
            try:
                pct = calculate_attendance_percentage(s["id"])
                if pct < 75:
                    reminders.append(f"⚠ {s['name']}: {pct:.0f}%")
            except Exception:
                pass

        if not reminders:
            self._reminders_card.pack_forget()
            return

        self._reminders_card.pack(fill="x", pady=(0, PAD_MD))
        ctk.CTkLabel(
            self._reminders_inner,
            text="⚠  " + ("  •  ".join(reminders[:3]) + (" …" if len(reminders) > 3 else "")),
            font=_bold(FONT_SM),
            text_color=("#92400E", "#FDE68A"), anchor="w",
            wraplength=900,
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            self._reminders_inner, text="View All", height=26, width=80,
            corner_radius=RADIUS_SM,
            fg_color=WARNING, hover_color=ACCENT,
            text_color=("#FFFFFF", "#FFFFFF"),
            font=_bold(FONT_SM),
            command=lambda: self._navigate("assignments"),
        ).pack(side="right")

    def _load_timetable(self):
        for w in self._tt_content.winfo_children():
            w.destroy()

        today = datetime.now().strftime("%A")
        entries = [e for e in get_timetable() if e.get("day") == today]
        subj_map = {s["id"]: s for s in get_subjects()}

        if not entries:
            empty = ctk.CTkFrame(self._tt_content, fg_color="transparent")
            empty.pack(pady=PAD_LG)
            ctk.CTkLabel(
                empty, text="▦", font=_font(28), text_color=TEXT_MUTED,
            ).pack()
            ctk.CTkLabel(
                empty, text=f"No classes scheduled for {today}",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=(PAD_SM, 0))
            return

        time_order = ["8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00",
                      "12:00-1:00","1:00-2:00","2:00-3:00","3:00-4:00","4:00-5:00"]
        entries.sort(key=lambda x: time_order.index(x.get("time_slot",""))
                     if x.get("time_slot") in time_order else 99)

        for entry in entries:
            subj = subj_map.get(entry.get("subject_id"), {})
            color = subj.get("color") or ACCENT[1]
            _row_item(
                self._tt_content,
                title=subj.get("name", "Unknown Subject"),
                subtitle=entry.get("time_slot", ""),
                right_text=f"📍 {entry.get('classroom', entry.get('room', 'TBD'))}",
                right_color=TEXT_SECONDARY,
                dot_color=color,
            )

    def _load_attendance(self):
        for w in self._att_content.winfo_children():
            w.destroy()

        subjects = get_subjects()
        if not subjects:
            ctk.CTkLabel(
                self._att_content,
                text="No subjects yet. Add subjects to track attendance.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=PAD_LG)
            return

        has_data = False
        for s in subjects:
            att = get_attendance(s["id"])
            if not att:
                continue
            has_data = True
            pct = calculate_attendance_percentage(s["id"])
            color = attendance_color(pct)
            row = ctk.CTkFrame(self._att_content, fg_color=BG_CARD, corner_radius=RADIUS_SM)
            row.pack(fill="x", pady=3)

            ctk.CTkFrame(row, fg_color=color, width=4, corner_radius=0).pack(side="left", fill="y")

            name_lbl = ctk.CTkLabel(
                row, text=s["name"],
                font=_bold(FONT_MD), text_color=TEXT_PRIMARY, anchor="w", width=180,
            )
            name_lbl.pack(side="left", padx=PAD_MD, pady=PAD_SM)

            bar = ctk.CTkProgressBar(row, height=8, corner_radius=4, progress_color=color)
            bar.set(pct / 100)
            bar.pack(side="left", fill="x", expand=True, padx=(0, PAD_MD), pady=PAD_SM)

            ctk.CTkLabel(
                row, text=f"{pct:.1f}%",
                font=_bold(FONT_MD), text_color=color, width=52,
            ).pack(side="right", padx=PAD_MD)

            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=BG_HOVER))
            row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=BG_CARD))

        if not has_data:
            ctk.CTkLabel(
                self._att_content,
                text="No attendance recorded yet.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=PAD_LG)

    def _load_assignments(self):
        for w in self._asgn_content.winfo_children():
            w.destroy()

        today = date.today()
        pending = []
        subj_map = {s["id"]: s for s in get_subjects()}

        for a in get_assignments():
            if a.get("status") == "pending" and a.get("due_date"):
                try:
                    due = datetime.strptime(a["due_date"], "%Y-%m-%d").date()
                    if due >= today:
                        pending.append((a, due))
                except Exception:
                    pass

        pending.sort(key=lambda x: x[1])

        if not pending:
            ctk.CTkLabel(
                self._asgn_content,
                text="✓  No upcoming assignments — great job!",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=PAD_LG)
            return

        for a, due in pending[:5]:
            delta = (due - today).days
            if delta == 0:
                days_txt, days_color = "Due today", DANGER[1]
            elif delta == 1:
                days_txt, days_color = "Tomorrow", WARNING[1]
            elif delta <= 7:
                days_txt, days_color = f"{delta} days", WARNING[1]
            else:
                days_txt, days_color = f"{delta} days", TEXT_MUTED[1]

            subj = subj_map.get(a.get("subject_id"), {})
            dot = subj.get("color") or priority_color(a.get("priority", "medium"))
            _row_item(
                self._asgn_content,
                title=a.get("title", "Untitled"),
                subtitle=subj.get("name", "Unknown Subject"),
                right_text=days_txt,
                right_color=days_color,
                dot_color=dot,
            )

    def _load_notes(self):
        for w in self._notes_content.winfo_children():
            w.destroy()

        subjects = get_subjects()
        all_notes = []
        for s in subjects:
            for n in get_notes(s["id"]):
                all_notes.append((n, s))

        if not all_notes:
            ctk.CTkLabel(
                self._notes_content,
                text="No notes yet. Start writing in a subject workspace.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=PAD_LG)
            return

        all_notes.sort(key=lambda x: x[0].get("updated_at", ""), reverse=True)

        for note, subj in all_notes[:5]:
            try:
                dt = datetime.strptime(note.get("updated_at", ""), "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%b %d, %I:%M %p")
            except Exception:
                date_str = ""

            _row_item(
                self._notes_content,
                title=note.get("title", "Untitled"),
                subtitle=subj["name"],
                right_text=date_str,
                right_color=TEXT_MUTED,
                icon="≡",
            )

    def _load_streak(self):
        for w in self._streak_content.winfo_children():
            w.destroy()

        raw = get_setting("study_streak")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = {}
        if not isinstance(raw, dict):
            raw = {}

        today_str = date.today().isoformat()
        current = raw.get("current_streak", 0)
        longest = raw.get("longest_streak", 0)
        last = raw.get("last_study_date")

        has_activity = self._check_today_activity()
        if has_activity and last != today_str:
            if last:
                try:
                    gap = (date.today() - date.fromisoformat(last)).days
                    current = current + 1 if gap == 1 else 1
                except Exception:
                    current = 1
            else:
                current = 1
            longest = max(longest, current)
            set_setting("study_streak", {
                "current_streak": current, "last_study_date": today_str, "longest_streak": longest
            })
        elif last:
            try:
                if (date.today() - date.fromisoformat(last)).days > 1:
                    current = 0
                    set_setting("study_streak", {
                        "current_streak": 0, "last_study_date": last, "longest_streak": longest
                    })
            except Exception:
                pass

        # Streak row
        row = ctk.CTkFrame(self._streak_content, fg_color=BG_CARD, corner_radius=RADIUS_LG)
        row.pack(fill="x")

        # Flame icon
        flame_frame = ctk.CTkFrame(
            row, fg_color=("#FFF7ED", "#451A03"),
            corner_radius=RADIUS_MD, width=60, height=60,
        )
        flame_frame.pack(side="left", padx=PAD_LG, pady=PAD_MD)
        flame_frame.pack_propagate(False)
        ctk.CTkLabel(
            flame_frame, text="🔥", font=_font(28),
        ).place(relx=0.5, rely=0.5, anchor="center")

        mid = ctk.CTkFrame(row, fg_color="transparent")
        mid.pack(side="left", fill="both", expand=True, pady=PAD_MD)

        ctk.CTkLabel(
            mid, text=f"{current} Day{'s' if current != 1 else ''}",
            font=_bold(FONT_2XL), text_color="#F97316", anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            mid,
            text="Current study streak" if current > 0 else "Start studying to build your streak!",
            font=_font(FONT_SM), text_color=TEXT_MUTED, anchor="w",
        ).pack(anchor="w")

        # Best streak
        right_streak = ctk.CTkFrame(row, fg_color=BG_CHIP, corner_radius=RADIUS_MD)
        right_streak.pack(side="right", padx=PAD_LG, pady=PAD_MD)

        ctk.CTkLabel(
            right_streak, text="BEST",
            font=_bold(FONT_XS), text_color=TEXT_MUTED,
        ).pack(padx=PAD_MD, pady=(PAD_SM, 0))
        ctk.CTkLabel(
            right_streak, text=str(longest),
            font=_bold(FONT_2XL), text_color=SUCCESS[1],
        ).pack(padx=PAD_MD)
        ctk.CTkLabel(
            right_streak, text="days",
            font=_font(FONT_XS), text_color=TEXT_MUTED,
        ).pack(padx=PAD_MD, pady=(0, PAD_SM))

    def _check_today_activity(self) -> bool:
        today = date.today()
        for s in get_subjects():
            for n in get_notes(s["id"]):
                try:
                    if datetime.strptime(n.get("updated_at", ""), "%Y-%m-%d %H:%M:%S").date() == today:
                        return True
                except Exception:
                    pass
            att = get_attendance(s["id"])
            if att:
                try:
                    if datetime.strptime(att.get("updated_at", ""), "%Y-%m-%d %H:%M:%S").date() == today:
                        return True
                except Exception:
                    pass
        for a in get_assignments():
            try:
                if datetime.strptime(a.get("created_at", ""), "%Y-%m-%d %H:%M:%S").date() == today:
                    return True
            except Exception:
                pass
        return False

    def _load_charts(self):
        """Render attendance bar chart and GPA line chart on the dashboard."""
        self._render_attendance_chart()
        self._render_cgpa_chart()

    def _render_attendance_chart(self):
        for w in self._att_chart_container.winfo_children():
            w.destroy()

        subjects = get_subjects()
        data = [(s["name"][:10], calculate_attendance_percentage(s["id"]))
                for s in subjects if get_attendance(s["id"])]

        if not data:
            ctk.CTkLabel(
                self._att_chart_container,
                text="No attendance data yet.\nStart marking attendance.",
                font=_font(FONT_SM), text_color=TEXT_MUTED,
                justify="center",
            ).pack(pady=30)
            return

        names  = [d[0] for d in data]
        pcts   = [d[1] for d in data]
        colors = ["#22C55E" if p >= 75 else "#F59E0B" if p >= 60 else "#EF4444" for p in pcts]

        import customtkinter as _ctk
        mode = _ctk.get_appearance_mode().lower()
        bg = "#1F2533" if mode == "dark" else "#F8FAFC"
        text_col = "#8899B4" if mode == "dark" else "#64748B"
        grid_col = "#283040" if mode == "dark" else "#E2E8F0"

        fig, ax = plt.subplots(figsize=(5, 2.8), dpi=90)
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)

        bars = ax.bar(names, pcts, color=colors, width=0.55, zorder=3)
        ax.axhline(y=75, color="#F59E0B", linestyle="--", alpha=0.7, linewidth=1, label="75% min")
        ax.set_ylim(0, 110)
        ax.set_ylabel("%", color=text_col, fontsize=8)
        ax.tick_params(axis="x", colors=text_col, labelsize=7, rotation=20)
        ax.tick_params(axis="y", colors=text_col, labelsize=7)
        for spine in ax.spines.values():
            spine.set_color(grid_col)
        ax.grid(axis="y", alpha=0.2, color=grid_col, zorder=0)
        ax.legend(loc="upper right", fontsize=7,
                  facecolor="#252E3E" if mode == "dark" else "#FFFFFF",
                  edgecolor=grid_col)
        for bar, pct in zip(bars, pcts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{pct:.0f}%", ha="center", va="bottom",
                    color=text_col, fontsize=6)

        fig.tight_layout(pad=0.5)
        canvas = FigureCanvasTkAgg(fig, master=self._att_chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    def _render_cgpa_chart(self):
        for w in self._cgpa_chart_container.winfo_children():
            w.destroy()

        records = get_cgpa_records()
        if not records:
            ctk.CTkLabel(
                self._cgpa_chart_container,
                text="Add semester records in\nCGPA Calculator to see your GPA trend.",
                font=_font(FONT_SM), text_color=TEXT_MUTED,
                justify="center",
            ).pack(pady=30)
            return

        records.sort(key=lambda x: x.get("semester", 0))
        sems = [f"S{r['semester']}" for r in records]
        gpas = [r.get("gpa", 0) for r in records]

        import customtkinter as _ctk
        mode = _ctk.get_appearance_mode().lower()
        bg       = "#1F2533" if mode == "dark" else "#F8FAFC"
        text_col = "#8899B4" if mode == "dark" else "#64748B"
        grid_col = "#283040" if mode == "dark" else "#E2E8F0"

        fig, ax = plt.subplots(figsize=(5, 2.8), dpi=90)
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)

        accent = "#4F8EF7"
        ax.plot(sems, gpas, marker="o", linewidth=2, markersize=6,
                color=accent, markerfacecolor=accent, zorder=5)
        ax.fill_between(range(len(sems)), gpas, alpha=0.12, color=accent)
        ax.axhline(y=4.0, color="#22C55E", linestyle="--", alpha=0.5, linewidth=1, label="Max (4.0)")
        ax.axhline(y=2.0, color="#F59E0B", linestyle="--", alpha=0.5, linewidth=1, label="Pass (2.0)")

        ax.set_xticks(range(len(sems)))
        ax.set_xticklabels(sems)
        ax.set_ylim(0, 4.5)
        ax.set_ylabel("GPA", color=text_col, fontsize=8)
        ax.tick_params(axis="x", colors=text_col, labelsize=8)
        ax.tick_params(axis="y", colors=text_col, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(grid_col)
        ax.grid(True, alpha=0.15, color=grid_col)
        ax.legend(loc="upper left", fontsize=7,
                  facecolor="#252E3E" if mode == "dark" else "#FFFFFF",
                  edgecolor=grid_col)

        fig.tight_layout(pad=0.5)
        canvas = FigureCanvasTkAgg(fig, master=self._cgpa_chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    def _navigate(self, page: str):
        if self.navigate_callback:
            self.navigate_callback(page)
