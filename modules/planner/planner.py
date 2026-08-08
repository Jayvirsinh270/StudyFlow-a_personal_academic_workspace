"""
Planner Module
Daily and weekly study planner with tasks, classes, and events integration.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date, timedelta
from database import (
    get_timetable, get_subjects, get_calendar_events,
    get_assignments, get_study_tasks, add_study_task,
    update_study_task, delete_study_task,
)
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_CHIP, BG_HOVER, BG_INPUT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    ACCENT, ACCENT_HOVER, SUCCESS, WARNING, DANGER,
    BORDER, PAD_SM, PAD_MD, PAD_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL,
)


def _font(size=FONT_MD, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

def _bold(size=FONT_MD) -> ctk.CTkFont:
    return _font(size, "bold")


class Planner(ctk.CTkFrame):
    """Study planner with daily schedule, tasks, and upcoming deadlines."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.subjects_data = get_subjects()

        from database import get_setting
        saved = get_setting("planner_selected_date")
        if saved:
            try:
                self.selected_date = datetime.strptime(saved, "%Y-%m-%d").date()
            except ValueError:
                self.selected_date = date.today()
        else:
            self.selected_date = date.today()

        self._create_content()
        self._load_planner_data()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _create_content(self):
        # Header with date navigation
        header = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        header.grid(row=0, column=0, sticky="ew", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        ctk.CTkLabel(
            header, text="▦  Study Planner",
            font=_bold(FONT_XL),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=PAD_LG, pady=PAD_LG)

        nav = ctk.CTkFrame(header, fg_color="transparent")
        nav.pack(side="right", padx=PAD_LG, pady=PAD_LG)

        _nb = dict(width=34, height=34, corner_radius=RADIUS_SM,
                   fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY)
        ctk.CTkButton(nav, text="◀", command=self._previous_day, **_nb).pack(side="left", padx=(0, PAD_SM))

        self.date_label = ctk.CTkLabel(
            nav, text=self.selected_date.strftime("%B %d, %Y"),
            font=_bold(FONT_MD),
            text_color=TEXT_PRIMARY, width=150,
        )
        self.date_label.pack(side="left", padx=PAD_SM)

        ctk.CTkButton(nav, text="▶", command=self._next_day, **_nb).pack(side="left", padx=(PAD_SM, PAD_SM))
        ctk.CTkButton(
            nav, text="Today", width=70, height=34, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT, font=_bold(FONT_SM),
            command=self._go_to_today,
        ).pack(side="left", padx=(PAD_SM, 0))

        # Two-column content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=PAD_LG, pady=(0, PAD_LG))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Left: Schedule
        sched_card = ctk.CTkFrame(content, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        sched_card.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))
        ctk.CTkLabel(
            sched_card, text="Today's Schedule",
            font=_bold(FONT_LG), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_MD))
        self.schedule_container = ctk.CTkScrollableFrame(sched_card, fg_color="transparent")
        self.schedule_container.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))

        # Right column
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(PAD_SM, 0))
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        # Tasks
        tasks_card = ctk.CTkFrame(right, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        tasks_card.grid(row=0, column=0, sticky="nsew", pady=(0, PAD_SM))
        th = ctk.CTkFrame(tasks_card, fg_color="transparent")
        th.pack(fill="x", padx=PAD_LG, pady=(PAD_LG, PAD_MD))
        ctk.CTkLabel(th, text="Study Tasks",
                     font=_bold(FONT_LG),
                     text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(
            th, text="＋  Task", width=85, height=30, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT, font=_bold(FONT_SM),
            command=self._show_add_task_dialog,
        ).pack(side="right")
        self.tasks_container = ctk.CTkScrollableFrame(tasks_card, fg_color="transparent")
        self.tasks_container.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))

        # Deadlines
        dead_card = ctk.CTkFrame(right, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        dead_card.grid(row=1, column=0, sticky="nsew", pady=(PAD_SM, 0))
        ctk.CTkLabel(
            dead_card, text="Upcoming Deadlines",
            font=_bold(FONT_LG), text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_MD))
        self.deadlines_container = ctk.CTkScrollableFrame(dead_card, fg_color="transparent")
        self.deadlines_container.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))

    # ── Data ────────────────────────────────────────────────────────────────

    def _load_planner_data(self):
        self.date_label.configure(text=self.selected_date.strftime("%B %d, %Y"))
        for c in (self.schedule_container, self.tasks_container, self.deadlines_container):
            for w in c.winfo_children():
                w.destroy()
        self._load_schedule()
        self._load_tasks()
        self._load_deadlines()

    def _load_schedule(self):
        day_name = self.selected_date.strftime("%A")
        timetable = get_timetable()
        entries   = [e for e in timetable if e.get("day") == day_name]
        date_str  = self.selected_date.strftime("%Y-%m-%d")
        events    = [ev for ev in get_calendar_events() if ev.get("event_date") == date_str]

        if not entries and not events:
            ctk.CTkLabel(
                self.schedule_container,
                text="No classes or events for this day.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=30)
            return

        slot_order = list(_SLOT_ORDER.keys())
        entries.sort(key=lambda x: slot_order.index(x.get("time_slot")) if x.get("time_slot") in slot_order else 999)

        for entry in entries:
            subj = next((s for s in self.subjects_data if s["id"] == entry.get("subject_id")), None)
            self._sched_item(
                time=entry.get("time_slot", ""),
                title=subj["name"] if subj else "Unknown",
                location=entry.get("classroom") or entry.get("room", ""),
                color=subj.get("color") or ACCENT[1] if subj else ACCENT[1],
            )
        for ev in events:
            event_colors = {"academic": WARNING[1], "exam": DANGER[1], "holiday": SUCCESS[1]}
            self._sched_item(
                time="All Day",
                title=ev.get("title", "Event"),
                location=ev.get("description", ""),
                color=event_colors.get(ev.get("event_type"), ACCENT[1]),
            )

    def _sched_item(self, time, title, location, color):
        card = ctk.CTkFrame(self.schedule_container, fg_color=BG_CARD, corner_radius=RADIUS_SM)
        card.pack(fill="x", pady=PAD_SM)

        ctk.CTkFrame(card, fg_color=color, width=4, corner_radius=0).pack(side="left", fill="y")
        ctk.CTkLabel(
            card, text=time, font=_bold(FONT_SM),
            text_color=color, width=84, anchor="w",
        ).pack(side="left", padx=PAD_MD, pady=PAD_SM)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=(0, PAD_SM), pady=PAD_SM)

        ctk.CTkLabel(inner, text=title, font=_bold(FONT_SM),
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
        if location:
            ctk.CTkLabel(inner, text=location, font=_font(FONT_XS),
                         text_color=TEXT_MUTED, anchor="w").pack(anchor="w")

    def _load_tasks(self):
        date_str   = self.selected_date.strftime("%Y-%m-%d")
        all_tasks  = get_study_tasks()
        day_tasks  = [t for t in all_tasks if t.get("due_date") == date_str]
        undated    = [t for t in all_tasks if not t.get("due_date") and t.get("status") == "pending"]
        other_pending = [t for t in all_tasks
                         if t.get("status") == "pending" and t.get("due_date") and t.get("due_date") != date_str]
        today_tasks = day_tasks + undated

        if not today_tasks and not other_pending:
            ctk.CTkLabel(
                self.tasks_container, text="No tasks for today.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=30)
            return

        if today_tasks:
            ctk.CTkLabel(self.tasks_container, text="Today",
                         font=_bold(FONT_XS),
                         text_color=ACCENT[1]).pack(anchor="w", pady=(PAD_SM, PAD_SM))
            for t in today_tasks:
                self._task_item(t)

        if other_pending:
            ctk.CTkLabel(self.tasks_container, text="Pending (Other Days)",
                         font=_bold(FONT_XS),
                         text_color=WARNING[1]).pack(anchor="w", pady=(PAD_MD, PAD_SM))
            for t in other_pending[:5]:
                self._task_item(t)

    def _task_item(self, task):
        card = ctk.CTkFrame(self.tasks_container, fg_color=BG_CARD, corner_radius=RADIUS_SM)
        card.pack(fill="x", pady=3)
        card.bind("<Enter>", lambda e, c=card: c.configure(fg_color=BG_HOVER))
        card.bind("<Leave>", lambda e, c=card: c.configure(fg_color=BG_CARD))

        cb = ctk.CTkCheckBox(
            card, text="", width=20, height=20, corner_radius=4, border_width=2,
            fg_color=SUCCESS, hover_color=("#15803D", "#16A34A"),
            command=lambda t=task: self._toggle_task(t),
        )
        if task.get("status") == "completed":
            cb.select()
        cb.pack(side="left", padx=PAD_MD, pady=PAD_SM)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=(0, PAD_SM), pady=PAD_SM)

        ctk.CTkLabel(inner, text=task.get("title", "Untitled"),
                     font=_font(FONT_SM), text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
        if task.get("description"):
            ctk.CTkLabel(inner, text=task["description"],
                         font=_font(FONT_XS), text_color=TEXT_MUTED, anchor="w").pack(anchor="w")

        ctk.CTkButton(
            card, text="×", width=26, height=26, corner_radius=RADIUS_SM,
            fg_color=DANGER, hover_color=("#B91C1C", "#DC2626"),
            text_color=TEXT_ON_ACCENT, font=_bold(FONT_MD),
            command=lambda t=task: self._delete_task(t),
        ).pack(side="right", padx=PAD_MD)

    def _load_deadlines(self):
        today = date.today()
        pending = []
        for a in get_assignments():
            if a.get("status") != "completed" and a.get("due_date"):
                try:
                    dd = datetime.strptime(a["due_date"], "%Y-%m-%d").date()
                    if dd >= today:
                        pending.append((a, dd))
                except Exception:
                    pass
        pending.sort(key=lambda x: x[1])

        if not pending:
            ctk.CTkLabel(
                self.deadlines_container, text="No upcoming deadlines.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=30)
            return

        for assignment, dd in pending[:5]:
            days = (dd - today).days
            if days == 0:
                urgency, uc = "Due today", DANGER[1]
            elif days == 1:
                urgency, uc = "Tomorrow", WARNING[1]
            elif days <= 7:
                urgency, uc = f"{days}d", WARNING[1]
            else:
                urgency, uc = f"{days}d", TEXT_MUTED[1]

            subj = next((s for s in self.subjects_data if s["id"] == assignment.get("subject_id")), None)
            card = ctk.CTkFrame(self.deadlines_container, fg_color=BG_CARD, corner_radius=RADIUS_SM)
            card.pack(fill="x", pady=3)

            ctk.CTkLabel(
                card, text=urgency, font=_bold(FONT_SM),
                text_color=uc, width=68,
            ).pack(side="left", padx=PAD_MD, pady=PAD_SM)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(side="left", fill="both", expand=True, padx=(0, PAD_SM), pady=PAD_SM)
            ctk.CTkLabel(inner, text=assignment.get("title", "Untitled"),
                         font=_bold(FONT_SM),
                         text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(inner, text=subj["name"] if subj else "Unknown",
                         font=_font(FONT_XS), text_color=TEXT_MUTED, anchor="w").pack(anchor="w")

    # ── Navigation ───────────────────────────────────────────────────────────

    def _previous_day(self):
        self.selected_date -= timedelta(days=1)
        self._persist_date()
        self._load_planner_data()

    def _next_day(self):
        self.selected_date += timedelta(days=1)
        self._persist_date()
        self._load_planner_data()

    def _go_to_today(self):
        self.selected_date = date.today()
        self._persist_date()
        self._load_planner_data()

    def _persist_date(self):
        from database import set_setting
        set_setting("planner_selected_date", self.selected_date.strftime("%Y-%m-%d"))

    # ── Tasks dialog ─────────────────────────────────────────────────────────

    def _show_add_task_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Study Task")
        dialog.geometry("420x360")
        dialog.transient(self)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(dialog, fg_color=BG_SURFACE)
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        _lkw = dict(font=_font(FONT_SM), text_color=TEXT_SECONDARY, anchor="w")
        ctk.CTkLabel(scroll, text="Title:", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        title_e = ctk.CTkEntry(scroll, placeholder_text="Task title", height=38,
                                corner_radius=RADIUS_SM, fg_color=BG_INPUT,
                                text_color=TEXT_PRIMARY, border_color=BORDER, border_width=1)
        title_e.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(scroll, text="Description:", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        desc_e = ctk.CTkTextbox(scroll, height=80, corner_radius=RADIUS_SM,
                                 fg_color=BG_INPUT, text_color=TEXT_PRIMARY)
        desc_e.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(scroll, text="Due Date (YYYY-MM-DD):", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        date_e = ctk.CTkEntry(scroll, placeholder_text="Optional",
                               height=38, corner_radius=RADIUS_SM,
                               fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
                               border_color=BORDER, border_width=1)
        date_e.insert(0, self.selected_date.strftime("%Y-%m-%d"))
        date_e.pack(fill="x")

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=PAD_LG, pady=(0, PAD_LG))

        def _save():
            title = title_e.get().strip()
            if not title:
                messagebox.showerror("Error", "Title is required")
                return
            try:
                add_study_task(
                    title=title,
                    task_type="daily",
                    description=desc_e.get("1.0", "end").strip() or None,
                    due_date=date_e.get().strip() or None,
                )
                dialog.destroy()
                self._load_planner_data()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        ctk.CTkButton(btn_row, text="Cancel", height=38, corner_radius=RADIUS_SM,
                      fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
                      command=dialog.destroy).pack(side="right", padx=(PAD_SM, 0))
        ctk.CTkButton(btn_row, text="Save", height=38, corner_radius=RADIUS_SM,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_ON_ACCENT,
                      command=_save).pack(side="right")

    def _toggle_task(self, task):
        new = "completed" if task.get("status") != "completed" else "pending"
        update_study_task(task["id"], status=new)
        self._load_planner_data()

    def _delete_task(self, task):
        if messagebox.askyesno("Confirm", "Delete this task?"):
            delete_study_task(task["id"])
            self._load_planner_data()


# slot order for sorting — covers full 06:00-23:00 range used by timetable
_SLOT_ORDER = {f"{h}:00-{h+1}:00": i for i, h in enumerate(range(6, 23))}
