"""
StudyFlow Quick Search & Command Palette Modal (Ctrl + K)
Allows fast cross-module searching across notes, subjects, assignments, documents, tasks, and calendar events.
"""

import customtkinter as ctk
from database import (
    get_subjects, get_notes, get_assignments, 
    get_subject_files, get_study_tasks, get_calendar_events
)


class QuickSearchDialog(ctk.CTkToplevel):
    """Floating global search modal triggered via Ctrl+K or search bar"""

    def __init__(self, parent, navigate_callback=None):
        super().__init__(parent)

        self.navigate_callback = navigate_callback
        self.title("Quick Search (Ctrl + K)")
        self.geometry("600x480")
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_ui()
        self._perform_search()

    def _create_ui(self):
        # Search input header
        search_frame = ctk.CTkFrame(self, fg_color="#2D2D30", height=60, corner_radius=10)
        search_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        search_label = ctk.CTkLabel(
            search_frame, text="🔍", font=ctk.CTkFont(size=18), text_color="#4F8EF7"
        )
        search_label.pack(side="left", padx=(15, 5))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search notes, subjects, assignments, tasks, files...",
            height=40,
            border_width=0,
            fg_color="transparent",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=14)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self._perform_search())
        self.search_entry.focus()

        # Results scrollable list
        self.results_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

    def _perform_search(self):
        query = self.search_entry.get().strip().lower()

        # Clear existing result cards
        for child in self.results_frame.winfo_children():
            child.destroy()

        results = []

        # 1. Subjects
        subjects = get_subjects() or []
        for s in subjects:
            if not query or query in s.get("name", "").lower() or query in (s.get("code") or "").lower():
                results.append({
                    "category": "Subject",
                    "title": s.get("name"),
                    "subtitle": f"Code: {s.get('code', 'N/A')} | Credits: {s.get('credits', 'N/A')}",
                    "action": ("subjects", s.get("id"))
                })

        # 2. Notes
        for s in subjects:
            notes = get_notes(s["id"]) or []
            for n in notes:
                title = n.get("title", "")
                content = n.get("content", "")
                if not query or query in title.lower() or query in content.lower():
                    results.append({
                        "category": "Note",
                        "title": title,
                        "subtitle": f"Subject: {s['name']}",
                        "action": ("subject_workspace", s["id"])
                    })

        # 3. Assignments
        assignments = get_assignments() or []
        for a in assignments:
            title = a.get("title", "")
            desc = a.get("description", "") or ""
            if not query or query in title.lower() or query in desc.lower():
                results.append({
                    "category": "Assignment",
                    "title": title,
                    "subtitle": f"Due: {a.get('due_date', 'N/A')} | Priority: {a.get('priority', 'N/A')}",
                    "action": ("assignments", None)
                })

        # 4. Tasks
        tasks = get_study_tasks() or []
        for t in tasks:
            title = t.get("title", "")
            if not query or query in title.lower():
                results.append({
                    "category": "Task",
                    "title": title,
                    "subtitle": f"Status: {t.get('status', 'pending')}",
                    "action": ("planner", None)
                })

        # 5. Calendar Events
        events = get_calendar_events() or []
        for e in events:
            title = e.get("title", "")
            if not query or query in title.lower():
                results.append({
                    "category": "Calendar Event",
                    "title": title,
                    "subtitle": f"Date: {e.get('event_date', 'N/A')} ({e.get('event_type', 'personal')})",
                    "action": ("calendar", None)
                })

        if not results:
            no_res = ctk.CTkLabel(
                self.results_frame,
                text="No matching items found.",
                font=ctk.CTkFont(size=13),
                text_color="#C5C5C5"
            )
            no_res.pack(pady=30)
            return

        # Render top 20 results
        for res in results[:20]:
            self._create_result_row(res)

    def _create_result_row(self, res: dict):
        card = ctk.CTkFrame(self.results_frame, fg_color="#1E1E1E", corner_radius=8)
        card.pack(fill="x", pady=4)

        cat_colors = {
            "Subject": "#4F8EF7",
            "Note": "#FFC107",
            "Assignment": "#EB5757",
            "Task": "#27AE60",
            "Calendar Event": "#F2994A"
        }

        cat_badge = ctk.CTkLabel(
            card,
            text=res["category"],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=cat_colors.get(res["category"], "#4F8EF7"),
            width=100,
            anchor="w"
        )
        cat_badge.pack(side="left", padx=12, pady=10)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=8)

        t_lbl = ctk.CTkLabel(
            info,
            text=res["title"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FFFFFF",
            anchor="w"
        )
        t_lbl.pack(anchor="w")

        s_lbl = ctk.CTkLabel(
            info,
            text=res["subtitle"],
            font=ctk.CTkFont(size=11),
            text_color="#C5C5C5",
            anchor="w"
        )
        s_lbl.pack(anchor="w")

        open_btn = ctk.CTkButton(
            card,
            text="Open",
            width=60,
            height=28,
            corner_radius=6,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            command=lambda action=res["action"]: self._navigate(action)
        )
        open_btn.pack(side="right", padx=12)

    def _navigate(self, action):
        page_id, subject_id = action
        self.destroy()
        if self.navigate_callback:
            if page_id == "subject_workspace" and subject_id:
                self.navigate_callback(page_id, subject_id=subject_id)
            else:
                self.navigate_callback(page_id)
