import customtkinter as ctk
from database import get_note_by_id

class NoteReader(ctk.CTkToplevel):
    """Read-only view for notes with student-friendly features"""
    
    def __init__(self, master, note_id: int, **kwargs):
        super().__init__(master, **kwargs)
        
        self.title("Note Reader")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Bring to front on open
        self.lift()
        self.focus_force()
        self.grab_set()  # Optional: Make it modal. Let's not make it modal so students can refer to other things.
        self.grab_release()
        
        self.note_id = note_id
        self.note_data = get_note_by_id(self.note_id)
        self.current_font_size = 14
        
        self._create_content()
        self._load_note()
        
    def _create_content(self):
        # Toolbar
        toolbar_frame = ctk.CTkFrame(self, fg_color="#2D2D30", height=50, corner_radius=12)
        toolbar_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Zoom Controls
        zoom_in_btn = ctk.CTkButton(
            toolbar_frame, 
            text="A+", 
            width=40,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            command=self._zoom_in
        )
        zoom_in_btn.pack(side="left", padx=(10, 5), pady=10)
        
        zoom_out_btn = ctk.CTkButton(
            toolbar_frame, 
            text="A-", 
            width=40,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            command=self._zoom_out
        )
        zoom_out_btn.pack(side="left", padx=5, pady=10)
        
        # Theme dropdown
        theme_label = ctk.CTkLabel(toolbar_frame, text="Theme:", text_color="#C5C5C5")
        theme_label.pack(side="left", padx=(15, 5))
        
        self.theme_var = ctk.StringVar(value="Dark")
        theme_menu = ctk.CTkOptionMenu(
            toolbar_frame, 
            values=["Dark", "Light", "Eye Protection"], 
            variable=self.theme_var,
            width=120,
            fg_color="#3A3A3A",
            button_color="#3A3A3A",
            button_hover_color="#4A4A4A",
            command=self._change_theme
        )
        theme_menu.pack(side="left", padx=5, pady=10)
        
        # Highlight button
        highlight_btn = ctk.CTkButton(
            toolbar_frame, 
            text="Highlight Text", 
            width=100, 
            fg_color="#FFC107", 
            text_color="black", 
            hover_color="#FFB300", 
            command=self._highlight_text
        )
        highlight_btn.pack(side="left", padx=(20, 5), pady=10)
        
        # Textbox Frame
        editor_frame = ctk.CTkFrame(self, fg_color="#2D2D30", corner_radius=12)
        editor_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.text_reader = ctk.CTkTextbox(
            editor_frame,
            corner_radius=8,
            fg_color="#1E1E1E",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=self.current_font_size),
            wrap="word",
            state="normal"
        )
        self.text_reader.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tag configuration for highlighting
        self.text_reader.tag_config("highlight", background="#FFEB3B", foreground="black")

    def _load_note(self):
        if self.note_data:
            self.title(f"Reading: {self.note_data.get('title', 'Untitled')}")
            self.text_reader.insert("1.0", f"{self.note_data.get('title', 'Untitled')}\n\n")
            self.text_reader.insert("end", self.note_data.get('content', ''))
            
            # Make the title bigger
            self.text_reader.tag_add("title", "1.0", "1.end")
            self.text_reader.tag_config("title", font=ctk.CTkFont(family="Segoe UI", size=self.current_font_size + 6, weight="bold"))
            
        self.text_reader.configure(state="disabled")
        
    def _zoom_in(self):
        self.current_font_size += 2
        self.text_reader.configure(font=ctk.CTkFont(family="Segoe UI", size=self.current_font_size))
        self.text_reader.tag_config("title", font=ctk.CTkFont(family="Segoe UI", size=self.current_font_size + 6, weight="bold"))
        
    def _zoom_out(self):
        if self.current_font_size > 8:
            self.current_font_size -= 2
            self.text_reader.configure(font=ctk.CTkFont(family="Segoe UI", size=self.current_font_size))
            self.text_reader.tag_config("title", font=ctk.CTkFont(family="Segoe UI", size=self.current_font_size + 6, weight="bold"))
            
    def _change_theme(self, theme):
        if theme == "Dark":
            self.text_reader.configure(fg_color="#1E1E1E", text_color="#FFFFFF")
        elif theme == "Light":
            self.text_reader.configure(fg_color="#FFFFFF", text_color="#000000")
        elif theme == "Eye Protection":
            # Warm Sepia tone
            self.text_reader.configure(fg_color="#F4ECD8", text_color="#5B4636")
            
    def _highlight_text(self):
        try:
            self.text_reader.tag_add("highlight", "sel.first", "sel.last")
        except:
            pass # No text selected
