"""
Subject Workspace
Individual subject dashboard with tabs for Overview, Notes, Files, Attendance, Assignments, and Resources
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
from database import get_subject_by_id, get_notes, get_subject_files, get_attendance, calculate_attendance_percentage, get_assignments, add_subject_file, delete_subject_file, update_attendance, add_assignment, update_assignment, delete_assignment, duplicate_note, update_note, delete_note
from modules.notes.editor import NotesEditor
from utils.file_manager import file_manager
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_INPUT, BG_CHIP, BG_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    ACCENT, ACCENT_HOVER, SUCCESS, WARNING, DANGER,
    BORDER, PAD_SM, PAD_MD, PAD_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    attendance_color, priority_color,
)


def build_note_preview(content: str | None, max_length: int = 70) -> str:
    """Create a short preview for note cards from raw note content."""
    if not content:
        return "No content yet"

    cleaned = " ".join(str(content).split())
    if not cleaned:
        return "No content yet"

    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip() + "..."


class SubjectWorkspace(ctk.CTkFrame):
    """Subject workspace with tabbed interface"""
    
    def __init__(self, master, subject_id: int, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="transparent")
        self.subject_id = subject_id
        self.subject_data = None
        
        self._create_content()
        self._load_subject_data()
    
    def _create_content(self):
        """Create workspace content"""
        # Subject header
        self.header_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Subject name
        self.subject_name_label = ctk.CTkLabel(
            self.header_frame,
            text="Subject Name",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.subject_name_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        # Subject details
        self.subject_details_label = ctk.CTkLabel(
            self.header_frame,
            text="Subject Code • Faculty Name",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_SECONDARY,
        )
        self.subject_details_label.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Tab buttons
        tabs_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        tabs_frame.pack(fill="x", padx=20, pady=10)
        
        self.tab_buttons = {}
        tabs = ["Overview", "Notes", "Files", "Attendance", "Assignments", "Resources"]
        
        for i, tab in enumerate(tabs):
            btn = ctk.CTkButton(
                tabs_frame,
                text=tab,
                width=120,
                height=40,
                corner_radius=RADIUS_SM,
                fg_color="transparent",
                text_color=TEXT_SECONDARY,
                hover_color=BG_HOVER,
                font=ctk.CTkFont(size=13),
                command=lambda t=tab: self._switch_tab(t),
            )
            btn.pack(side="left", padx=5, pady=10)
            self.tab_buttons[tab] = btn
        
        # Content area for tabs
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Initialize with Overview tab
        self.current_tab = "Overview"
        self._switch_tab("Overview")
    
    def _load_subject_data(self):
        """Load subject data from database"""
        self.subject_data = get_subject_by_id(self.subject_id)
        
        if self.subject_data:
            self.subject_name_label.configure(text=self.subject_data.get('name', 'Unknown'))
            
            details = []
            if self.subject_data.get('subject_code'):
                details.append(self.subject_data['subject_code'])
            if self.subject_data.get('faculty_name'):
                details.append(self.subject_data['faculty_name'])
            if self.subject_data.get('semester'):
                details.append(f"Sem {self.subject_data['semester']}")
            
            self.subject_details_label.configure(text=" • ".join(details) if details else "")
    
    def _switch_tab(self, tab_name: str):
        """Switch to a different tab"""
        self.current_tab = tab_name
        
        # Update tab button styles
        for tab, btn in self.tab_buttons.items():
            if tab == tab_name:
                btn.configure(fg_color=ACCENT, text_color=TEXT_ON_ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Load tab content
        if tab_name == "Overview":
            self._load_overview()
        elif tab_name == "Notes":
            self._load_notes()
        elif tab_name == "Files":
            self._load_files()
        elif tab_name == "Attendance":
            self._load_attendance()
        elif tab_name == "Assignments":
            self._load_assignments()
        elif tab_name == "Resources":
            self._load_resources()
    
    def _load_overview(self):
        """Load overview tab"""
        overview_frame = ctk.CTkFrame(self.content_frame, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        overview_frame.pack(fill="both", expand=True)
        
        title_label = ctk.CTkLabel(
            overview_frame,
            text="Subject Overview",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 15))
        
        # Quick stats
        stats_frame = ctk.CTkFrame(overview_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Notes count
        notes = get_notes(self.subject_id)
        self._create_stat_card(stats_frame, "Notes", str(len(notes)), "📝", 0)
        
        # Files count
        files = get_subject_files(self.subject_id)
        self._create_stat_card(stats_frame, "Files", str(len(files)), "📁", 1)
        
        # Attendance
        attendance = get_attendance(self.subject_id)
        if attendance:
            percentage = calculate_attendance_percentage(self.subject_id)
            self._create_stat_card(stats_frame, "Attendance", f"{percentage:.1f}%", "✅", 2)
        else:
            self._create_stat_card(stats_frame, "Attendance", "N/A", "✅", 2)
        
        # Assignments
        assignments = get_assignments(self.subject_id)
        pending = len([a for a in assignments if a.get('status') == 'pending'])
        self._create_stat_card(stats_frame, "Pending", str(pending), "📋", 3)
        
        # Info section
        info_frame = ctk.CTkFrame(overview_frame, fg_color=BG_CARD, corner_radius=RADIUS_MD)
        info_frame.pack(fill="x", padx=20, pady=(0, 20))

        quick_tip = ctk.CTkLabel(
            info_frame,
            text="Quick tip: add a note after each class and upload important materials before the next lecture.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
            wraplength=640,
            justify="left",
        )
        quick_tip.pack(anchor="w", padx=20, pady=(15, 10))
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="Subject Information",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        info_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        if self.subject_data:
            info_text = []
            if self.subject_data.get('faculty_name'):
                info_text.append(f"Faculty: {self.subject_data['faculty_name']}")
            if self.subject_data.get('semester'):
                info_text.append(f"Semester: {self.subject_data['semester']}")
            if self.subject_data.get('credit'):
                info_text.append(f"Credits: {self.subject_data['credit']}")
            
            for line in info_text:
                line_label = ctk.CTkLabel(
                    info_frame,
                    text=line,
                    font=ctk.CTkFont(size=13),
                    text_color=TEXT_SECONDARY,
                )
                line_label.pack(anchor="w", padx=20, pady=2)

        action_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        action_row.pack(fill="x", padx=20, pady=(8, 15))

        note_action = ctk.CTkButton(
            action_row,
            text="Open Notes",
            width=110,
            height=34,
            corner_radius=RADIUS_SM,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            command=lambda: self._switch_tab("Notes"),
        )
        note_action.pack(side="left", padx=(0, 8))

        file_action = ctk.CTkButton(
            action_row,
            text="Manage Files",
            width=110,
            height=34,
            corner_radius=RADIUS_SM,
            fg_color=BG_CHIP,
            hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY,
            command=lambda: self._switch_tab("Files"),
        )
        file_action.pack(side="left")
    
    def _load_notes(self):
        """Load notes tab"""
        notes_frame = ctk.CTkFrame(self.content_frame, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        notes_frame.pack(fill="both", expand=True)
        
        # Header with title and add button
        header_frame = ctk.CTkFrame(notes_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Notes",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.pack(side="left")
        
        add_note_btn = ctk.CTkButton(
            header_frame,
            text="+ New Note",
            width=120,
            height=34,
            corner_radius=RADIUS_SM,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._create_new_note,
        )
        add_note_btn.pack(side="right")

        toolbar_frame = ctk.CTkFrame(notes_frame, fg_color=BG_CARD, corner_radius=RADIUS_SM)
        toolbar_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.note_search_entry = ctk.CTkEntry(
            toolbar_frame,
            placeholder_text="Search notes...",
            height=36,
            width=220,
            corner_radius=RADIUS_SM,
            border_width=0,
            fg_color="transparent",
            text_color=TEXT_PRIMARY,
        )
        self.note_search_entry.pack(side="left", padx=10, pady=8)
        self.note_search_entry.bind("<KeyRelease>", lambda e: self._filter_notes(self.note_search_entry.get()))

        self.note_sort_var = ctk.StringVar(value="updated_at")
        sort_menu = ctk.CTkOptionMenu(
            toolbar_frame,
            values=["updated_at", "title"],
            variable=self.note_sort_var,
            width=120,
            height=36,
            corner_radius=RADIUS_SM,
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=BG_HOVER,
            dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
            command=lambda _: self._refresh_notes_list(),
        )
        sort_menu.pack(side="right", padx=10, pady=8)
        
        # Notes list or editor
        self.notes_list_frame = ctk.CTkFrame(notes_frame, fg_color="transparent")
        self.notes_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self._show_notes_list()
    
    def _show_notes_list(self):
        """Show list of notes"""
        self._refresh_notes_list()

    def _refresh_notes_list(self):
        """Refresh the notes list with current search and sort settings."""
        for widget in self.notes_list_frame.winfo_children():
            widget.destroy()

        notes = get_notes(self.subject_id, sort_by=self.note_sort_var.get() if hasattr(self, 'note_sort_var') else 'updated_at')
        search_text = self.note_search_entry.get().strip().lower() if hasattr(self, 'note_search_entry') else ''

        if search_text:
            notes = [note for note in notes if search_text in note.get('title', '').lower() or search_text in note.get('content', '').lower()]

        if not notes:
            empty_label = ctk.CTkLabel(
                self.notes_list_frame,
                text="No notes created yet. Click '+ New Note' to start writing.",
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED,
            )
            empty_label.pack(pady=(50, 10))
            help_btn = ctk.CTkButton(
                self.notes_list_frame,
                text="Create First Note",
                width=160,
                height=34,
                corner_radius=RADIUS_SM,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                text_color=TEXT_ON_ACCENT,
                command=self._create_new_note,
            )
            help_btn.pack()
        else:
            for note in notes:
                note_card = self._create_note_card(note)
                note_card.pack(fill="x", pady=5)
    
    def _create_new_note(self):
        """Create a new note and open editor"""
        # Create notes editor in a new window
        self.notes_editor = NotesEditor(self.winfo_toplevel(), self.subject_id, on_close_callback=self._refresh_notes_list)
    
    def _edit_note(self, note_id: int):
        """Edit an existing note"""
        # Create notes editor with existing note in a new window
        self.notes_editor = NotesEditor(self.winfo_toplevel(), self.subject_id, note_id, on_close_callback=self._refresh_notes_list)
        
    def _read_note(self, note_id: int):
        """Read a note in read mode"""
        from modules.notes.reader import NoteReader
        NoteReader(self.winfo_toplevel(), note_id)
    
    def _filter_notes(self, search_text: str):
        """Filter notes based on the current search text."""
        self._refresh_notes_list()

    def _toggle_pin_note(self, note: dict):
        """Toggle note pin state."""
        try:
            update_note(note['id'], is_pinned=not bool(note.get('is_pinned')))
            self._refresh_notes_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update note: {str(e)}")

    def _duplicate_note(self, note: dict):
        """Create a duplicate of the selected note."""
        try:
            duplicate_id = duplicate_note(note['id'])
            if duplicate_id:
                self._refresh_notes_list()
            else:
                messagebox.showerror("Error", "Could not duplicate the note.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to duplicate note: {str(e)}")

    def _delete_note(self, note: dict):
        """Delete a note with confirmation."""
        if messagebox.askyesno("Delete Note", f"Are you sure you want to delete '{note.get('title', 'Untitled')}'?"):
            try:
                delete_note(note['id'])
                self._refresh_notes_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete note: {str(e)}")

    def _load_files(self):
        """Load files tab"""
        files_frame = ctk.CTkFrame(self.content_frame, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        files_frame.pack(fill="both", expand=True)
        
        # Header with title and upload button
        header_frame = ctk.CTkFrame(files_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Files",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.pack(side="left")
        
        upload_btn = ctk.CTkButton(
            header_frame,
            text="+ Upload File",
            width=120,
            height=34,
            corner_radius=RADIUS_SM,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._upload_file,
        )
        upload_btn.pack(side="right")
        
        # Search and controls bar
        controls_frame = ctk.CTkFrame(files_frame, fg_color=BG_CARD, corner_radius=RADIUS_SM)
        controls_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.file_search_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="Search files...",
            height=36,
            width=220,
            corner_radius=RADIUS_SM,
            border_width=0,
            fg_color="transparent",
            text_color=TEXT_PRIMARY,
        )
        self.file_search_entry.pack(side="left", padx=10, pady=8)
        self.file_search_entry.bind("<KeyRelease>", lambda e: self._filter_files(self.file_search_entry.get()))

        self.file_sort_var = ctk.StringVar(value="name")
        sort_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=["name", "type", "size"],
            variable=self.file_sort_var,
            width=100,
            height=36,
            corner_radius=RADIUS_SM,
            fg_color=BG_INPUT,
            button_color=BG_INPUT,
            button_hover_color=BG_HOVER,
            dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
            command=lambda _: self._refresh_files_list(),
        )
        sort_menu.pack(side="right", padx=10, pady=8)

        self.file_view_var = ctk.StringVar(value="list")
        view_toggle = ctk.CTkSegmentedButton(
            controls_frame,
            values=["list", "grid"],
            variable=self.file_view_var,
            command=lambda _: self._refresh_files_list()
        )
        view_toggle.pack(side="right", padx=(0, 10), pady=8)
        
        # Files list
        self.files_list_frame = ctk.CTkFrame(files_frame, fg_color="transparent")
        self.files_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self._show_files_list()
    
    def _show_files_list(self, files=None):
        """Show list of files"""
        self._refresh_files_list(files)

    def _refresh_files_list(self, files=None):
        """Refresh the files list using the current sort and view settings."""
        for widget in self.files_list_frame.winfo_children():
            widget.destroy()

        if files is None:
            files = get_subject_files(self.subject_id)

        if hasattr(self, 'file_sort_var'):
            files = file_manager.sort_files(files, sort_by=self.file_sort_var.get())

        if not files:
            empty_label = ctk.CTkLabel(
                self.files_list_frame,
                text="No files uploaded yet. Click '+ Upload File' to add study materials.",
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED,
            )
            empty_label.pack(pady=(50, 10))
            help_btn = ctk.CTkButton(
                self.files_list_frame,
                text="Upload First File",
                width=160,
                height=34,
                corner_radius=RADIUS_SM,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                text_color=TEXT_ON_ACCENT,
                command=self._upload_file,
            )
            help_btn.pack()
        else:
            for file in files:
                file_card = self._create_file_card(file)
                if getattr(self, 'file_view_var', None) and self.file_view_var.get() == 'grid':
                    file_card.pack(side="left", padx=5, pady=5)
                else:
                    file_card.pack(fill="x", pady=5)
    
    def _upload_file(self):
        """Upload a file to the subject"""
        file_path = filedialog.askopenfilename(
            title="Select a file to upload",
            filetypes=[
                ("All Files", "*.*"),
                ("PDF Files", "*.pdf"),
                ("Images", "*.png *.jpg *.jpeg *.gif"),
                ("Documents", "*.doc *.docx *.txt"),
                ("Presentations", "*.ppt *.pptx")
            ]
        )
        
        if file_path:
            try:
                import os
                file_name = os.path.basename(file_path)
                file_type = file_name.split('.')[-1].upper() if '.' in file_name else 'UNKNOWN'
                
                # Save file to subject directory
                saved_path = file_manager.save_file(self.subject_id, file_path, file_name)
                
                # Add to database
                add_subject_file(
                    subject_id=self.subject_id,
                    file_name=file_name,
                    file_path=saved_path,
                    file_type=file_type,
                    file_size=file_manager.get_file_size_formatted(saved_path)
                )
                
                # Refresh files list
                self._show_files_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload file: {str(e)}")
    
    def _filter_files(self, search_text: str):
        """Filter files based on search text"""
        if not search_text:
            self._show_files_list()
            return
        
        files = get_subject_files(self.subject_id)
        filtered = [
            f for f in files
            if search_text.lower() in f.get('file_name', '').lower()
            or search_text.lower() in f.get('file_type', '').lower()
        ]
        self._show_files_list(filtered)
    
    def _open_file(self, file: dict):
        """Open a file with the default application"""
        file_path = file.get('file_path')
        if file_path and file_manager.open_file(file_path):
            pass  # File opened successfully
        else:
            messagebox.showerror("Error", "Could not open the file.")
    
    def _rename_file(self, file: dict):
        """Rename a file"""
        from tkinter import simpledialog
        new_name = simpledialog.askstring(
            "Rename File",
            "Enter new file name:",
            initialvalue=file.get('file_name', '')
        )
        
        if new_name and new_name != file.get('file_name'):
            old_path = file.get('file_path')
            if file_manager.rename_file(old_path, new_name):
                # Update database (would need update function in queries)
                # For now, just refresh the list
                self._show_files_list()
    
    def _delete_file(self, file: dict):
        """Delete a file with confirmation"""
        if messagebox.askyesno(
            "Delete File",
            f"Are you sure you want to delete '{file.get('file_name', 'Unknown')}'?"
        ):
            try:
                file_path = file.get('file_path')
                if file_manager.delete_file(file_path):
                    delete_subject_file(file['id'])
                    self._show_files_list()
                else:
                    messagebox.showerror("Error", "Could not delete the file.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {str(e)}")
    
    def _get_attendance_color(self, percentage: float) -> str:
        """Return the visual color for the attendance percentage."""
        if percentage >= 75:
            return "#4CAF50"
        if percentage >= 60:
            return "#FFC107"
        return "#F44336"

    def _is_attendance_warning(self, percentage: float) -> bool:
        """Determine whether attendance is below the warning threshold."""
        return percentage < 75

    def _format_percentage(self, percentage: float) -> str:
        """Format percentage values for the UI."""
        return f"{percentage:.1f}%"

    def _load_attendance(self):
        """Load attendance tab"""
        attendance_frame = ctk.CTkFrame(self.content_frame, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        attendance_frame.pack(fill="both", expand=True)
        
        # Header with title and mark attendance button
        header_frame = ctk.CTkFrame(attendance_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Attendance",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.pack(side="left")
        
        mark_btn = ctk.CTkButton(
            header_frame,
            text="+ Mark Attendance",
            width=140,
            height=34,
            corner_radius=RADIUS_SM,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._mark_attendance,
        )
        mark_btn.pack(side="right")
        
        attendance = get_attendance(self.subject_id)
        
        if not attendance:
            empty_label = ctk.CTkLabel(
                attendance_frame,
                text="No attendance data recorded. Click '+ Mark Attendance' to start tracking.",
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED,
            )
            empty_label.pack(pady=50)
        else:
            percentage = calculate_attendance_percentage(self.subject_id)
            
            # Attendance overview card
            overview_card = ctk.CTkFrame(attendance_frame, fg_color=BG_CARD, corner_radius=RADIUS_MD)
            overview_card.pack(fill="x", padx=20, pady=(0, 15))
            
            # Percentage display
            percentage_frame = ctk.CTkFrame(overview_card, fg_color="transparent")
            percentage_frame.pack(fill="x", padx=20, pady=(20, 15))
            
            color = attendance_color(percentage)
            percentage_label = ctk.CTkLabel(
                percentage_frame,
                text=self._format_percentage(percentage),
                font=ctk.CTkFont(size=48, weight="bold"),
                text_color=color
            )
            percentage_label.pack(side="left")

            circular_frame = ctk.CTkFrame(percentage_frame, fg_color="transparent")
            circular_frame.pack(side="right", fill="both", expand=True, padx=(20, 0))

            circular_canvas = ctk.CTkFrame(circular_frame, width=110, height=110, fg_color="#1E1E1E", corner_radius=55)
            circular_canvas.pack(pady=(10, 0))
            circular_canvas.pack_propagate(False)
            circular_label = ctk.CTkLabel(
                circular_canvas,
                text=self._format_percentage(percentage),
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=color
            )
            circular_label.place(relx=0.5, rely=0.5, anchor="center")

            progress_frame = ctk.CTkFrame(percentage_frame, fg_color="transparent")
            progress_frame.pack(side="right", fill="both", expand=True, padx=(20, 0))

            progress_bar = ctk.CTkProgressBar(
                progress_frame,
                width=200,
                height=20,
                corner_radius=10,
                progress_color=color
            )
            progress_bar.set(percentage / 100)
            progress_bar.pack(pady=(10, 0))

            if self._is_attendance_warning(percentage):
                warning_label = ctk.CTkLabel(
                    overview_card,
                    text="⚠ Attendance below 75%",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=WARNING[1],
                )
                warning_label.pack(anchor="w", padx=20, pady=(0, 15))
            
            # Details
            details_frame = ctk.CTkFrame(overview_card, fg_color="transparent")
            details_frame.pack(fill="x", padx=20, pady=(0, 20))
            
            total_label = ctk.CTkLabel(
                details_frame,
                text=f"Total Lectures: {attendance['total_lectures']}",
                font=ctk.CTkFont(size=13),
                text_color=TEXT_SECONDARY,
            )
            total_label.pack(side="left", padx=(0, 20))
            
            present_label = ctk.CTkLabel(
                details_frame,
                text=f"Present: {attendance['present_lectures']}",
                font=ctk.CTkFont(size=13),
                text_color=SUCCESS[1],
            )
            present_label.pack(side="left", padx=(0, 20))
            
            absent_label = ctk.CTkLabel(
                details_frame,
                text=f"Absent: {attendance['absent_lectures']}",
                font=ctk.CTkFont(size=13),
                text_color=DANGER[1],
            )
            absent_label.pack(side="right")
    
    def _mark_attendance(self):
        """Mark attendance for today's lecture"""
        from tkinter import simpledialog
        
        # Ask for status
        status = messagebox.askyesno(
            "Mark Attendance",
            "Mark today's lecture as Present?"
        )
        
        if status is not None:
            # Get today's date
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Update attendance
            attendance = get_attendance(self.subject_id)
            
            if attendance:
                if status:
                    new_present = attendance['present_lectures'] + 1
                    new_total = attendance['total_lectures'] + 1
                else:
                    new_present = attendance['present_lectures']
                    new_total = attendance['total_lectures'] + 1
                
                update_attendance(
                    self.subject_id,
                    total_lectures=new_total,
                    present_lectures=new_present
                )
            else:
                # Create new attendance record
                if status:
                    update_attendance(self.subject_id, total_lectures=1, present_lectures=1)
                else:
                    update_attendance(self.subject_id, total_lectures=1, present_lectures=0)
            
            # Refresh attendance display
            self._switch_tab("Attendance")
    
    def _get_assignment_priority_color(self, priority: str) -> str:
        """Return a color for an assignment priority."""
        return {"high": "#F44336", "medium": "#FFC107", "low": "#4CAF50"}.get(priority, "#C5C5C5")

    def _get_assignment_status_color(self, status: str) -> str:
        """Return a color for an assignment status."""
        return "#4CAF50" if status == "completed" else "#FFC107"

    def _sort_assignments(self, assignments: list, sort_by: str = "due_date") -> list:
        """Sort assignments for display."""
        if sort_by == "priority":
            priority_order = {"high": 0, "medium": 1, "low": 2}
            return sorted(assignments, key=lambda item: (priority_order.get(item.get('priority'), 99), item.get('due_date') or ""))
        if sort_by == "status":
            return sorted(assignments, key=lambda item: (item.get('status') != "pending", item.get('due_date') or ""))
        return sorted(assignments, key=lambda item: (item.get('due_date') or "", item.get('title') or ""))

    def _filter_assignments(self, assignments: list, priority: str = None, status: str = None) -> list:
        """Filter assignments by priority and status."""
        filtered = assignments
        if priority:
            filtered = [item for item in filtered if item.get('priority') == priority]
        if status:
            filtered = [item for item in filtered if item.get('status') == status]
        return filtered

    def _load_assignments(self):
        """Load assignments tab"""
        assignments_frame = ctk.CTkFrame(self.content_frame, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        assignments_frame.pack(fill="both", expand=True)
        
        # Header with title and add button
        header_frame = ctk.CTkFrame(assignments_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Assignments",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.pack(side="left")
        
        add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add Assignment",
            width=140,
            height=34,
            corner_radius=RADIUS_SM,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._show_add_assignment_dialog,
        )
        add_btn.pack(side="right")

        controls_frame = ctk.CTkFrame(assignments_frame, fg_color=BG_CARD, corner_radius=RADIUS_SM)
        controls_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.assignment_priority_var = ctk.StringVar(value="")
        self.assignment_status_var = ctk.StringVar(value="")
        self.assignment_sort_var = ctk.StringVar(value="due_date")

        priority_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=["", "low", "medium", "high"],
            variable=self.assignment_priority_var,
            width=110, height=36, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=BG_HOVER, dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
            command=lambda _: self._show_assignments_list(),
        )
        priority_menu.pack(side="left", padx=10, pady=8)

        status_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=["", "pending", "completed"],
            variable=self.assignment_status_var,
            width=120, height=36, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=BG_HOVER, dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
            command=lambda _: self._show_assignments_list(),
        )
        status_menu.pack(side="left", padx=10, pady=8)

        sort_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=["due_date", "priority", "status"],
            variable=self.assignment_sort_var,
            width=120, height=36, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=BG_HOVER, dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
            command=lambda _: self._show_assignments_list(),
        )
        sort_menu.pack(side="right", padx=10, pady=8)
        
        # Assignments list
        self.assignments_list_frame = ctk.CTkFrame(assignments_frame, fg_color="transparent")
        self.assignments_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self._show_assignments_list()
    
    def _show_assignments_list(self):
        """Show list of assignments"""
        # Clear assignments list frame
        for widget in self.assignments_list_frame.winfo_children():
            widget.destroy()
        
        assignments = self._filter_assignments(
            get_assignments(self.subject_id),
            priority=self.assignment_priority_var.get() if hasattr(self, 'assignment_priority_var') else None,
            status=self.assignment_status_var.get() if hasattr(self, 'assignment_status_var') else None
        )
        assignments = self._sort_assignments(assignments, sort_by=self.assignment_sort_var.get() if hasattr(self, 'assignment_sort_var') else 'due_date')
        
        if not assignments:
            empty_label = ctk.CTkLabel(
                self.assignments_list_frame,
                text="No assignments added yet. Click '+ Add Assignment' to create one.",
                font=ctk.CTkFont(size=13),
                text_color=TEXT_MUTED,
            )
            empty_label.pack(pady=(50, 10))
            help_btn = ctk.CTkButton(
                self.assignments_list_frame,
                text="Add First Assignment",
                width=180,
                height=34,
                corner_radius=RADIUS_SM,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                text_color=TEXT_ON_ACCENT,
                command=self._show_add_assignment_dialog,
            )
            help_btn.pack()
        else:
            for assignment in assignments:
                assignment_card = self._create_assignment_card(assignment)
                assignment_card.pack(fill="x", pady=5)
    
    def _show_add_assignment_dialog(self):
        """Show dialog to add a new assignment"""
        dialog = AssignmentDialog(self, "Add Assignment")
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                add_assignment(
                    subject_id=self.subject_id,
                    title=dialog.result['title'],
                    description=dialog.result.get('description'),
                    due_date=dialog.result.get('due_date'),
                    priority=dialog.result.get('priority'),
                    status=dialog.result.get('status')
                )
                self._show_assignments_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add assignment: {str(e)}")
    
    def _show_edit_assignment_dialog(self, assignment: dict):
        """Show dialog to edit an existing assignment"""
        dialog = AssignmentDialog(self, "Edit Assignment", assignment)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                update_assignment(
                    assignment_id=assignment['id'],
                    title=dialog.result['title'],
                    description=dialog.result.get('description'),
                    due_date=dialog.result.get('due_date'),
                    priority=dialog.result.get('priority'),
                    status=dialog.result.get('status')
                )
                self._show_assignments_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update assignment: {str(e)}")
    
    def _delete_assignment(self, assignment: dict):
        """Delete an assignment with confirmation"""
        if messagebox.askyesno(
            "Delete Assignment",
            f"Are you sure you want to delete '{assignment['title']}'?"
        ):
            try:
                delete_assignment(assignment['id'])
                self._show_assignments_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete assignment: {str(e)}")
    
    def _toggle_assignment_status(self, assignment: dict):
        """Toggle assignment status between pending and completed"""
        try:
            new_status = "completed" if assignment.get('status') == 'pending' else "pending"
            update_assignment(
                assignment_id=assignment['id'],
                status=new_status
            )
            self._show_assignments_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update assignment status: {str(e)}")
    
    def _load_resources(self):
        """Load resources tab"""
        resources_frame = ctk.CTkFrame(self.content_frame, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        resources_frame.pack(fill="both", expand=True)
        
        title_label = ctk.CTkLabel(
            resources_frame,
            text="Resources",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 15))
        
        empty_label = ctk.CTkLabel(
            resources_frame,
            text="Resources section coming soon.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        )
        empty_label.pack(pady=50)
    
    def _create_stat_card(self, parent, title: str, value: str, icon: str, column: int):
        """Create a statistics card"""
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=RADIUS_SM)
        card.grid(row=0, column=column, padx=5, sticky="nsew")
        parent.grid_columnconfigure(column, weight=1)
        
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=24)
        )
        icon_label.pack(pady=(15, 5))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=ACCENT[1],
        )
        value_label.pack(pady=(0, 5))
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        )
        title_label.pack(pady=(0, 15))
    
    def _create_note_card(self, note: dict) -> ctk.CTkFrame:
        """Create a note card with pin, duplicate, and quick actions."""
        card = ctk.CTkFrame(
            self.notes_list_frame,
            fg_color=BG_CHIP if note.get('is_pinned') else BG_CARD,
            corner_radius=RADIUS_SM,
            height=80,
        )
        card.pack_propagate(False)

        card.bind("<Enter>", lambda e: card.configure(fg_color=BG_HOVER))
        card.bind("<Leave>", lambda e: card.configure(fg_color=BG_CHIP if note.get('is_pinned') else BG_CARD))

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)

        title_text = f"📌 {note.get('title', 'Untitled')}" if note.get('is_pinned') else note.get('title', 'Untitled')
        name_label = ctk.CTkLabel(
            info_frame,
            text=title_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        name_label.pack(anchor="w", pady=(0, 3))

        preview_text = build_note_preview(note.get('content'))
        preview_label = ctk.CTkLabel(
            info_frame,
            text=preview_text,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
            anchor="w",
            wraplength=320,
            justify="left",
        )
        preview_label.pack(anchor="w", pady=(0, 3))

        date_label = ctk.CTkLabel(
            info_frame,
            text=f"Last modified: {note.get('updated_at', '')[:10]}",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        date_label.pack(anchor="w")

        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(side="right", padx=10, pady=10)
        
        primary_actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        primary_actions_frame.pack(side="right", padx=10, pady=25)
        
        read_btn = ctk.CTkButton(
            primary_actions_frame,
            text="Read Mode",
            width=80,
            height=30,
            corner_radius=RADIUS_SM,
            fg_color=SUCCESS,
            hover_color=("#15803D", "#16A34A"),
            text_color=TEXT_ON_ACCENT,
            command=lambda n=note['id']: self._read_note(n),
        )
        read_btn.pack(side="left", padx=5)
        
        edit_btn = ctk.CTkButton(
            primary_actions_frame,
            text="Edit Mode",
            width=80,
            height=30,
            corner_radius=RADIUS_SM,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            command=lambda n=note['id']: self._edit_note(n),
        )
        edit_btn.pack(side="left", padx=5)

        pin_btn = ctk.CTkButton(
            actions_frame,
            text="📌" if not note.get('is_pinned') else "📍",
            width=36,
            height=28,
            corner_radius=6,
            fg_color="#4F8EF7" if not note.get('is_pinned') else "#4CAF50",
            hover_color="#3A7AD9",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12),
            command=lambda n=note: self._toggle_pin_note(n)
        )
        pin_btn.pack(side="top", pady=2)

        duplicate_btn = ctk.CTkButton(
            actions_frame,
            text="⧉",
            width=36,
            height=28,
            corner_radius=6,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12),
            command=lambda n=note: self._duplicate_note(n)
        )
        duplicate_btn.pack(side="top", pady=2)

        delete_btn = ctk.CTkButton(
            actions_frame,
            text="✕",
            width=36,
            height=28,
            corner_radius=6,
            fg_color="#F44336",
            hover_color="#D32F2F",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12),
            command=lambda n=note: self._delete_note(n)
        )
        delete_btn.pack(side="top", pady=2)

        return card
    
    def _create_file_card(self, file: dict) -> ctk.CTkFrame:
        """Create a file card with a visual icon and action buttons."""
        card = ctk.CTkFrame(
            self.files_list_frame,
            fg_color="#1E1E1E",
            corner_radius=8,
            height=90 if getattr(self, 'file_view_var', None) and self.file_view_var.get() == 'grid' else 70
        )
        card.pack_propagate(False)

        icon_label = ctk.CTkLabel(
            card,
            text=file_manager.get_file_type_icon(file.get('file_name', '')),
            font=ctk.CTkFont(size=24),
            width=32
        )
        icon_label.pack(side="left", padx=(15, 10), pady=10)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        name_label = ctk.CTkLabel(
            info_frame,
            text=file.get('file_name', 'Unknown'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF",
            anchor="w"
        )
        name_label.pack(anchor="w", pady=(0, 3))

        details_text = f"{file.get('file_type', 'Unknown')} • {file.get('file_size', '0 B')}"
        details_label = ctk.CTkLabel(
            info_frame,
            text=details_text,
            font=ctk.CTkFont(size=11),
            text_color="#C5C5C5",
            anchor="w"
        )
        details_label.pack(anchor="w")

        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(side="right", padx=15, pady=10)

        open_btn = ctk.CTkButton(
            actions_frame,
            text="Open",
            width=60,
            height=28,
            corner_radius=6,
            fg_color="#4F8EF7",
            hover_color="#3A7AD9",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11),
            command=lambda f=file: self._open_file(f)
        )
        open_btn.pack(side="left", padx=(0, 5))

        rename_btn = ctk.CTkButton(
            actions_frame,
            text="Rename",
            width=60,
            height=28,
            corner_radius=6,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11),
            command=lambda f=file: self._rename_file(f)
        )
        rename_btn.pack(side="left", padx=(0, 5))

        delete_btn = ctk.CTkButton(
            actions_frame,
            text="Delete",
            width=60,
            height=28,
            corner_radius=6,
            fg_color="#F44336",
            hover_color="#D32F2F",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11),
            command=lambda f=file: self._delete_file(f)
        )
        delete_btn.pack(side="right")

        return card
    
    def _create_assignment_card(self, assignment: dict) -> ctk.CTkFrame:
        """Create an assignment card"""
        card = ctk.CTkFrame(
            self.assignments_list_frame,
            fg_color="#1E1E1E",
            corner_radius=8,
            height=80
        )
        card.pack_propagate(False)
        
        # Assignment info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        title_label = ctk.CTkLabel(
            info_frame,
            text=assignment.get('title', 'Untitled'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF",
            anchor="w"
        )
        title_label.pack(anchor="w", pady=(0, 3))
        
        # Priority and due date
        details_text = f"Due: {assignment.get('due_date', 'No date')}"
        if assignment.get('priority'):
            details_text = f"Priority: {assignment['priority'].title()} • {details_text}"
        
        details_label = ctk.CTkLabel(
            info_frame,
            text=details_text,
            font=ctk.CTkFont(size=11),
            text_color="#C5C5C5",
            anchor="w"
        )
        details_label.pack(anchor="w", pady=(0, 3))
        
        # Status
        status_text = assignment.get('status', 'pending').title()
        status_color = self._get_assignment_status_color(assignment.get('status', 'pending'))
        
        status_label = ctk.CTkLabel(
            info_frame,
            text=f"Status: {status_text}",
            font=ctk.CTkFont(size=11),
            text_color=status_color,
            anchor="w"
        )
        status_label.pack(anchor="w")
        
        # Action buttons
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(side="right", padx=15, pady=10)
        
        # Toggle status button
        toggle_btn = ctk.CTkButton(
            actions_frame,
            text="✓" if assignment.get('status') == 'pending' else "↺",
            width=35,
            height=28,
            corner_radius=6,
            fg_color="#4CAF50" if assignment.get('status') == 'pending' else "#FFC107",
            hover_color="#45A049" if assignment.get('status') == 'pending' else "#FFB300",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda a=assignment: self._toggle_assignment_status(a)
        )
        toggle_btn.pack(side="left", padx=(0, 5))
        
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="Edit",
            width=60,
            height=28,
            corner_radius=6,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11),
            command=lambda a=assignment: self._show_edit_assignment_dialog(a)
        )
        edit_btn.pack(side="left", padx=(0, 5))
        
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="Delete",
            width=60,
            height=28,
            corner_radius=6,
            fg_color="#F44336",
            hover_color="#D32F2F",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11),
            command=lambda a=assignment: self._delete_assignment(a)
        )
        delete_btn.pack(side="right")
        
        return card


class AssignmentDialog(ctk.CTkToplevel):
    """Dialog for adding/editing assignments"""
    
    def __init__(self, parent, title: str, assignment_data: dict = None):
        super().__init__(parent)
        
        self.result = None
        self.assignment_data = assignment_data
        
        self.title(title)
        self.geometry("500x450")
        self.transient(parent)
        self.grab_set()
        
        self._create_content()
        
        if assignment_data:
            self._load_data(assignment_data)
    
    def _create_content(self):
        """Create dialog content"""
        container = ctk.CTkFrame(self, fg_color="#1E1E1E")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title field
        title_label = ctk.CTkLabel(
            container,
            text="Assignment Title *",
            font=ctk.CTkFont(size=13),
            text_color="#C5C5C5"
        )
        title_label.pack(anchor="w", pady=(0, 5))
        
        self.title_entry = ctk.CTkEntry(
            container,
            placeholder_text="e.g., Chapter 1 Homework",
            height=40,
            corner_radius=8,
            border_width=1,
            border_color="#3A3A3A",
            fg_color="#2D2D30",
            text_color="#FFFFFF",
            placeholder_text_color="#C5C5C5"
        )
        self.title_entry.pack(fill="x", pady=(0, 15))
        
        # Description field
        desc_label = ctk.CTkLabel(
            container,
            text="Description",
            font=ctk.CTkFont(size=13),
            text_color="#C5C5C5"
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
        self.desc_entry = ctk.CTkTextbox(
            container,
            height=80,
            corner_radius=8,
            border_width=1,
            border_color="#3A3A3A",
            fg_color="#2D2D30",
            text_color="#FFFFFF",
            wrap="word"
        )
        self.desc_entry.pack(fill="x", pady=(0, 15))
        
        # Due date field
        date_label = ctk.CTkLabel(
            container,
            text="Due Date (YYYY-MM-DD)",
            font=ctk.CTkFont(size=13),
            text_color="#C5C5C5"
        )
        date_label.pack(anchor="w", pady=(0, 5))
        
        self.date_entry = ctk.CTkEntry(
            container,
            placeholder_text="e.g., 2024-12-31",
            height=40,
            corner_radius=8,
            border_width=1,
            border_color="#3A3A3A",
            fg_color="#2D2D30",
            text_color="#FFFFFF",
            placeholder_text_color="#C5C5C5"
        )
        self.date_entry.pack(fill="x", pady=(0, 15))
        
        # Priority and status in same row
        row_frame = ctk.CTkFrame(container, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 15))
        
        # Priority
        priority_label = ctk.CTkLabel(
            row_frame,
            text="Priority",
            font=ctk.CTkFont(size=13),
            text_color="#C5C5C5"
        )
        priority_label.pack(anchor="w", pady=(0, 5))
        
        self.priority_var = ctk.StringVar(value="medium")
        self.priority_menu = ctk.CTkOptionMenu(
            row_frame,
            values=["low", "medium", "high"],
            variable=self.priority_var,
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#3A3A3A",
            button_color="#3A3A3A",
            button_hover_color="#4A4A4A",
            dropdown_fg_color="#2D2D30",
            text_color="#FFFFFF"
        )
        self.priority_menu.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Status
        status_label = ctk.CTkLabel(
            row_frame,
            text="Status",
            font=ctk.CTkFont(size=13),
            text_color="#C5C5C5"
        )
        status_label.pack(anchor="w", pady=(0, 5))
        
        self.status_var = ctk.StringVar(value="pending")
        self.status_menu = ctk.CTkOptionMenu(
            row_frame,
            values=["pending", "completed"],
            variable=self.status_var,
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#3A3A3A",
            button_color="#3A3A3A",
            button_hover_color="#4A4A4A",
            dropdown_fg_color="#2D2D30",
            text_color="#FFFFFF"
        )
        self.status_menu.pack(side="right", fill="x", expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            height=40,
            corner_radius=8,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            text_color="#FFFFFF",
            command=self.destroy
        )
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            height=40,
            corner_radius=8,
            fg_color="#4F8EF7",
            hover_color="#3A7AD9",
            text_color="#FFFFFF",
            command=self._save
        )
        save_btn.pack(side="right", fill="x", expand=True)
    
    def _load_data(self, assignment: dict):
        """Load existing assignment data into form"""
        self.title_entry.insert(0, assignment.get('title', ''))
        self.desc_entry.insert("1.0", assignment.get('description', ''))
        if assignment.get('due_date'):
            self.date_entry.insert(0, assignment['due_date'])
        if assignment.get('priority'):
            self.priority_var.set(assignment['priority'])
        if assignment.get('status'):
            self.status_var.set(assignment['status'])
    
    def _save(self):
        """Save assignment data"""
        title = self.title_entry.get().strip()
        description = self.desc_entry.get("1.0", "end-1c").strip()
        due_date = self.date_entry.get().strip()
        priority = self.priority_var.get()
        status = self.status_var.get()
        
        if not title:
            self.title_entry.configure(border_color="#F44336")
            return
        
        # Reset border color
        self.title_entry.configure(border_color="#3A3A3A")
        
        self.result = {
            'title': title,
            'description': description if description else None,
            'due_date': due_date if due_date else None,
            'priority': priority,
            'status': status
        }
        
        self.destroy()
