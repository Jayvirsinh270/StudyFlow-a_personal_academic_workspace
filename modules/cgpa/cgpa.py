"""
CGPA Calculator Module
Semester GPA input, CGPA calculation, and progress charts.
"""

import customtkinter as ctk
from tkinter import messagebox
from database import add_cgpa_record, get_cgpa_records, calculate_cgpa, update_cgpa_record, delete_cgpa_record
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_INPUT, BG_CHIP, BG_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    ACCENT, ACCENT_HOVER, SUCCESS, WARNING, DANGER,
    BORDER, PAD_SM, PAD_MD, PAD_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    gpa_color,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL, FONT_2XL,
)


def _font(size=FONT_MD, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

def _bold(size=FONT_MD) -> ctk.CTkFont:
    return _font(size, "bold")


class CGPA(ctk.CTkFrame):
    """CGPA calculator with semester records and overall CGPA display."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self._create_content()
        self._load_cgpa_data()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _create_content(self):
        # ── Overall CGPA banner ──────────────────────────────────────────────
        banner = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        banner.pack(fill="x", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        ctk.CTkLabel(
            banner, text="⊙  CGPA Calculator",
            font=_bold(FONT_XL),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_MD))

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        # Big number
        self.cgpa_label = ctk.CTkLabel(
            inner, text="0.00",
            font=_bold(64),
            text_color=ACCENT[1],
        )
        self.cgpa_label.pack(side="left")

        # Right side stats
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True, padx=(PAD_LG, 0))

        self.avg_gpa_label = ctk.CTkLabel(
            right, text="Avg GPA: 0.00",
            font=_font(FONT_MD), text_color=TEXT_SECONDARY,
        )
        self.avg_gpa_label.pack(anchor="e", pady=(PAD_SM, PAD_MD))

        self.cgpa_progress = ctk.CTkProgressBar(
            right, height=14, corner_radius=7,
            fg_color=BG_INPUT, progress_color=ACCENT,
        )
        self.cgpa_progress.set(0)
        self.cgpa_progress.pack(fill="x")

        grade_info = ctk.CTkLabel(
            right,
            text="Scale: 0.0 – 4.0   |   Good ≥ 3.5   |   Pass ≥ 2.0",
            font=_font(FONT_XS), text_color=TEXT_MUTED,
        )
        grade_info.pack(anchor="e", pady=(PAD_SM, 0))

        # ── Semester Records ──────────────────────────────────────────────────
        records_card = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        records_card.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_SM))

        rh = ctk.CTkFrame(records_card, fg_color="transparent")
        rh.pack(fill="x", padx=PAD_LG, pady=(PAD_LG, PAD_MD))

        ctk.CTkLabel(
            rh, text="⊟  Semester Records",
            font=_bold(FONT_LG),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            rh, text="＋  Add Semester",
            width=140, height=34, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT, font=_bold(FONT_SM),
            command=self._show_add_semester_dialog,
        ).pack(side="right")

        self.records_frame = ctk.CTkScrollableFrame(records_card, fg_color="transparent")
        self.records_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))

        # ── GPA Chart ─────────────────────────────────────────────────────────
        chart_card = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        chart_card.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        ctk.CTkLabel(
            chart_card, text="GPA Progress",
            font=_bold(FONT_LG),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_MD))

        self.chart_container = ctk.CTkFrame(chart_card, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))

        self._show_records_list()

    # ── Data ────────────────────────────────────────────────────────────────

    def _load_cgpa_data(self):
        cgpa = calculate_cgpa()
        records = get_cgpa_records()

        if cgpa:
            col = gpa_color(cgpa)
            self.cgpa_label.configure(text=f"{cgpa:.2f}", text_color=col)
            self.cgpa_progress.configure(progress_color=col)
            self.cgpa_progress.set(cgpa / 4.0)
        else:
            self.cgpa_label.configure(text="0.00", text_color=ACCENT[1])
            self.cgpa_progress.set(0)

        if records:
            avg = sum(r.get("gpa", 0) for r in records) / len(records)
            self.avg_gpa_label.configure(text=f"Avg GPA: {avg:.2f}")
        else:
            self.avg_gpa_label.configure(text="Avg GPA: 0.00")

        self._update_chart()

    def _update_chart(self):
        for w in self.chart_container.winfo_children():
            w.destroy()

        records = get_cgpa_records()
        if not records:
            ctk.CTkLabel(
                self.chart_container,
                text="Add semester records to see your GPA progress chart.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=30)
            return

        records.sort(key=lambda x: x.get("semester", 0))
        semesters = [f"Sem {r.get('semester', '')}" for r in records]
        gpas      = [r.get("gpa", 0) for r in records]

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(8, 3), dpi=96)
        bg = "#1F2533"
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)

        accent_hex = "#4F8EF7"
        ax.plot(semesters, gpas, marker="o", linewidth=2.5, markersize=8,
                color=accent_hex, markerfacecolor=accent_hex, zorder=5)
        ax.fill_between(range(len(semesters)), gpas, alpha=0.15, color=accent_hex)

        ax.axhline(y=4.0, color="#22C55E", linestyle="--", alpha=0.5, linewidth=1, label="Max (4.0)")
        ax.axhline(y=2.0, color="#F59E0B", linestyle="--", alpha=0.5, linewidth=1, label="Pass (2.0)")

        ax.set_xticks(range(len(semesters)))
        ax.set_xticklabels(semesters)
        ax.set_ylim(0, 4.5)
        ax.set_ylabel("GPA", color="#8899B4", fontsize=9)
        ax.tick_params(axis="x", colors="#8899B4", labelsize=8)
        ax.tick_params(axis="y", colors="#8899B4", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#283040")
        ax.grid(True, alpha=0.15, color="#283040")
        ax.legend(loc="upper right", fontsize=7, facecolor="#252E3E", edgecolor="#283040")

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    def _show_records_list(self):
        for w in self.records_frame.winfo_children():
            w.destroy()

        records = get_cgpa_records()
        if not records:
            ctk.CTkLabel(
                self.records_frame,
                text="No semester records yet. Click '＋  Add Semester' to start.",
                font=_font(FONT_MD), text_color=TEXT_MUTED,
            ).pack(pady=50)
        else:
            for rec in records:
                self._create_record_card(rec).pack(fill="x", pady=PAD_SM)

    # ── Card ─────────────────────────────────────────────────────────────────

    def _create_record_card(self, record: dict) -> ctk.CTkFrame:
        gpa   = record.get("gpa", 0.0)
        col   = gpa_color(gpa)

        card = ctk.CTkFrame(self.records_frame, fg_color=BG_CARD, corner_radius=RADIUS_MD, height=68)
        card.pack_propagate(False)
        card.bind("<Enter>", lambda e, c=card: c.configure(fg_color=BG_HOVER))
        card.bind("<Leave>", lambda e, c=card: c.configure(fg_color=BG_CARD))

        # Color accent strip
        ctk.CTkFrame(card, fg_color=col, width=4, corner_radius=0).pack(side="left", fill="y")

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=PAD_MD, pady=PAD_SM)

        ctk.CTkLabel(
            info, text=f"Semester {record.get('semester', 'N/A')}",
            font=_bold(FONT_MD),
            text_color=TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=f"GPA: {gpa:.2f}   ·   Credits: {record.get('credits', 0)}",
            font=_font(FONT_SM), text_color=TEXT_SECONDARY, anchor="w",
        ).pack(anchor="w")

        # GPA dot
        ctk.CTkLabel(info, text="●", font=_font(FONT_XL), text_color=col).pack(side="right")

        acts = ctk.CTkFrame(card, fg_color="transparent")
        acts.pack(side="right", padx=PAD_MD, pady=PAD_SM)

        ctk.CTkButton(
            acts, text="Edit", width=58, height=26, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            font=_font(FONT_SM),
            command=lambda r=record: self._show_edit_semester_dialog(r),
        ).pack(side="left", padx=(0, PAD_SM))

        ctk.CTkButton(
            acts, text="Delete", width=58, height=26, corner_radius=RADIUS_SM,
            fg_color=DANGER, hover_color=("#B91C1C", "#DC2626"),
            text_color=TEXT_ON_ACCENT, font=_font(FONT_SM),
            command=lambda r=record: self._delete_record(r),
        ).pack(side="right")

        return card

    # ── Actions ──────────────────────────────────────────────────────────────

    def _show_add_semester_dialog(self):
        dialog = SemesterDialog(self, "Add Semester")
        self.wait_window(dialog)
        if dialog.result:
            try:
                add_cgpa_record(**dialog.result)
                self._show_records_list()
                self._load_cgpa_data()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def _show_edit_semester_dialog(self, record: dict):
        dialog = SemesterDialog(self, "Edit Semester", record)
        self.wait_window(dialog)
        if dialog.result:
            try:
                update_cgpa_record(record_id=record["id"], **dialog.result)
                self._show_records_list()
                self._load_cgpa_data()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def _delete_record(self, record: dict):
        if messagebox.askyesno("Delete", f"Delete Semester {record['semester']}?"):
            try:
                delete_cgpa_record(record["id"])
                self._show_records_list()
                self._load_cgpa_data()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))


class SemesterDialog(ctk.CTkToplevel):
    """Dialog for adding / editing a semester record."""

    def __init__(self, parent, title: str, record_data: dict = None):
        super().__init__(parent)
        self.result = None
        self.record_data = record_data
        self.title(title)
        self.geometry("420x360")
        self.minsize(380, 320)
        self.resizable(False, True)
        self.transient(parent)
        self.grab_set()

        # Grid: row 0 = header, row 1 = scrollable form, row 2 = button bar
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_content()
        if record_data:
            self._load_data(record_data)

    def _create_content(self):
        # ── Coloured header ───────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=ACCENT, height=50, corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr_text = "✎  Edit Semester" if self.record_data else "＋  Add Semester"
        ctk.CTkLabel(
            hdr, text=hdr_text,
            font=_bold(FONT_LG), text_color="#FFFFFF",
        ).pack(side="left", padx=PAD_LG, pady=PAD_MD)

        # ── Scrollable form body ──────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_SURFACE)
        scroll.grid(row=1, column=0, sticky="nsew")

        inner = ctk.CTkFrame(scroll, fg_color="transparent")
        inner.pack(fill="x", padx=PAD_LG, pady=PAD_LG)

        _lkw = dict(font=_bold(FONT_SM), text_color=TEXT_PRIMARY, anchor="w")
        _ekw = dict(height=42, corner_radius=RADIUS_SM, border_width=1,
                    border_color=BORDER, fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
                    placeholder_text_color=TEXT_MUTED)

        # Semester field
        ctk.CTkLabel(inner, text="Semester  *", **_lkw).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            inner, text="Enter the semester number (e.g. 1, 2, 3 …)",
            font=_font(FONT_XS), text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, PAD_SM))
        self.semester_entry = ctk.CTkEntry(
            inner, placeholder_text="e.g., 1", **_ekw)
        self.semester_entry.pack(fill="x", pady=(0, PAD_MD))

        # GPA field
        ctk.CTkLabel(inner, text="GPA  *  (0.0 – 4.0)", **_lkw).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            inner, text="Semester grade point average on a 4.0 scale",
            font=_font(FONT_XS), text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, PAD_SM))
        self.gpa_entry = ctk.CTkEntry(
            inner, placeholder_text="e.g., 3.5", **_ekw)
        self.gpa_entry.pack(fill="x", pady=(0, PAD_MD))

        # Credits field
        ctk.CTkLabel(inner, text="Credits  *", **_lkw).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            inner, text="Total credit hours for this semester (e.g. 20)",
            font=_font(FONT_XS), text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, PAD_SM))
        self.credits_entry = ctk.CTkEntry(
            inner, placeholder_text="e.g., 20", **_ekw)
        self.credits_entry.pack(fill="x", pady=(0, PAD_SM))

        # ── Fixed button bar (always visible, never scrolls away) ─────────────
        btn_bar = ctk.CTkFrame(
            self, fg_color=BG_SURFACE,
            border_width=1, border_color=BORDER, corner_radius=0,
        )
        btn_bar.grid(row=2, column=0, sticky="ew")

        btn_inner = ctk.CTkFrame(btn_bar, fg_color="transparent")
        btn_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        ctk.CTkButton(
            btn_inner, text="Cancel",
            height=40, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            font=_font(FONT_MD),
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))

        ctk.CTkButton(
            btn_inner,
            text="✎  Update" if self.record_data else "＋  Save Semester",
            height=40, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            font=_bold(FONT_MD),
            command=self._save,
        ).pack(side="right", fill="x", expand=True)

    def _load_data(self, rec: dict):
        if rec.get("semester"):
            self.semester_entry.insert(0, str(rec["semester"]))
        if rec.get("gpa"):
            self.gpa_entry.insert(0, str(rec["gpa"]))
        if rec.get("credits"):
            self.credits_entry.insert(0, str(rec["credits"]))

    def _save(self):
        semester = self.semester_entry.get().strip()
        gpa      = self.gpa_entry.get().strip()
        credits  = self.credits_entry.get().strip()

        err_col = DANGER[1]
        ok_col  = BORDER
        self.semester_entry.configure(border_color=err_col if not semester else ok_col)
        self.gpa_entry.configure(border_color=err_col if not gpa else ok_col)
        self.credits_entry.configure(border_color=err_col if not credits else ok_col)

        if not (semester and gpa and credits):
            return
        try:
            sem_i = int(semester)
            gpa_f = float(gpa)
            cred_i = int(credits)
            if not (0 <= gpa_f <= 4.0):
                messagebox.showerror("Error", "GPA must be 0.0 – 4.0")
                return
            if cred_i <= 0:
                messagebox.showerror("Error", "Credits must be > 0")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return

        self.semester_entry.configure(border_color=ok_col)
        self.gpa_entry.configure(border_color=ok_col)
        self.credits_entry.configure(border_color=ok_col)

        self.result = {"semester": sem_i, "gpa": gpa_f, "credits": cred_i}
        self.destroy()
