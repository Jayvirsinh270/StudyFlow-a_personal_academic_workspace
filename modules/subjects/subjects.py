"""
Subjects Module — Premium redesign for StudyFlow.
"""

import customtkinter as ctk
from tkinter import messagebox
from database import add_subject, get_subjects, update_subject, delete_subject
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_CHIP, BG_HOVER, BG_INPUT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT, ACCENT_HOVER, BORDER,
    DANGER, SUCCESS,
    PAD_SM, PAD_MD, PAD_LG, RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL,
    SUBJECT_COLORS,
)


def _font(size=FONT_MD, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def _bold(size=FONT_MD) -> ctk.CTkFont:
    return _font(size, "bold")


def _subject_color(subject: dict, index: int = 0) -> str:
    return subject.get("color") or SUBJECT_COLORS[index % len(SUBJECT_COLORS)]


class Subjects(ctk.CTkFrame):
    """Subjects view with premium card-based display."""

    def __init__(self, master, navigate_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.subjects_data: list = []
        self.navigate_callback = navigate_callback
        self._create_content()
        self._load_subjects()

    def _create_content(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(
            self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
            border_width=1, border_color=BORDER,
        )
        header.pack(fill="x", pady=(0, PAD_MD))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=PAD_LG, pady=PAD_MD)

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")
        ctk.CTkLabel(
            title_row, text="⊟", font=_font(FONT_XL), text_color=ACCENT[1],
        ).pack(side="left", padx=(0, PAD_SM))
        ctk.CTkLabel(
            title_row, text="My Subjects",
            font=_bold(FONT_XL), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self._summary_lbl = ctk.CTkLabel(
            left, text="Loading…",
            font=_font(FONT_SM), text_color=TEXT_MUTED,
        )
        self._summary_lbl.pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            header, text="＋  Add Subject",
            font=_bold(FONT_MD),
            width=140, height=38, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=("#FFFFFF", "#FFFFFF"),
            command=self._show_add_subject_dialog,
        ).pack(side="right", padx=PAD_LG, pady=PAD_MD)

        # ── Search ────────────────────────────────────────────────────────────
        search_bg = ctk.CTkFrame(
            self, fg_color=BG_INPUT, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER,
        )
        search_bg.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(
            search_bg, text="⊘", font=_font(FONT_MD),
            text_color=TEXT_MUTED, width=30,
        ).pack(side="left", padx=(PAD_SM, 0))

        self._search_entry = ctk.CTkEntry(
            search_bg,
            placeholder_text="Search subjects by name, code, or faculty…",
            height=40, corner_radius=RADIUS_SM, border_width=0,
            fg_color="transparent", text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
        )
        self._search_entry.pack(fill="x", expand=True, padx=(4, PAD_SM))
        self._search_entry.bind("<KeyRelease>", lambda e: self._filter_subjects(self._search_entry.get()))

        # ── Grid container ────────────────────────────────────────────────────
        self._grid = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._grid.pack(fill="both", expand=True)
        for col in range(3):
            self._grid.grid_columnconfigure(col, weight=1)

    def _load_subjects(self):
        self.subjects_data = get_subjects()
        count = len(self.subjects_data)
        if count:
            self._summary_lbl.configure(
                text=f"{count} subject{'s' if count != 1 else ''} this semester"
            )
        else:
            self._summary_lbl.configure(text="No subjects yet — add your first one")
        self._display_subjects(self.subjects_data)

    def _display_subjects(self, subjects: list):
        for w in self._grid.winfo_children():
            w.destroy()

        if not subjects:
            empty = ctk.CTkFrame(self._grid, fg_color="transparent")
            empty.grid(row=0, column=0, columnspan=3, pady=80)

            # Empty state illustration
            icon_frame = ctk.CTkFrame(
                empty, fg_color=BG_CHIP, corner_radius=RADIUS_XL,
                width=80, height=80,
            )
            icon_frame.pack()
            icon_frame.pack_propagate(False)
            ctk.CTkLabel(
                icon_frame, text="⊟", font=_font(32), text_color=TEXT_MUTED,
            ).place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(
                empty, text="No subjects found",
                font=_bold(FONT_XL), text_color=TEXT_PRIMARY,
            ).pack(pady=(PAD_MD, PAD_XS if hasattr(self, '_no') else 4))
            ctk.CTkLabel(
                empty,
                text="Add your first subject to start organizing your semester.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack()
            ctk.CTkButton(
                empty, text="＋  Add Your First Subject",
                font=_bold(FONT_MD),
                height=42, corner_radius=RADIUS_SM,
                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                text_color=("#FFFFFF", "#FFFFFF"),
                command=self._show_add_subject_dialog,
            ).pack(pady=(PAD_MD, 0))
            return

        for i, subj in enumerate(subjects):
            row, col = divmod(i, 3)
            card = self._make_card(subj, i)
            card.grid(row=row, column=col, padx=PAD_SM, pady=PAD_SM, sticky="nsew")

    def _make_card(self, subject: dict, index: int) -> ctk.CTkFrame:
        color = _subject_color(subject, index)

        card = ctk.CTkFrame(
            self._grid, fg_color=BG_SURFACE,
            corner_radius=RADIUS_LG, border_width=1, border_color=BORDER,
        )
        card.pack_propagate(False)
        card.configure(height=190)

        # Colored top accent bar
        bar = ctk.CTkFrame(card, fg_color=color, height=5, corner_radius=0)
        bar.pack(fill="x")

        # Hover effect
        card.bind("<Enter>", lambda e: card.configure(border_color=color))
        card.bind("<Leave>", lambda e: card.configure(border_color=BORDER))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=PAD_MD, pady=(PAD_SM, 0))
        body.bind("<Button-1>", lambda e, s=subject: self._open_workspace(s))

        # Subject initial circle + name
        header_row = ctk.CTkFrame(body, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, PAD_XS if hasattr(self, '_xs') else 2))

        initial_frame = ctk.CTkFrame(
            header_row, fg_color=BG_CHIP,
            corner_radius=RADIUS_SM, width=36, height=36,
        )
        initial_frame.pack(side="left")
        initial_frame.pack_propagate(False)
        ctk.CTkLabel(
            initial_frame,
            text=subject.get("name", "?")[0].upper(),
            font=_bold(FONT_MD), text_color=color,
        ).place(relx=0.5, rely=0.5, anchor="center")

        name_lbl = ctk.CTkLabel(
            header_row,
            text=subject.get("name", "Unknown"),
            font=_bold(FONT_MD),
            text_color=TEXT_PRIMARY, anchor="w", wraplength=160,
        )
        name_lbl.pack(side="left", padx=(PAD_SM, 0))
        name_lbl.bind("<Button-1>", lambda e, s=subject: self._open_workspace(s))

        # Code badge
        if subject.get("subject_code"):
            code_chip = ctk.CTkLabel(
                body, text=subject["subject_code"],
                font=_bold(FONT_XS),
                text_color=color, fg_color=BG_CHIP,
                corner_radius=RADIUS_SM, padx=8, pady=2,
            )
            code_chip.pack(anchor="w", pady=(2, 0))

        # Faculty
        if subject.get("faculty_name"):
            ctk.CTkLabel(
                body, text=f"⊗  {subject['faculty_name']}",
                font=_font(FONT_SM), text_color=TEXT_SECONDARY, anchor="w",
            ).pack(anchor="w", pady=(4, 0))

        # Semester & credits
        meta_row = ctk.CTkFrame(body, fg_color="transparent")
        meta_row.pack(fill="x", pady=(4, 0))
        if subject.get("semester"):
            ctk.CTkLabel(
                meta_row, text=f"Sem {subject['semester']}",
                font=_bold(FONT_SM), text_color=color,
            ).pack(side="left", padx=(0, PAD_SM))
        if subject.get("credit"):
            ctk.CTkLabel(
                meta_row, text=f"{subject['credit']} Cr",
                font=_font(FONT_SM), text_color=TEXT_MUTED,
            ).pack(side="left")

        # Action buttons
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=PAD_MD, pady=(PAD_SM, PAD_MD))

        ctk.CTkButton(
            btn_row, text="✎  Edit",
            width=65, height=28, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            font=_font(FONT_SM),
            command=lambda s=subject: self._show_edit_subject_dialog(s),
        ).pack(side="left", padx=(0, PAD_SM))

        ctk.CTkButton(
            btn_row, text="✕  Delete",
            width=70, height=28, corner_radius=RADIUS_SM,
            fg_color=("#FEE2E2", "#450A0A"), hover_color=("#FECACA", "#7F1D1D"),
            text_color=DANGER[0], font=_font(FONT_SM),
            command=lambda s=subject: self._delete_subject(s),
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="Open →",
            width=75, height=28, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=("#FFFFFF", "#FFFFFF"), font=_bold(FONT_SM),
            command=lambda s=subject: self._open_workspace(s),
        ).pack(side="right")

        return card

    def _filter_subjects(self, text: str):
        if not text:
            self._display_subjects(self.subjects_data)
            return
        t = text.lower()
        filtered = [s for s in self.subjects_data
                    if t in s.get("name", "").lower()
                    or t in s.get("subject_code", "").lower()
                    or t in s.get("faculty_name", "").lower()]
        self._display_subjects(filtered)

    def _show_add_subject_dialog(self):
        dlg = SubjectDialog(self, "Add Subject")
        self.wait_window(dlg)
        if dlg.result:
            try:
                add_subject(**dlg.result)
                self._load_subjects()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add subject: {e}")

    def _show_edit_subject_dialog(self, subject: dict):
        dlg = SubjectDialog(self, "Edit Subject", subject)
        self.wait_window(dlg)
        if dlg.result:
            try:
                update_subject(subject_id=subject["id"], **dlg.result)
                self._load_subjects()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update subject: {e}")

    def _delete_subject(self, subject: dict):
        if messagebox.askyesno(
            "Delete Subject",
            f"Delete '{subject['name']}'?\n\nThis will also remove all related notes, files, attendance, and assignments.",
        ):
            try:
                delete_subject(subject["id"])
                self._load_subjects()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete subject: {e}")

    def _open_workspace(self, subject: dict):
        if self.navigate_callback:
            self.navigate_callback("subject_workspace", subject["id"])


# ── Subject Dialog ────────────────────────────────────────────────────────────

class SubjectDialog(ctk.CTkToplevel):
    """Premium modal for creating or editing a subject."""

    def __init__(self, parent, title: str, subject_data: dict = None):
        super().__init__(parent)
        self.result = None
        self.subject_data = subject_data
        self.title(title)
        self.geometry("500x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        if subject_data:
            self._prefill(subject_data)

    def _field(self, parent, label: str, placeholder: str) -> ctk.CTkEntry:
        ctk.CTkLabel(
            parent, text=label,
            font=_font(FONT_SM), text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))
        entry = ctk.CTkEntry(
            parent, placeholder_text=placeholder, height=40,
            corner_radius=RADIUS_SM, border_width=1, border_color=BORDER,
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
        )
        entry.pack(fill="x", pady=(0, PAD_MD))
        return entry

    def _build(self):
        # Dialog header
        hdr = ctk.CTkFrame(self, fg_color=ACCENT, height=52, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="⊟  Subject Details",
            font=_bold(FONT_LG), text_color="#FFFFFF",
        ).pack(side="left", padx=PAD_LG, pady=PAD_MD)

        wrap = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0)
        wrap.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(wrap, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)

        ctk.CTkLabel(scroll, text="Subject Name *",
                     font=_font(FONT_SM), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self._name = ctk.CTkEntry(
            scroll, placeholder_text="e.g., Data Structures", height=40,
            corner_radius=RADIUS_SM, border_width=1, border_color=BORDER,
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_MUTED,
        )
        self._name.pack(fill="x", pady=(0, PAD_MD))

        self._code    = self._field(scroll, "Subject Code", "e.g., CS201")
        self._faculty = self._field(scroll, "Faculty Name", "e.g., Dr. Sharma")

        # Semester + credits row
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=(0, PAD_MD))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)

        sem_wrap = ctk.CTkFrame(row, fg_color="transparent")
        sem_wrap.grid(row=0, column=0, sticky="ew", padx=(0, PAD_SM))
        ctk.CTkLabel(sem_wrap, text="Semester",
                     font=_font(FONT_SM), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self._semester = ctk.CTkEntry(
            sem_wrap, placeholder_text="1–8", height=40, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER, fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_MUTED,
        )
        self._semester.pack(fill="x")

        cred_wrap = ctk.CTkFrame(row, fg_color="transparent")
        cred_wrap.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(cred_wrap, text="Credits",
                     font=_font(FONT_SM), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self._credits = ctk.CTkEntry(
            cred_wrap, placeholder_text="e.g., 4", height=40, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER, fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_MUTED,
        )
        self._credits.pack(fill="x")

        # Color picker
        ctk.CTkLabel(scroll, text="Accent Color",
                     font=_font(FONT_SM), text_color=TEXT_SECONDARY).pack(anchor="w", pady=(PAD_SM, 4))
        color_row = ctk.CTkFrame(scroll, fg_color="transparent")
        color_row.pack(anchor="w", pady=(0, PAD_MD))
        self._selected_color = SUBJECT_COLORS[0]
        self._color_btns: list[ctk.CTkButton] = []
        for c in SUBJECT_COLORS[:10]:
            b = ctk.CTkButton(
                color_row, text="", width=26, height=26, corner_radius=13,
                fg_color=c, hover_color=c, border_width=2,
                border_color=BORDER if c != self._selected_color else TEXT_PRIMARY,
                command=lambda col=c: self._pick_color(col),
            )
            b.pack(side="left", padx=2)
            self._color_btns.append(b)

        # Buttons
        btn_row = ctk.CTkFrame(wrap, fg_color="transparent")
        btn_row.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        ctk.CTkButton(
            btn_row, text="Cancel", height=40, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))

        ctk.CTkButton(
            btn_row, text="Save Subject", height=40, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=("#FFFFFF", "#FFFFFF"),
            font=_bold(FONT_MD), command=self._save,
        ).pack(side="right", fill="x", expand=True)

    def _pick_color(self, color: str):
        self._selected_color = color
        for btn in self._color_btns:
            btn.configure(border_color=TEXT_PRIMARY if btn.cget("fg_color") == color else BORDER)

    def _prefill(self, data: dict):
        self._name.insert(0, data.get("name", ""))
        self._code.insert(0, data.get("subject_code", "") or "")
        self._faculty.insert(0, data.get("faculty_name", "") or "")
        if data.get("semester"):
            self._semester.insert(0, str(data["semester"]))
        if data.get("credit"):
            self._credits.insert(0, str(data["credit"]))
        if data.get("color"):
            self._selected_color = data["color"]

    def _save(self):
        name = self._name.get().strip()
        if not name:
            self._name.configure(border_color=DANGER[1])
            return
        self._name.configure(border_color=BORDER)

        code    = self._code.get().strip() or None
        faculty = self._faculty.get().strip() or None
        sem_raw = self._semester.get().strip()
        cred_raw = self._credits.get().strip()

        try:
            semester = int(sem_raw) if sem_raw else None
        except ValueError:
            messagebox.showerror("Invalid Input", "Semester must be a number (1–8).")
            return

        try:
            credit = float(cred_raw) if cred_raw else None
        except ValueError:
            messagebox.showerror("Invalid Input", "Credits must be a number.")
            return

        self.result = {
            "name": name, "subject_code": code, "faculty_name": faculty,
            "semester": semester, "credit": credit, "color": self._selected_color,
        }
        self.destroy()
