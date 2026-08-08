"""
Assignments Module
Centralized assignment management across all subjects.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date
from database import get_assignments, get_subjects, add_assignment, update_assignment, delete_assignment
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_INPUT, BG_CHIP, BG_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    ACCENT, ACCENT_HOVER, SUCCESS, WARNING, DANGER,
    BORDER, PAD_SM, PAD_MD, PAD_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG,
    priority_color,
)


def _font(size=FONT_MD, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def _bold(size=FONT_MD) -> ctk.CTkFont:
    return _font(size, "bold")


def get_due_state_label(due_date: str | None) -> str:
    """Return a short, human-readable label for assignment urgency."""
    if not due_date:
        return "No due date"
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
        delta = (due - date.today()).days
    except ValueError:
        return "Needs review"
    if delta < 0:
        return "Overdue"
    if delta == 0:
        return "Due today"
    if delta == 1:
        return "Due tomorrow"
    if delta <= 7:
        return "Due soon"
    return "On track"


def _due_color(due_date: str | None) -> str:
    if not due_date:
        return TEXT_MUTED[0]
    try:
        delta = (datetime.strptime(due_date, "%Y-%m-%d").date() - date.today()).days
        if delta <= 0:
            return DANGER[1]
        if delta <= 2:
            return WARNING[1]
        if delta <= 7:
            return ACCENT[1]
        return TEXT_MUTED[1]
    except Exception:
        return TEXT_MUTED[1]


class Assignments(ctk.CTkFrame):
    """Centralized assignments view."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.subjects_data = get_subjects()
        self.filter_status_var   = ctk.StringVar(value="all")
        self.filter_priority_var = ctk.StringVar(value="all")
        self.sort_var            = ctk.StringVar(value="due_date")
        self.search_var          = ctk.StringVar(value="")
        self._create_content()
        self._load_assignments()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _create_content(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        header.grid(row=0, column=0, sticky="ew", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        ctk.CTkLabel(
            header, text="☑  All Assignments",
            font=_bold(18),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=PAD_LG, pady=PAD_LG)

        ctk.CTkButton(
            header, text="+ Add Assignment",
            font=_bold(FONT_MD),
            width=145, height=34, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            command=self._show_add_assignment_dialog,
        ).pack(side="right", padx=PAD_LG, pady=PAD_LG)

        # Stats strip
        stats_bar = ctk.CTkFrame(self, fg_color=BG_CHIP, corner_radius=RADIUS_MD)
        stats_bar.grid(row=1, column=0, sticky="ew", padx=PAD_LG, pady=(0, PAD_SM))

        self.stats_label = ctk.CTkLabel(
            stats_bar, text="Loading…",
            font=_font(FONT_SM), text_color=TEXT_SECONDARY,
        )
        self.stats_label.pack(anchor="w", padx=PAD_LG, pady=PAD_SM)

        # Controls row
        controls = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_MD)
        controls.grid(row=2, column=0, sticky="ew", padx=PAD_LG, pady=(0, PAD_SM))

        ctk.CTkLabel(controls, text="⊘  Search:", text_color=TEXT_SECONDARY,
                     font=_font(FONT_SM)).pack(side="left", padx=(PAD_LG, PAD_SM), pady=PAD_MD)

        self.search_entry = ctk.CTkEntry(
            controls, textvariable=self.search_var,
            placeholder_text="Search assignments…",
            width=200, height=34, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            border_color=BORDER, border_width=1,
        )
        self.search_entry.pack(side="left", padx=(0, PAD_LG), pady=PAD_MD)
        self.search_entry.bind("<KeyRelease>", lambda _: self._load_assignments())

        _om_kw = dict(
            width=120, height=34, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=BG_HOVER, dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
        )
        ctk.CTkOptionMenu(
            controls, values=["all", "pending", "completed"],
            variable=self.filter_status_var,
            command=lambda _: self._load_assignments(), **_om_kw,
        ).pack(side="left", padx=PAD_SM, pady=PAD_MD)

        ctk.CTkOptionMenu(
            controls, values=["all", "high", "medium", "low"],
            variable=self.filter_priority_var,
            command=lambda _: self._load_assignments(), **_om_kw,
        ).pack(side="left", padx=PAD_SM, pady=PAD_MD)

        ctk.CTkOptionMenu(
            controls, values=["due_date", "priority", "status", "subject"],
            variable=self.sort_var,
            command=lambda _: self._load_assignments(), **_om_kw,
        ).pack(side="right", padx=PAD_LG, pady=PAD_MD)

        # List
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.grid(row=3, column=0, sticky="nsew", padx=PAD_LG, pady=(0, PAD_LG))

    # ── Data ────────────────────────────────────────────────────────────────

    def _load_assignments(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        all_a = get_assignments()

        q = self.search_var.get().lower()
        if q:
            all_a = [a for a in all_a if q in a.get("title", "").lower()]

        sf = self.filter_status_var.get()
        if sf != "all":
            all_a = [a for a in all_a if a.get("status") == sf]

        pf = self.filter_priority_var.get()
        if pf != "all":
            all_a = [a for a in all_a if a.get("priority") == pf]

        srt = self.sort_var.get()
        if srt == "due_date":
            all_a.sort(key=lambda x: x.get("due_date") or "9999-12-31")
        elif srt == "priority":
            order = {"high": 0, "medium": 1, "low": 2}
            all_a.sort(key=lambda x: order.get(x.get("priority", "low"), 2))
        elif srt == "status":
            all_a.sort(key=lambda x: x.get("status", "pending"))
        elif srt == "subject":
            all_a.sort(key=lambda x: self._subject_name(x.get("subject_id")))

        raw = get_assignments()
        pending = sum(1 for a in raw if a.get("status") == "pending")
        completed = len(raw) - pending
        self.stats_label.configure(
            text=f"Total: {len(raw)} · Pending: {pending} · Completed: {completed}"
        )

        if not all_a:
            ctk.CTkLabel(
                self.list_frame,
                text="No assignments match your filters.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=60)
        else:
            for a in all_a:
                self._create_card(a).pack(fill="x", pady=PAD_SM)

    # ── Card ─────────────────────────────────────────────────────────────────

    def _create_card(self, assignment: dict) -> ctk.CTkFrame:
        subj_id   = assignment.get("subject_id")
        subj_name = self._subject_name(subj_id)
        subj_col  = self._subject_color(subj_id)
        status    = assignment.get("status", "pending")
        priority  = assignment.get("priority", "medium")
        due_date  = assignment.get("due_date", "")
        p_color   = priority_color(priority)
        d_color   = _due_color(due_date)

        card = ctk.CTkFrame(
            self.list_frame, fg_color=BG_CARD, corner_radius=RADIUS_LG,
            border_width=1, border_color=BORDER, height=90,
        )
        card.pack_propagate(False)

        card.bind("<Enter>", lambda _: card.configure(fg_color=BG_HOVER))
        card.bind("<Leave>", lambda _: card.configure(fg_color=BG_CARD))

        # Subject accent strip
        ctk.CTkFrame(card, fg_color=subj_col, width=4, corner_radius=0).pack(side="left", fill="y")

        # Info
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=PAD_MD, pady=PAD_SM)

        ctk.CTkLabel(info, text=subj_name, font=_bold(FONT_XS),
                     text_color=subj_col, anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=assignment.get("title", "Untitled"),
                     font=_bold(FONT_MD),
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w", pady=(1, 0))

        meta = ctk.CTkFrame(info, fg_color="transparent")
        meta.pack(anchor="w")

        ctk.CTkLabel(meta, text=f"Due: {due_date or '—'}",
                     font=_font(FONT_SM), text_color=d_color).pack(side="left", padx=(0, PAD_MD))
        ctk.CTkLabel(meta, text=priority.title(),
                     font=_font(FONT_SM), text_color=p_color).pack(side="left", padx=(0, PAD_SM))
        ctk.CTkLabel(meta, text=get_due_state_label(due_date),
                     font=_font(FONT_SM), text_color=d_color).pack(side="left")

        status_color = SUCCESS[1] if status == "completed" else WARNING[1]
        ctk.CTkLabel(meta, text=status.title(), font=_font(FONT_SM),
                     text_color=status_color).pack(side="right")

        # Actions
        acts = ctk.CTkFrame(card, fg_color="transparent")
        acts.pack(side="right", padx=PAD_MD, pady=PAD_SM)

        ctk.CTkButton(
            acts,
            text="✓  Done" if status == "pending" else "↺  Undo",
            width=72, height=26, corner_radius=RADIUS_SM,
            fg_color=SUCCESS if status == "pending" else WARNING,
            hover_color=("#15803D", "#16A34A") if status == "pending" else ("#B45309", "#D97706"),
            text_color=TEXT_ON_ACCENT, font=_bold(FONT_SM),
            command=lambda a=assignment: self._toggle_status(a),
        ).pack(pady=2)
        ctk.CTkButton(
            acts, text="✎  Edit", width=72, height=26, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY, font=_font(FONT_SM),
            command=lambda a=assignment: self._edit_assignment(a),
        ).pack(pady=2)
        ctk.CTkButton(
            acts, text="✕  Del", width=72, height=26, corner_radius=RADIUS_SM,
            fg_color=DANGER, hover_color=("#B91C1C", "#DC2626"),
            text_color=TEXT_ON_ACCENT, font=_font(FONT_SM),
            command=lambda a=assignment: self._delete_assignment(a),
        ).pack(pady=2)

        return card

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _subject_name(self, subject_id: int) -> str:
        for s in self.subjects_data:
            if s.get("id") == subject_id:
                return s.get("name", "Unknown")
        return "Unknown"

    def _subject_color(self, subject_id: int) -> str:
        for s in self.subjects_data:
            if s.get("id") == subject_id:
                return s.get("color") or ACCENT[1]
        return ACCENT[1]

    # ── Actions ──────────────────────────────────────────────────────────────

    def _toggle_status(self, assignment: dict):
        new_status = "completed" if assignment.get("status") == "pending" else "pending"
        try:
            update_assignment(assignment_id=assignment["id"], status=new_status)
            self._load_assignments()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to update status: {exc}")

    def _edit_assignment(self, assignment: dict):
        dialog = AssignmentDialog(self, "Edit Assignment", self.subjects_data, assignment)
        self.wait_window(dialog)
        if dialog.result:
            try:
                update_assignment(
                    assignment_id=assignment["id"],
                    title=dialog.result["title"],
                    description=dialog.result.get("description"),
                    due_date=dialog.result.get("due_date"),
                    priority=dialog.result.get("priority"),
                    status=dialog.result.get("status"),
                )
                self._load_assignments()
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to update: {exc}")

    def _delete_assignment(self, assignment: dict):
        if messagebox.askyesno("Delete", f"Delete '{assignment['title']}'?"):
            try:
                delete_assignment(assignment["id"])
                self._load_assignments()
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to delete: {exc}")

    def _show_add_assignment_dialog(self):
        self.subjects_data = get_subjects()
        if not self.subjects_data:
            messagebox.showinfo("No Subjects", "Add subjects before creating assignments.")
            return
        dialog = AssignmentDialog(self, "Add Assignment", self.subjects_data)
        self.wait_window(dialog)
        if dialog.result:
            try:
                add_assignment(
                    subject_id=dialog.result["subject_id"],
                    title=dialog.result["title"],
                    description=dialog.result.get("description"),
                    due_date=dialog.result.get("due_date"),
                    priority=dialog.result.get("priority"),
                    status=dialog.result.get("status"),
                )
                self._load_assignments()
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to add: {exc}")


class AssignmentDialog(ctk.CTkToplevel):
    """Dialog for adding / editing assignments."""

    def __init__(self, parent, title: str, subjects: list, assignment_data: dict = None):
        super().__init__(parent)
        self.result = None
        self.subjects = subjects
        self.assignment_data = assignment_data
        self.title(title)
        self.geometry("500x560")
        self.transient(parent)
        self.grab_set()
        self._create_content()
        if assignment_data:
            self._load_data(assignment_data)

    def _create_content(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_SURFACE)
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        _lkw = dict(font=_font(FONT_SM), text_color=TEXT_SECONDARY, anchor="w")
        _ekw = dict(height=40, corner_radius=RADIUS_SM, border_width=1,
                    border_color=BORDER, fg_color=BG_INPUT,
                    text_color=TEXT_PRIMARY)

        # Subject
        ctk.CTkLabel(scroll, text="Subject *", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        subject_names = [s.get("name", "Unknown") for s in self.subjects]
        self.subject_var = ctk.StringVar(value=subject_names[0] if subject_names else "")
        ctk.CTkOptionMenu(
            scroll, values=subject_names, variable=self.subject_var,
            height=40, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=BG_HOVER, dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
        ).pack(fill="x", pady=(0, PAD_MD))

        # Title
        ctk.CTkLabel(scroll, text="Title *", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        self.title_entry = ctk.CTkEntry(scroll, placeholder_text="e.g., Chapter 1 Homework", **_ekw)
        self.title_entry.pack(fill="x", pady=(0, PAD_MD))

        # Description
        ctk.CTkLabel(scroll, text="Description", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        self.desc_text = ctk.CTkTextbox(
            scroll, height=90, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY, wrap="word",
        )
        self.desc_text.pack(fill="x", pady=(0, PAD_MD))

        # Due date
        ctk.CTkLabel(scroll, text="Due Date (YYYY-MM-DD)", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        self.date_entry = ctk.CTkEntry(scroll, placeholder_text="e.g., 2025-12-31", **_ekw)
        self.date_entry.pack(fill="x", pady=(0, PAD_MD))

        # Priority
        ctk.CTkLabel(scroll, text="Priority", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        self.priority_var = ctk.StringVar(value="medium")
        ctk.CTkOptionMenu(
            scroll, values=["low", "medium", "high"], variable=self.priority_var,
            height=40, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=BG_HOVER, dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
        ).pack(fill="x", pady=(0, PAD_MD))

        # Status
        ctk.CTkLabel(scroll, text="Status", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        self.status_var = ctk.StringVar(value="pending")
        ctk.CTkOptionMenu(
            scroll, values=["pending", "completed"], variable=self.status_var,
            height=40, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=BG_HOVER, dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
        ).pack(fill="x", pady=(0, PAD_SM))

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=PAD_LG, pady=(0, PAD_LG))

        ctk.CTkButton(
            btn_row, text="Cancel", height=38, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))

        ctk.CTkButton(
            btn_row, text="Save", height=38, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_ON_ACCENT,
            command=self._save,
        ).pack(side="right", fill="x", expand=True)

    def _load_data(self, a: dict):
        for s in self.subjects:
            if s.get("id") == a.get("subject_id"):
                self.subject_var.set(s.get("name", "Unknown"))
                break
        if a.get("title"):
            self.title_entry.insert(0, a["title"])
        if a.get("description"):
            self.desc_text.insert("1.0", a["description"])
        if a.get("due_date"):
            self.date_entry.insert(0, a["due_date"])
        if a.get("priority"):
            self.priority_var.set(a["priority"])
        if a.get("status"):
            self.status_var.set(a["status"])

    def _save(self):
        subject_name = self.subject_var.get()
        title = self.title_entry.get().strip()
        subject_id = next(
            (s["id"] for s in self.subjects if s.get("name") == subject_name), None
        )
        if not subject_id:
            messagebox.showerror("Error", "Please select a subject")
            return
        if not title:
            messagebox.showerror("Error", "Please enter a title")
            return
        desc = self.desc_text.get("1.0", "end-1c").strip()
        due  = self.date_entry.get().strip()
        self.result = {
            "subject_id": subject_id,
            "title": title,
            "description": desc or None,
            "due_date": due or None,
            "priority": self.priority_var.get(),
            "status": self.status_var.get(),
        }
        self.destroy()
