"""
Attendance Module
Centralized attendance tracking across all subjects with bulk marking.
"""

import customtkinter as ctk
from tkinter import messagebox
from database import get_subjects, get_attendance, update_attendance, calculate_attendance_percentage
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_INPUT, BG_HOVER, BG_CHIP,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    ACCENT, ACCENT_HOVER, SUCCESS, WARNING, DANGER,
    BORDER, PAD_SM, PAD_MD, PAD_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    attendance_color,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL,
)


def _font(size: int = FONT_MD, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def _bold(size: int = FONT_MD) -> ctk.CTkFont:
    return _font(size, "bold")


class Attendance(ctk.CTkFrame):
    """Centralized attendance view with all subjects' attendance data."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.subjects_data = get_subjects()
        self._create_content()
        self._load_attendance()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _create_content(self):
        # Header bar
        header = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        header.pack(fill="x", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        ctk.CTkLabel(
            header, text="◎  Attendance Overview",
            font=_bold(FONT_XL),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=PAD_LG, pady=PAD_LG)

        self.bulk_btn = ctk.CTkButton(
            header, text="✓  Mark All Present",
            font=_bold(FONT_MD),
            width=160, height=34, corner_radius=RADIUS_SM,
            fg_color=SUCCESS, hover_color=("#15803D", "#16A34A"),
            text_color=TEXT_ON_ACCENT,
            command=self._bulk_mark_present,
        )
        self.bulk_btn.pack(side="right", padx=PAD_LG, pady=PAD_LG)

        # Summary strip
        summary = ctk.CTkFrame(self, fg_color=BG_CHIP, corner_radius=RADIUS_MD)
        summary.pack(fill="x", padx=PAD_LG, pady=(0, PAD_SM))

        self.stats_label = ctk.CTkLabel(
            summary, text="Loading…",
            font=_font(FONT_SM),
            text_color=TEXT_SECONDARY,
        )
        self.stats_label.pack(anchor="w", padx=PAD_LG, pady=PAD_SM)

        # Scrollable cards container
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))

    # ── Data ────────────────────────────────────────────────────────────────

    def _load_attendance(self):
        for w in self.container.winfo_children():
            w.destroy()

        if not self.subjects_data:
            ctk.CTkLabel(
                self.container,
                text="No subjects added yet. Add subjects to start tracking attendance.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=60)
            self.stats_label.configure(text="No subjects to track")
            return

        total_subjects = len(self.subjects_data)
        subjects_with_data = total_percentage = low_count = 0

        for subject in self.subjects_data:
            attendance = get_attendance(subject["id"])
            percentage = calculate_attendance_percentage(subject["id"])
            if attendance:
                subjects_with_data += 1
                total_percentage += percentage
                if percentage < 75:
                    low_count += 1
            self._create_card(subject, attendance, percentage)

        avg = (total_percentage / subjects_with_data) if subjects_with_data else 0
        self.stats_label.configure(
            text=(
                f"{total_subjects} subject{'s' if total_subjects != 1 else ''} · "
                f"Average: {avg:.1f}% · "
                f"Below 75 %: {low_count}"
            )
        )

    def _create_card(self, subject: dict, attendance, percentage: float):
        """Render one subject attendance card."""
        color = attendance_color(percentage)
        status_text = (
            "Good" if percentage >= 75
            else "Low" if percentage >= 60
            else "Critical"
        )

        card = ctk.CTkFrame(self.container, fg_color=BG_SURFACE, corner_radius=RADIUS_MD)
        card.pack(fill="x", pady=PAD_SM)

        # Hover highlight effect
        def _on_enter(e, c=card):
            c.configure(fg_color=BG_HOVER)
        def _on_leave(e, c=card):
            c.configure(fg_color=BG_SURFACE)
        card.bind("<Enter>", _on_enter)
        card.bind("<Leave>", _on_leave)

        # Accent left-border
        accent_bar = ctk.CTkFrame(card, fg_color=color, width=4, corner_radius=0)
        accent_bar.pack(side="left", fill="y")

        # ── Subject info ──────────────────────────────────────────────────
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(PAD_MD, PAD_SM), pady=PAD_MD)

        # Title row with icon
        title_row = ctk.CTkFrame(info, fg_color="transparent")
        title_row.pack(anchor="w", fill="x")

        ctk.CTkLabel(
            title_row, text="▪",
            font=_bold(FONT_LG),
            text_color=color,
        ).pack(side="left", padx=(0, PAD_SM))

        ctk.CTkLabel(
            title_row, text=subject["name"],
            font=_bold(FONT_LG),
            text_color=TEXT_PRIMARY, anchor="w",
        ).pack(side="left")

        if subject.get("faculty_name"):
            ctk.CTkLabel(
                info, text=f"Faculty · {subject['faculty_name']}",
                font=_font(FONT_SM), text_color=TEXT_MUTED, anchor="w",
            ).pack(anchor="w", pady=(2, 0))

        if attendance:
            total = attendance.get("total_lectures", 0)
            present = attendance.get("present_lectures", 0)
            ctk.CTkLabel(
                info, text=f"{present} / {total} classes",
                font=_font(FONT_SM), text_color=TEXT_SECONDARY, anchor="w",
            ).pack(anchor="w", pady=(4, 0))

            # Progress bar
            bar = ctk.CTkProgressBar(
                info, height=6, corner_radius=3,
                fg_color=BG_INPUT, progress_color=color,
            )
            bar.set(min(percentage / 100, 1.0))
            bar.pack(anchor="w", fill="x", pady=(6, 0))

        # ── Stats + buttons ───────────────────────────────────────────────
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=PAD_MD, pady=PAD_MD)

        ctk.CTkLabel(
            right, text=f"{percentage:.1f}%",
            font=_bold(26),
            text_color=color,
        ).pack()

        ctk.CTkLabel(
            right, text=status_text,
            font=_font(FONT_XS),
            text_color=color,
        ).pack(pady=(0, PAD_SM))

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row, text="✓  Present",
            width=88, height=28, corner_radius=RADIUS_SM,
            fg_color=SUCCESS, hover_color=("#15803D", "#16A34A"),
            text_color=TEXT_ON_ACCENT, font=_bold(FONT_SM),
            command=lambda sid=subject["id"]: self._mark(sid, "present"),
        ).pack(side="left", padx=(0, PAD_SM))

        ctk.CTkButton(
            btn_row, text="✕  Absent",
            width=88, height=28, corner_radius=RADIUS_SM,
            fg_color=DANGER, hover_color=("#B91C1C", "#DC2626"),
            text_color=TEXT_ON_ACCENT, font=_bold(FONT_SM),
            command=lambda sid=subject["id"]: self._mark(sid, "absent"),
        ).pack(side="left")

    # ── Actions ─────────────────────────────────────────────────────────────

    def _mark(self, subject_id: int, status: str):
        att = get_attendance(subject_id)
        if status == "present":
            new_present = (att.get("present_lectures", 0) + 1) if att else 1
            new_total   = (att.get("total_lectures", 0)   + 1) if att else 1
            new_absent  = att.get("absent_lectures", 0)        if att else 0
        else:
            new_absent  = (att.get("absent_lectures", 0) + 1) if att else 1
            new_total   = (att.get("total_lectures", 0)  + 1) if att else 1
            new_present = att.get("present_lectures", 0)       if att else 0

        update_attendance(
            subject_id=subject_id,
            total_lectures=new_total,
            present_lectures=new_present,
            absent_lectures=new_absent,
        )
        self._load_attendance()

    def _bulk_mark_present(self):
        if not self.subjects_data:
            messagebox.showinfo("Info", "No subjects to mark attendance for.")
            return
        if messagebox.askyesno(
            "Confirm",
            f"Mark all {len(self.subjects_data)} subjects as present for today?",
        ):
            for subject in self.subjects_data:
                self._mark(subject["id"], "present")
