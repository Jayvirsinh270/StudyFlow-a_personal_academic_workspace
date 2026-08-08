"""
Settings Module — Premium redesign for StudyFlow.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from database import (
    get_student_profile, create_student_profile, update_student_profile,
    get_setting, set_setting,
)
from database.backup_manager import export_full_backup, import_full_backup, export_attendance_csv
import shutil
import os
from pathlib import Path
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_CHIP, BG_HOVER, BG_INPUT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT, ACCENT_HOVER, BORDER,
    SUCCESS, DANGER,
    PAD_SM, PAD_MD, PAD_LG, RADIUS_SM, RADIUS_MD, RADIUS_LG,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL,
)


def _font(size=FONT_MD, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def _bold(size=FONT_MD) -> ctk.CTkFont:
    return _font(size, "bold")


def _bool_pref(value, default=False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def _section(parent, title: str, icon: str = "") -> ctk.CTkFrame:
    card = ctk.CTkFrame(
        parent, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
        border_width=1, border_color=BORDER,
    )
    card.pack(fill="x", pady=(0, PAD_MD))

    hdr = ctk.CTkFrame(card, fg_color="transparent")
    hdr.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, 0))
    if icon:
        ctk.CTkLabel(hdr, text=icon, font=_font(FONT_LG), text_color=ACCENT[1]).pack(side="left", padx=(0, PAD_SM))
    ctk.CTkLabel(
        hdr, text=title,
        font=_bold(FONT_LG), text_color=TEXT_PRIMARY,
    ).pack(side="left")
    ctk.CTkFrame(card, fg_color=BORDER, height=1).pack(fill="x", padx=PAD_LG, pady=(PAD_SM, 0))
    return card


class Settings(ctk.CTkFrame):
    """Premium settings view — student profile + app preferences + backup."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.profile_data = None
        self._build()
        self._load_profile()
        self._load_preferences()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Page title ────────────────────────────────────────────────────────
        title_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, PAD_LG))
        ctk.CTkLabel(
            title_frame, text="⊕  Settings",
            font=_bold(FONT_XL + 4), text_color=TEXT_PRIMARY,
        ).pack(side="left")
        ctk.CTkLabel(
            title_frame, text="Manage your profile, appearance, and data",
            font=_font(FONT_MD), text_color=TEXT_MUTED,
        ).pack(side="left", padx=(PAD_MD, 0))

        # ── Profile section ───────────────────────────────────────────────────
        profile_card = _section(scroll, "Student Profile", icon="⊗")
        form = ctk.CTkFrame(profile_card, fg_color="transparent")
        form.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_LG))

        self._hint_lbl = ctk.CTkLabel(
            form,
            text="Tell StudyFlow about yourself so the dashboard feels personal.",
            font=_font(FONT_SM), text_color=TEXT_MUTED, justify="left", wraplength=540,
        )
        self._hint_lbl.pack(anchor="w", pady=(0, PAD_MD))

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(fill="x", pady=(0, PAD_SM))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        self._name       = self._field(grid, "Full Name *",        "Your full name",         row=0, col=0)
        self._enrollment = self._field(grid, "Enrollment Number",  "e.g., 22CS001",          row=0, col=1)
        self._department = self._field(grid, "Department",         "e.g., Computer Science", row=1, col=0)
        self._semester   = self._field(grid, "Current Semester",   "1–8",                    row=1, col=1)

        self._save_btn = ctk.CTkButton(
            form, text="⊠  Save Profile",
            height=42, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=("#FFFFFF", "#FFFFFF"),
            font=_bold(FONT_MD),
            command=self._save_profile,
        )
        self._save_btn.pack(fill="x", pady=(PAD_SM, 0))

        # ── Appearance section ────────────────────────────────────────────────
        appear_card = _section(scroll, "Appearance", icon="☀")
        appear_inner = ctk.CTkFrame(appear_card, fg_color="transparent")
        appear_inner.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_LG))

        # Theme mode
        theme_row = ctk.CTkFrame(appear_inner, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, PAD_MD))

        theme_info = ctk.CTkFrame(theme_row, fg_color="transparent")
        theme_info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(theme_info, text="Appearance Mode",
                     font=_bold(FONT_MD), text_color=TEXT_PRIMARY).pack(anchor="w")
        self._theme_status = ctk.CTkLabel(
            theme_info, text="",
            font=_font(FONT_SM), text_color=TEXT_MUTED,
        )
        self._theme_status.pack(anchor="w")

        self._theme_switch = ctk.CTkSwitch(
            theme_row, text="Dark Mode",
            font=_font(FONT_MD),
            fg_color=BORDER, progress_color=ACCENT,
            command=self._toggle_theme,
        )
        self._theme_switch.pack(side="right")

        # Theme presets
        ctk.CTkLabel(appear_inner, text="Theme Presets",
                     font=_bold(FONT_SM), text_color=TEXT_PRIMARY).pack(anchor="w", pady=(PAD_SM, PAD_SM))

        presets_row = ctk.CTkFrame(appear_inner, fg_color="transparent")
        presets_row.pack(fill="x")

        presets = [
            ("Light",    "#F8FAFC", "#1E293B", "light"),
            ("Dark",     "#0F1117", "#F1F5F9", "dark"),
            ("Ocean",    "#060E1A", "#E0F2FE", "dark"),
            ("Forest",   "#0C130F", "#E8F5EA", "dark"),
            ("Midnight", "#080B14", "#E2E8F0", "dark"),
        ]
        for name, bg, fg, mode in presets:
            btn = ctk.CTkButton(
                presets_row,
                text=name, width=90, height=34, corner_radius=RADIUS_SM,
                fg_color=bg, hover_color=bg,
                text_color=fg, border_width=1, border_color=BORDER,
                font=_font(FONT_SM),
                command=lambda m=mode: self._apply_preset_theme(m),
            )
            btn.pack(side="left", padx=(0, PAD_SM))

        # ── Dashboard preferences ─────────────────────────────────────────────
        pref_card = _section(scroll, "Dashboard Preferences", icon="⊞")
        pref_inner = ctk.CTkFrame(pref_card, fg_color="transparent")
        pref_inner.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_LG))

        def _pref_row(parent, label: str, desc: str, attr: str):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=(0, PAD_MD))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(info, text=label, font=_bold(FONT_MD), text_color=TEXT_PRIMARY).pack(anchor="w")
            ctk.CTkLabel(info, text=desc, font=_font(FONT_SM), text_color=TEXT_MUTED).pack(anchor="w")

            sw = ctk.CTkSwitch(
                row, text="",
                fg_color=BORDER, progress_color=ACCENT,
                command=self._save_preferences,
            )
            sw.pack(side="right")
            setattr(self, attr, sw)

        _pref_row(pref_inner, "Show deadline reminders",
                  "Display urgent assignment and attendance alerts on the dashboard",
                  "_reminders_sw")
        _pref_row(pref_inner, "Show quick action buttons",
                  "Display shortcut buttons for common actions on the dashboard",
                  "_quick_actions_sw")

        # ── Backup section ────────────────────────────────────────────────────
        backup_card = _section(scroll, "Data Backup & Restore", icon="⊠")
        backup_inner = ctk.CTkFrame(backup_card, fg_color="transparent")
        backup_inner.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_LG))

        ctk.CTkLabel(
            backup_inner,
            text="Export a zip snapshot of all your data, or restore from a previous backup.",
            font=_font(FONT_SM), text_color=TEXT_MUTED, justify="left",
        ).pack(anchor="w", pady=(0, PAD_MD))

        btn_row = ctk.CTkFrame(backup_inner, fg_color="transparent")
        btn_row.pack(fill="x")
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)
        btn_row.grid_columnconfigure(2, weight=1)

        self._export_btn = ctk.CTkButton(
            btn_row, text="⬆  Export Backup",
            height=40, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=("#FFFFFF", "#FFFFFF"),
            font=_bold(FONT_MD),
            command=self._export_data,
        )
        self._export_btn.grid(row=0, column=0, sticky="ew", padx=(0, PAD_SM))

        self._import_btn = ctk.CTkButton(
            btn_row, text="⬇  Import Backup",
            height=40, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            font=_bold(FONT_MD),
            command=self._import_data,
        )
        self._import_btn.grid(row=0, column=1, sticky="ew", padx=(0, PAD_SM))

        self._reset_btn_backup = ctk.CTkButton(
            btn_row, text="✕  Reset All Data",
            height=40, corner_radius=RADIUS_SM,
            fg_color=("#FEE2E2", "#450A0A"), hover_color=("#FECACA", "#7F1D1D"),
            text_color=DANGER[0], font=_bold(FONT_MD),
            command=self._reset_data,
        )
        self._reset_btn_backup.grid(row=0, column=2, sticky="ew")

        # ── About ─────────────────────────────────────────────────────────────
        about_card = _section(scroll, "About StudyFlow", icon="ℹ")
        about_inner = ctk.CTkFrame(about_card, fg_color="transparent")
        about_inner.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_LG))

        ctk.CTkLabel(
            about_inner,
            text="StudyFlow v2.0  —  Your Personal Academic Workspace",
            font=_bold(FONT_MD), text_color=TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            about_inner,
            text="Built with Python + CustomTkinter  •  Designed for students",
            font=_font(FONT_SM), text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(4, 0))

    def _field(self, parent, label: str, placeholder: str,
               row: int = 0, col: int = 0) -> ctk.CTkEntry:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=col, sticky="ew",
                  padx=(0 if col else 0, PAD_SM if col == 0 else 0), pady=(0, PAD_MD))
        ctk.CTkLabel(wrap, text=label, font=_font(FONT_SM),
                     text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        entry = ctk.CTkEntry(
            wrap, placeholder_text=placeholder, height=40,
            corner_radius=RADIUS_SM, border_width=1, border_color=BORDER,
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_MUTED,
        )
        entry.pack(fill="x")
        return entry

    def _load_profile(self):
        self.profile_data = get_student_profile()
        if not self.profile_data:
            return
        for entry in (self._name, self._enrollment, self._department, self._semester):
            entry.delete(0, "end")
        self._name.insert(0, self.profile_data.get("name", "") or "")
        self._enrollment.insert(0, self.profile_data.get("enrollment_number", "") or "")
        self._department.insert(0, self.profile_data.get("department", "") or "")
        if self.profile_data.get("semester"):
            self._semester.insert(0, str(self.profile_data["semester"]))

    def _save_profile(self):
        name = self._name.get().strip()
        if not name:
            self._name.configure(border_color=DANGER[1])
            return
        self._name.configure(border_color=BORDER)

        enrollment = self._enrollment.get().strip() or None
        department = self._department.get().strip() or None
        sem_raw    = self._semester.get().strip()

        try:
            semester = int(sem_raw) if sem_raw else None
        except ValueError:
            self._semester.configure(border_color=DANGER[1])
            messagebox.showerror("Invalid Input", "Semester must be a number (1–8).")
            return
        self._semester.configure(border_color=BORDER)

        try:
            if self.profile_data:
                update_student_profile(
                    profile_id=self.profile_data["id"],
                    name=name, enrollment_number=enrollment,
                    department=department, semester=semester,
                )
            else:
                create_student_profile(
                    name=name, enrollment_number=enrollment,
                    department=department, semester=semester,
                )
            first = name.split()[0] if name.split() else name
            self._hint_lbl.configure(text=f"✓  Profile saved for {first}. Welcome!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {e}")
            return

        self._load_profile()
        self._save_btn.configure(text="✓  Saved!", fg_color=SUCCESS[1])
        self.after(2000, lambda: self._save_btn.configure(text="⊠  Save Profile", fg_color=ACCENT))

    def _load_preferences(self):
        mode = get_setting("theme_mode")
        if mode == "dark":
            self._theme_switch.select()
            self._theme_status.configure(text="Dark mode is active")
        else:
            self._theme_switch.deselect()
            self._theme_status.configure(text="Light mode is active")

        if _bool_pref(get_setting("show_reminders"), True):
            self._reminders_sw.select()
        else:
            self._reminders_sw.deselect()

        if _bool_pref(get_setting("show_quick_actions"), True):
            self._quick_actions_sw.select()
        else:
            self._quick_actions_sw.deselect()

    def _toggle_theme(self):
        if self._theme_switch.get():
            ctk.set_appearance_mode("dark")
            set_setting("theme_mode", "dark")
            self._theme_status.configure(text="Dark mode is active")
        else:
            ctk.set_appearance_mode("light")
            set_setting("theme_mode", "light")
            self._theme_status.configure(text="Light mode is active")

    def _apply_preset_theme(self, mode: str):
        ctk.set_appearance_mode(mode)
        set_setting("theme_mode", mode)
        if mode == "dark":
            self._theme_switch.select()
            self._theme_status.configure(text="Dark mode is active")
        else:
            self._theme_switch.deselect()
            self._theme_status.configure(text="Light mode is active")

    def _save_preferences(self):
        set_setting("show_reminders", bool(self._reminders_sw.get()))
        set_setting("show_quick_actions", bool(self._quick_actions_sw.get()))

    def _export_data(self):
        from datetime import datetime
        user_data_dir = Path(__file__).parent.parent.parent / "UserData"
        if not user_data_dir.exists():
            messagebox.showerror("Error", "UserData folder not found.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = filedialog.asksaveasfilename(
            title="Save Backup", defaultextension=".zip",
            initialfile=f"StudyFlow_Backup_{ts}.zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
        )
        if not dest:
            return
        try:
            shutil.make_archive(dest.replace(".zip", ""), "zip", user_data_dir.parent, "UserData")
            messagebox.showinfo("Backup Created", f"Backup saved to:\n{dest}")
            self._export_btn.configure(text="✓  Backup Complete!", fg_color=SUCCESS[1])
            self.after(2500, lambda: self._export_btn.configure(text="⬆  Export Backup", fg_color=ACCENT))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {e}")

    def _import_data(self):
        import zipfile
        from datetime import datetime
        user_data_dir = Path(__file__).parent.parent.parent / "UserData"
        src = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
        )
        if not src:
            return
        if not messagebox.askyesno("Confirm Import",
                                   "This will replace all current data with the backup. Continue?"):
            return
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            if user_data_dir.exists():
                shutil.copytree(user_data_dir, user_data_dir.parent / f"UserData_pre_import_{ts}")
            with zipfile.ZipFile(src, "r") as z:
                z.extractall(user_data_dir.parent)
            messagebox.showinfo("Import Complete", "Data imported. Your previous data was backed up.")
            self._import_btn.configure(text="✓  Import Complete!", fg_color=SUCCESS[1])
            self.after(2500, lambda: self._import_btn.configure(text="⬇  Import Backup", fg_color=BG_CHIP))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}")

    def _reset_data(self):
        if not messagebox.askyesno("Reset All Data",
                                   "This will permanently erase all your study data. This cannot be undone.\n\nAre you absolutely sure?"):
            return
        try:
            from database.database import db_manager
            conn = db_manager.get_connection()
            cur  = conn.cursor()
            for tbl in ["settings", "student_profile", "subjects", "notes",
                        "subject_files", "attendance", "assignments",
                        "timetable", "cgpa_records", "calendar_events", "study_tasks"]:
                cur.execute(f"DELETE FROM {tbl}")
            conn.commit()
            conn.close()
            messagebox.showinfo("Reset Complete",
                                "All data cleared. Restart the app to start fresh.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset data: {e}")
