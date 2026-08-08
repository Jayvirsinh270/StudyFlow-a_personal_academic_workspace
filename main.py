"""
StudyFlow - Your Personal Academic Workspace
Main Application Entry Point — Premium redesigned edition
"""

import customtkinter as ctk
import sys
import os
from utils.logger import get_logger

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize logger
logger = get_logger()

# Import components
from components.sidebar import Sidebar
from components.header import Header
from modules.dashboard.dashboard import Dashboard
from modules.settings.settings import Settings
from modules.subjects.subjects import Subjects
from modules.subjects.workspace import SubjectWorkspace
from modules.timetable.timetable import Timetable
from modules.cgpa.cgpa import CGPA
from modules.productivity.pomodoro import PomodoroTimer
from modules.assignments.assignments import Assignments
from modules.documents.documents import Documents
from modules.calendar.calendar import CalendarView
from modules.attendance.attendance import Attendance
from modules.planner.planner import Planner
from components.quick_search import QuickSearchDialog
from utils.theme import BG_MAIN, BG_SIDEBAR, ACCENT

# Import database
from database import initialize_database, get_setting, set_setting, get_student_profile, get_subjects


def should_show_onboarding(profile, subjects, onboarding_completed):
    """Return True when a first-time user should see onboarding guidance."""
    if onboarding_completed:
        return False
    if not profile:
        return True
    if profile.get("name") and str(profile.get("name")).strip():
        return not bool(subjects)
    return True


class StudyFlowApp(ctk.CTk):
    """Main application class for StudyFlow — Premium Edition"""

    def __init__(self):
        super().__init__()

        logger.info("Starting StudyFlow application")

        try:
            initialize_database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            from tkinter import messagebox
            messagebox.showerror("Database Error", "Failed to initialize database.")
            self.destroy()
            return

        # Configure window
        self.title("StudyFlow — Your Personal Academic Workspace")
        self.geometry("1360x780")
        self.minsize(1100, 640)
        self.configure(fg_color=BG_MAIN)

        # Load theme preference
        theme_mode = get_setting("theme_mode")
        if theme_mode:
            ctk.set_appearance_mode(theme_mode)
        else:
            ctk.set_appearance_mode("dark")
            set_setting("theme_mode", "dark")

        ctk.set_default_color_theme("blue")

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # State
        self.current_page = None
        self.content_frame = None
        self.page_titles = {
            "dashboard":         "Dashboard",
            "subjects":          "Subjects",
            "assignments":       "Assignments",
            "attendance":        "Attendance",
            "planner":           "Planner",
            "timetable":         "Timetable",
            "calendar":          "Calendar",
            "pomodoro":          "Focus Timer",
            "documents":         "Documents",
            "cgpa":              "CGPA Calculator",
            "settings":          "Settings",
            "subject_workspace": "Subject Workspace",
        }

        self.create_main_container()
        self._setup_keyboard_shortcuts()
        self.after(250, self._show_onboarding_if_needed)

    def create_main_container(self):
        """Create the main application container."""
        # Header
        self.header = Header(self, self.navigate_to)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Sidebar
        self.sidebar = Sidebar(self, self.navigate_to)
        self.sidebar.grid(row=1, column=0, sticky="nsew")

        # Content area
        self.content_area = ctk.CTkFrame(self, fg_color=BG_MAIN)
        self.content_area.grid(row=1, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Start at dashboard
        self.navigate_to("dashboard")

    def _show_onboarding_if_needed(self):
        """Show a lightweight welcome guide to first-time users."""
        if not self.winfo_exists():
            return

        profile = get_student_profile()
        subjects = get_subjects() or []
        onboarding_completed = bool(get_setting("onboarding_completed"))

        if not should_show_onboarding(profile, subjects, onboarding_completed):
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Welcome to StudyFlow")
        dialog.geometry("500x360")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Dialog header
        hdr = ctk.CTkFrame(dialog, fg_color=ACCENT, height=56, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="⊞  Welcome to StudyFlow",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left", padx=24, pady=16)

        body = ctk.CTkFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            body,
            text="Set up your study space in two quick steps and make the most of your semester.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#64748B", "#94A3B8"),
            wraplength=450, justify="left",
        ).pack(anchor="w", pady=(0, 20))

        options = [
            ("⊟  Add your first subject",           "subjects"),
            ("⊗  Set your profile and preferences",  "settings"),
            ("⊞  Start with the dashboard",          "dashboard"),
        ]

        for label, page_id in options:
            btn = ctk.CTkButton(
                body,
                text=label,
                height=42, corner_radius=10,
                fg_color=("transparent", "transparent"),
                border_width=1, border_color=ACCENT,
                text_color=ACCENT,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                hover_color=("#EFF6FF", "#1E2740"),
                anchor="w",
                command=lambda target=page_id: self._finish_onboarding(dialog, target),
            )
            btn.pack(fill="x", pady=5)

        ctk.CTkButton(
            body,
            text="Finish setup later",
            height=38,
            fg_color=("transparent", "transparent"),
            text_color=("#94A3B8", "#475569"),
            hover_color=("#F1F5F9", "#1E2130"),
            command=lambda: self._finish_onboarding(dialog, None),
        ).pack(fill="x", pady=(10, 0))

    def _finish_onboarding(self, dialog, target_page=None):
        """Persist onboarding choice and navigate."""
        set_setting("onboarding_completed", True)
        if dialog and dialog.winfo_exists():
            dialog.destroy()
        if target_page:
            self.navigate_to(target_page)

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for navigation."""
        self.bind("<Alt-1>", lambda e: self.navigate_to("dashboard"))
        self.bind("<Alt-2>", lambda e: self.navigate_to("subjects"))
        self.bind("<Alt-3>", lambda e: self.navigate_to("assignments"))
        self.bind("<Alt-4>", lambda e: self.navigate_to("attendance"))
        self.bind("<Alt-5>", lambda e: self.navigate_to("planner"))
        self.bind("<Alt-6>", lambda e: self.navigate_to("calendar"))
        self.bind("<Alt-7>", lambda e: self.navigate_to("pomodoro"))
        self.bind("<Alt-8>", lambda e: self.navigate_to("documents"))
        self.bind("<Alt-9>", lambda e: self.navigate_to("cgpa"))
        self.bind("<Alt-0>", lambda e: self.navigate_to("settings"))
        self.bind("<Control-s>", lambda e: self._handle_quick_save())
        self.bind("<Control-f>", lambda e: self._focus_search())
        self.bind("<Control-k>", lambda e: self._focus_search())
        self.bind("<Escape>", lambda e: self._handle_escape())

    def _handle_quick_save(self):
        if self.current_page == "settings":
            if hasattr(self.content_frame, '_save_profile'):
                self.content_frame._save_profile()

    def _focus_search(self):
        QuickSearchDialog(self, navigate_callback=self.navigate_to)

    def _handle_escape(self):
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkToplevel):
                widget.destroy()
                return
        if self.current_page != "dashboard":
            self.navigate_to("dashboard")

    def navigate_to(self, page_id: str, subject_id: int = None):
        """Navigate to a specific page with smooth transition."""
        # Clear current content
        if self.content_frame:
            self.content_frame.destroy()

        # Update header
        self.header.set_page_title(self.page_titles.get(page_id, page_id.title()))

        # Sync sidebar
        if self.sidebar and hasattr(self.sidebar, "_set_active_page"):
            active_page = "subjects" if page_id == "subject_workspace" else page_id
            self.sidebar._set_active_page(active_page)

        # Content padding
        pad = dict(padx=20, pady=20)

        # Create content
        if page_id == "dashboard":
            self.content_frame = Dashboard(self.content_area, self.navigate_to)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "subjects":
            self.content_frame = Subjects(self.content_area, self.navigate_to)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "subject_workspace" and subject_id:
            self.content_frame = SubjectWorkspace(self.content_area, subject_id)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "assignments":
            self.content_frame = Assignments(self.content_area)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "attendance":
            self.content_frame = Attendance(self.content_area)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "documents":
            self.content_frame = Documents(self.content_area)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "planner":
            self.content_frame = Planner(self.content_area)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "timetable":
            self.content_frame = Timetable(self.content_area)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "cgpa":
            self.content_frame = CGPA(self.content_area)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "calendar":
            self.content_frame = CalendarView(self.content_area)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "pomodoro":
            self.content_frame = PomodoroTimer(self.content_area)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        elif page_id == "settings":
            self.content_frame = Settings(self.content_area)
            self.content_frame.grid(row=0, column=0, sticky="nsew", **pad)
        else:
            self._create_placeholder_page(page_id)

        self.current_page = page_id

    def _create_placeholder_page(self, page_id: str):
        """Create a placeholder page for unimplemented modules."""
        from utils.theme import BG_SURFACE, BORDER, TEXT_PRIMARY, TEXT_MUTED, RADIUS_LG
        self.content_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        card = ctk.CTkFrame(
            self.content_frame,
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_LG,
            border_width=1, border_color=BORDER,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card,
            text=f"⊟  {page_id.title()} Module",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(padx=60, pady=(40, 10))

        ctk.CTkLabel(
            card,
            text="This module will be available in the next update.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT_MUTED,
        ).pack(pady=(0, 40))


def main():
    """Main entry point."""
    app = StudyFlowApp()
    app.mainloop()


if __name__ == "__main__":
    main()
