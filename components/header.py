"""
Header Component — Premium top bar for StudyFlow.
Features: breadcrumb, live clock, global search, notification bell, profile chip.
"""

import customtkinter as ctk
from datetime import datetime
from database import get_subjects, get_notes, get_assignments, get_subject_files, get_student_profile
from utils.theme import (
    BG_HEADER, BG_INPUT, BG_CHIP, BG_HOVER, BG_SURFACE, BG_CARD,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    ACCENT, ACCENT_HOVER, BORDER,
    DANGER, WARNING,
    PAD_SM, PAD_MD, PAD_LG, RADIUS_SM, RADIUS_MD, RADIUS_LG,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG,
)


def _font(size=FONT_MD, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


class Header(ctk.CTkFrame):
    """Premium header bar: breadcrumb, live clock, search, notifications, profile."""

    def __init__(self, master, navigate_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.navigate_callback = navigate_callback
        self._clock_job = None
        self._notif_count = 0

        self.configure(
            height=60,
            corner_radius=0,
            fg_color=BG_HEADER,
        )

        self._create_content()
        self._tick_clock()

    def _create_content(self):
        # Bottom border line
        border = ctk.CTkFrame(self, fg_color=BORDER, height=1)
        border.pack(side="bottom", fill="x")

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, 1))

        # ── Left: breadcrumb ─────────────────────────────────────────────────
        left = ctk.CTkFrame(wrap, fg_color="transparent")
        left.pack(side="left", padx=(0, PAD_MD))

        home_btn = ctk.CTkButton(
            left,
            text="⊞  StudyFlow",
            width=100,
            height=30,
            corner_radius=RADIUS_SM,
            fg_color=BG_CHIP,
            hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            font=_font(FONT_SM),
            command=lambda: self._navigate_to("dashboard"),
        )
        home_btn.pack(side="left")

        ctk.CTkLabel(
            left, text=" › ",
            font=_font(FONT_MD), text_color=TEXT_MUTED,
        ).pack(side="left")

        self.page_title = ctk.CTkLabel(
            left, text="Dashboard",
            font=_font(FONT_MD, "bold"), text_color=TEXT_PRIMARY,
        )
        self.page_title.pack(side="left")

        # ── Center: search bar ───────────────────────────────────────────────
        center = ctk.CTkFrame(wrap, fg_color="transparent")
        center.pack(side="left", expand=True, fill="x", padx=PAD_LG)

        search_bg = ctk.CTkFrame(
            center,
            fg_color=BG_INPUT,
            corner_radius=RADIUS_MD,
            border_width=1,
            border_color=BORDER,
        )
        search_bg.pack(fill="x")

        ctk.CTkLabel(
            search_bg, text="⊘",
            font=_font(FONT_MD), text_color=TEXT_MUTED, width=30,
        ).pack(side="left", padx=(PAD_SM, 0))

        self.search_entry = ctk.CTkEntry(
            search_bg,
            placeholder_text="Search subjects, assignments, notes…  Ctrl+K",
            font=_font(FONT_SM),
            height=34,
            corner_radius=RADIUS_MD,
            border_width=0,
            fg_color="transparent",
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
        )
        self.search_entry.pack(fill="both", expand=True, padx=(4, PAD_SM))
        self.search_entry.bind("<Return>", self._on_search_enter)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkLabel(
            search_bg, text="Ctrl+K",
            font=_font(FONT_XS), text_color=TEXT_MUTED,
            fg_color=BG_CHIP, corner_radius=4, padx=6, pady=2,
        ).pack(side="right", padx=(0, PAD_SM))

        # ── Right: clock, notifications, profile ─────────────────────────────
        right = ctk.CTkFrame(wrap, fg_color="transparent")
        right.pack(side="right")

        # Live clock
        self.clock_label = ctk.CTkLabel(
            right, text="",
            font=_font(FONT_SM), text_color=TEXT_SECONDARY,
        )
        self.clock_label.pack(side="left", padx=(0, PAD_MD))

        # Notification bell with badge
        self.notif_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.notif_frame.pack(side="left", padx=(0, PAD_SM))

        self.notif_btn = ctk.CTkButton(
            self.notif_frame,
            text="⊛",
            width=36, height=36,
            corner_radius=RADIUS_SM,
            fg_color=BG_CHIP,
            hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            font=_font(FONT_MD),
            command=self._show_notifications,
        )
        self.notif_btn.pack()

        # Notification count badge
        self.notif_badge = ctk.CTkFrame(
            self.notif_frame,
            fg_color=DANGER[1],
            corner_radius=8, width=16, height=16,
        )
        self.notif_badge_lbl = ctk.CTkLabel(
            self.notif_badge, text="0",
            font=_font(FONT_XS, "bold"),
            text_color="#FFFFFF",
        )
        self.notif_badge_lbl.place(relx=0.5, rely=0.5, anchor="center")
        # Hidden by default
        self.notif_badge.place_forget()

        # Profile chip
        self.profile_chip = ctk.CTkFrame(
            right,
            fg_color=BG_CHIP,
            corner_radius=RADIUS_MD,
        )
        self.profile_chip.pack(side="left")

        self.profile_avatar = ctk.CTkFrame(
            self.profile_chip,
            fg_color=ACCENT,
            corner_radius=14, width=28, height=28,
        )
        self.profile_avatar.pack(side="left", padx=(PAD_SM, 0), pady=5)
        self.profile_avatar.pack_propagate(False)
        self.avatar_letter = ctk.CTkLabel(
            self.profile_avatar, text="S",
            font=_font(FONT_SM, "bold"),
            text_color="#FFFFFF",
        )
        self.avatar_letter.place(relx=0.5, rely=0.5, anchor="center")

        self.profile_label = ctk.CTkLabel(
            self.profile_chip, text="Student",
            font=_font(FONT_SM, "bold"),
            text_color=TEXT_PRIMARY,
        )
        self.profile_label.pack(side="left", padx=(PAD_SM, PAD_MD), pady=5)

        self.profile_chip.bind("<Button-1>", lambda e: self._navigate_to("settings"))
        self._refresh_profile()

    # ── Live clock ────────────────────────────────────────────────────────────
    def _tick_clock(self):
        now = datetime.now()
        self.clock_label.configure(text=now.strftime("%a, %b %d  %I:%M %p"))
        self._clock_job = self.after(30_000, self._tick_clock)

    # ── Profile ───────────────────────────────────────────────────────────────
    def _refresh_profile(self):
        try:
            profile = get_student_profile()
            if profile and profile.get("name"):
                name = profile["name"]
                first = name.split()[0] if name.split() else name
                self.profile_label.configure(text=first[:14])
                self.avatar_letter.configure(text=first[0].upper())
        except Exception:
            pass

    def set_page_title(self, title: str):
        self.page_title.configure(text=title)
        self._refresh_profile()
        self._check_notifications_count()

    # ── Navigation ────────────────────────────────────────────────────────────
    def _navigate_to(self, page_id: str):
        if self.navigate_callback:
            self.navigate_callback(page_id)

    # ── Search ────────────────────────────────────────────────────────────────
    def _on_search(self, event=None):
        text = self.search_entry.get().strip().lower()
        if len(text) >= 2:
            self._show_search_results(text)

    def _on_search_enter(self, event=None):
        text = self.search_entry.get().strip().lower()
        if text:
            self._show_search_results(text)

    def _show_search_results(self, search_text: str):
        results = []

        for s in get_subjects():
            if search_text in s.get("name", "").lower():
                results.append({"type": "subject", "title": s["name"],
                                 "subtitle": s.get("subject_code", ""), "id": s["id"]})

        for n in get_notes():
            if search_text in n.get("title", "").lower() or search_text in (n.get("content") or "").lower():
                results.append({"type": "note", "title": n["title"],
                                 "subtitle": f"Subject {n.get('subject_id', '')}", "id": n["id"]})

        for a in get_assignments():
            if search_text in a.get("title", "").lower() or search_text in (a.get("description") or "").lower():
                results.append({"type": "assignment", "title": a["title"],
                                 "subtitle": f"Due: {a.get('due_date', 'No date')}", "id": a["id"]})

        for s in get_subjects():
            for f in get_subject_files(s["id"]):
                if search_text in f.get("file_name", "").lower():
                    results.append({"type": "file", "title": f["file_name"],
                                     "subtitle": f.get("file_type", ""), "id": f["id"]})

        SearchResultsDialog(self, search_text, results)

    # ── Notifications ─────────────────────────────────────────────────────────
    def _check_notifications_count(self):
        """Update the notification badge count."""
        try:
            from datetime import date
            count = 0
            today = date.today()

            for a in get_assignments():
                if a.get("status") != "completed" and a.get("due_date"):
                    try:
                        due = datetime.strptime(a["due_date"], "%Y-%m-%d").date()
                        if (due - today).days <= 3:
                            count += 1
                    except Exception:
                        pass

            from database import calculate_attendance_percentage
            for s in get_subjects():
                try:
                    if calculate_attendance_percentage(s["id"]) < 75:
                        count += 1
                except Exception:
                    pass

            self._notif_count = count
            if count > 0:
                self.notif_btn.configure(fg_color=("#FEF2F2", "#450A0A"), text_color=DANGER[1])
                self.notif_badge_lbl.configure(text=str(min(count, 99)))
                self.notif_badge.place(in_=self.notif_frame, relx=0.7, rely=0.05)
            else:
                self.notif_btn.configure(fg_color=BG_CHIP, text_color=TEXT_SECONDARY)
                self.notif_badge.place_forget()
        except Exception:
            pass

    def _show_notifications(self):
        from datetime import date
        notifications = []
        today = date.today()

        for a in get_assignments():
            if a.get("status") != "completed" and a.get("due_date"):
                try:
                    due = datetime.strptime(a["due_date"], "%Y-%m-%d").date()
                    delta = (due - today).days
                    if delta <= 3:
                        urgency = "Due today!" if delta == 0 else (
                            f"Due in {delta} day(s)" if delta > 0 else "Overdue!"
                        )
                        notifications.append({
                            "type": "assignment", "title": a["title"],
                            "message": urgency,
                            "priority": "high" if delta <= 1 else "medium",
                        })
                except Exception:
                    pass

        from database import calculate_attendance_percentage
        for s in get_subjects():
            try:
                pct = calculate_attendance_percentage(s["id"])
                if pct < 75:
                    notifications.append({
                        "type": "attendance", "title": s["name"],
                        "message": f"Attendance: {pct:.1f}% — Below 75%",
                        "priority": "high",
                    })
            except Exception:
                pass

        NotificationsDialog(self, notifications)


# ── Shared dialog helper ──────────────────────────────────────────────────────

def _apply_dialog_style(dialog):
    dialog.transient(dialog.master)
    dialog.grab_set()


class SearchResultsDialog(ctk.CTkToplevel):
    """Polished search-results modal."""

    _TYPE_ICONS  = {"subject": "⊟", "note": "✎", "assignment": "☑", "file": "≡"}
    _TYPE_COLORS = {
        "subject": ACCENT[1], "note": "#22C55E",
        "assignment": "#F59E0B", "file": "#A855F7",
    }

    def __init__(self, parent, search_text: str, results: list):
        super().__init__(parent)
        self.title("Search Results")
        self.geometry("540x460")
        self.resizable(False, False)
        _apply_dialog_style(self)
        self._build(search_text, results)

    def _build(self, search_text, results):
        wrap = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        wrap.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        # Header
        hdr = ctk.CTkFrame(wrap, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(
            hdr, text=f'⊘  Results for "{search_text}"',
            font=_font(FONT_LG, "bold"), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            hdr, text=f"{len(results)} found",
            font=_font(FONT_SM), text_color=TEXT_SECONDARY,
        ).pack(side="right")

        ctk.CTkFrame(wrap, fg_color=BORDER, height=1).pack(fill="x", pady=(0, PAD_SM))

        scroll = ctk.CTkScrollableFrame(wrap, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not results:
            ctk.CTkLabel(
                scroll, text="Nothing matched your query.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=50)
        else:
            for r in results:
                row = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=RADIUS_SM)
                row.pack(fill="x", pady=3)
                row.bind("<Enter>", lambda e, w=row: w.configure(fg_color=BG_HOVER))
                row.bind("<Leave>", lambda e, w=row: w.configure(fg_color=BG_CARD))

                color = self._TYPE_COLORS.get(r["type"], TEXT_SECONDARY)
                icon_bg = ctk.CTkFrame(row, fg_color=BG_CHIP, width=36, height=36, corner_radius=RADIUS_SM)
                icon_bg.pack(side="left", padx=PAD_SM, pady=PAD_SM)
                icon_bg.pack_propagate(False)
                ctk.CTkLabel(
                    icon_bg, text=self._TYPE_ICONS.get(r["type"], "•"),
                    font=_font(FONT_MD), text_color=color,
                ).place(relx=0.5, rely=0.5, anchor="center")

                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
                ctk.CTkLabel(
                    info, text=r["title"],
                    font=_font(FONT_MD, "bold"), text_color=TEXT_PRIMARY, anchor="w",
                ).pack(anchor="w")
                ctk.CTkLabel(
                    info, text=r["subtitle"],
                    font=_font(FONT_XS), text_color=TEXT_SECONDARY, anchor="w",
                ).pack(anchor="w")

                # Type badge
                badge = ctk.CTkLabel(
                    row, text=r["type"].upper(),
                    font=_font(FONT_XS, "bold"),
                    text_color=color,
                    fg_color=BG_CHIP,
                    corner_radius=4, padx=6, pady=2,
                )
                badge.pack(side="right", padx=PAD_MD)

        ctk.CTkFrame(wrap, fg_color=BORDER, height=1).pack(fill="x", pady=(PAD_SM, PAD_SM))
        ctk.CTkButton(
            wrap, text="Close", height=36, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            command=self.destroy,
        ).pack(fill="x")


class NotificationsDialog(ctk.CTkToplevel):
    """Premium notifications panel."""

    _PRIORITY_COLORS = {"high": DANGER[1], "medium": WARNING[1], "low": "#22C55E"}
    _TYPE_ICONS = {"assignment": "☑", "attendance": "◎", "exam": "✎", "general": "⊛"}

    def __init__(self, parent, notifications: list):
        super().__init__(parent)
        self.title("Notifications")
        self.geometry("420x420")
        self.resizable(False, False)
        _apply_dialog_style(self)
        self._build(notifications)

    def _build(self, notifications):
        wrap = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        wrap.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        hdr = ctk.CTkFrame(wrap, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(
            hdr, text="⊛  Notifications",
            font=_font(FONT_LG, "bold"), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        if notifications:
            badge = ctk.CTkFrame(hdr, fg_color=DANGER[1], corner_radius=12, width=24, height=24)
            badge.pack(side="right")
            badge.pack_propagate(False)
            ctk.CTkLabel(
                badge, text=str(len(notifications)),
                font=_font(FONT_XS, "bold"), text_color="#FFFFFF",
            ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkFrame(wrap, fg_color=BORDER, height=1).pack(fill="x", pady=(0, PAD_SM))

        scroll = ctk.CTkScrollableFrame(wrap, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        if not notifications:
            inner = ctk.CTkFrame(scroll, fg_color="transparent")
            inner.pack(expand=True, pady=50)
            ctk.CTkLabel(inner, text="✓", font=_font(28, "bold"),
                         text_color="#22C55E").pack()
            ctk.CTkLabel(inner, text="You're all caught up!",
                         font=_font(FONT_LG, "bold"), text_color=TEXT_PRIMARY).pack(pady=(PAD_SM, 0))
            ctk.CTkLabel(inner, text="No pending alerts or low attendance.",
                         font=_font(FONT_SM), text_color=TEXT_MUTED).pack()
        else:
            for n in notifications:
                row = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=RADIUS_SM)
                row.pack(fill="x", pady=3)

                bar_color = self._PRIORITY_COLORS.get(n.get("priority", "medium"), "#22C55E")
                bar = ctk.CTkFrame(row, fg_color=bar_color, width=4, corner_radius=0)
                bar.pack(side="left", fill="y")

                icon_bg = ctk.CTkFrame(
                    row, fg_color=BG_CHIP,
                    width=34, height=34, corner_radius=RADIUS_SM,
                )
                icon_bg.pack(side="left", padx=PAD_SM, pady=PAD_SM)
                icon_bg.pack_propagate(False)
                ctk.CTkLabel(
                    icon_bg, text=self._TYPE_ICONS.get(n.get("type", "general"), "⊛"),
                    font=_font(FONT_MD), text_color=bar_color,
                ).place(relx=0.5, rely=0.5, anchor="center")

                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
                ctk.CTkLabel(
                    info, text=n["title"],
                    font=_font(FONT_MD, "bold"), text_color=TEXT_PRIMARY, anchor="w",
                ).pack(anchor="w")
                ctk.CTkLabel(
                    info, text=n["message"],
                    font=_font(FONT_SM), text_color=TEXT_SECONDARY, anchor="w",
                ).pack(anchor="w")

        ctk.CTkFrame(wrap, fg_color=BORDER, height=1).pack(fill="x", pady=(PAD_SM, PAD_SM))
        ctk.CTkButton(
            wrap, text="Dismiss All", height=36, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            command=self.destroy,
        ).pack(fill="x")
