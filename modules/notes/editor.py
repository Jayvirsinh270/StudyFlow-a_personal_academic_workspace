"""
Notes Editor
Rich text editor with formatting toolbar and auto-save.
"""

import customtkinter as ctk
from database import create_note, get_note_by_id, update_note
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_INPUT, BG_CHIP, BG_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    ACCENT, ACCENT_HOVER, SUCCESS, WARNING, DANGER,
    BORDER, PAD_SM, PAD_MD, PAD_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
)


class NotesEditor(ctk.CTkToplevel):
    """Rich text notes editor with formatting toolbar."""

    def __init__(self, master, subject_id: int, note_id: int = None,
                 on_close_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Note Editor")
        self.geometry("820x620")
        self.minsize(620, 420)
        self.on_close_callback = on_close_callback
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.subject_id    = subject_id
        self.note_id       = note_id
        self.note_data     = None
        self.auto_save_enabled = True
        self.embedded_tables   = {}

        self._create_content()

        if note_id:
            self._load_note()
        else:
            self._create_new_note()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _create_content(self):
        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_MD)
        toolbar.pack(fill="x", padx=PAD_MD, pady=(PAD_MD, PAD_SM))

        row1 = ctk.CTkFrame(toolbar, fg_color="transparent")
        row1.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 2))

        _btn = dict(width=28, height=28, corner_radius=RADIUS_SM,
                    fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY)

        self.bold_btn = ctk.CTkButton(
            row1, text="B", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_bold, **_btn,
        )
        self.bold_btn.pack(side="left", padx=2)

        self.italic_btn = ctk.CTkButton(
            row1, text="I", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_italic, **_btn,
        )
        self.italic_btn.pack(side="left", padx=2)

        self.underline_btn = ctk.CTkButton(
            row1, text="U", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_underline, **_btn,
        )
        self.underline_btn.pack(side="left", padx=2)

        # Separator
        ctk.CTkFrame(row1, width=1, fg_color=BORDER).pack(side="left", padx=PAD_SM, fill="y", pady=4)

        # Font size
        ctk.CTkLabel(row1, text="Size:", text_color=TEXT_SECONDARY,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(PAD_SM, 2))
        self.font_size_var = ctk.StringVar(value="12")
        ctk.CTkOptionMenu(
            row1, values=["8","10","12","14","16","18","20","24","28","32"],
            variable=self.font_size_var,
            width=60, height=28, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, button_color=BG_INPUT,
            button_hover_color=BG_HOVER, dropdown_fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
            command=self._change_font_size,
        ).pack(side="left", padx=2)

        # Separator
        ctk.CTkFrame(row1, width=1, fg_color=BORDER).pack(side="left", padx=PAD_SM, fill="y", pady=4)

        # Alignment
        self.align_left_btn = ctk.CTkButton(
            row1, text="◧", font=ctk.CTkFont(size=12),
            command=lambda: self._set_alignment("left"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT, width=28, height=28, corner_radius=RADIUS_SM,
        )
        self.align_left_btn.pack(side="left", padx=2)

        self.align_center_btn = ctk.CTkButton(
            row1, text="◫", font=ctk.CTkFont(size=12),
            command=lambda: self._set_alignment("center"), **_btn,
        )
        self.align_center_btn.pack(side="left", padx=2)

        self.align_right_btn = ctk.CTkButton(
            row1, text="◨", font=ctk.CTkFont(size=12),
            command=lambda: self._set_alignment("right"), **_btn,
        )
        self.align_right_btn.pack(side="left", padx=2)

        # Save button on right
        ctk.CTkButton(
            row1, text="Save & Close",
            width=100, height=28, corner_radius=RADIUS_SM,
            fg_color=SUCCESS, hover_color=("#15803D", "#16A34A"),
            text_color=TEXT_ON_ACCENT, font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_closing,
        ).pack(side="right", padx=2)

        # Row 2 — insert tools
        row2 = ctk.CTkFrame(toolbar, fg_color="transparent")
        row2.pack(fill="x", padx=PAD_SM, pady=(2, PAD_SM))

        for text, cmd in [
            ("•", self._insert_bullet),
            ("1.", self._insert_number),
            ("⊞", self._insert_table),
            ("🔗", self._insert_link),
            ("🖼", self._insert_image),
            ("🔍", self._show_find_replace),
        ]:
            ctk.CTkButton(
                row2, text=text,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=cmd, **_btn,
            ).pack(side="left", padx=2)

        # ── Title entry ───────────────────────────────────────────────────────
        title_bar = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_MD)
        title_bar.pack(fill="x", padx=PAD_MD, pady=(0, PAD_SM))

        self.title_entry = ctk.CTkEntry(
            title_bar, placeholder_text="Note Title",
            height=36, corner_radius=RADIUS_SM, border_width=0,
            fg_color="transparent", text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.title_entry.pack(fill="x", padx=PAD_MD, pady=PAD_SM)

        # ── Editor ───────────────────────────────────────────────────────────
        editor_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_MD)
        editor_frame.pack(fill="both", expand=True, padx=PAD_MD, pady=(0, PAD_MD))

        self.text_editor = ctk.CTkTextbox(
            editor_frame, corner_radius=RADIUS_SM,
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            wrap="word",
        )
        self.text_editor.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        self.text_editor.bind("<KeyRelease>", self._on_text_change)
        self.title_entry.bind("<KeyRelease>", self._on_text_change)

    # ── Note I/O ─────────────────────────────────────────────────────────────

    def _load_note(self):
        self.note_data = get_note_by_id(self.note_id)
        if not self.note_data:
            return
        self.title_entry.insert(0, self.note_data.get("title", ""))
        content = self.note_data.get("content", "")
        self.text_editor.delete("1.0", "end")

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|---"):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                table_data = []
                for ri, r in enumerate(table_lines):
                    if ri == 1:
                        continue
                    cells = [c.strip() for c in r.strip().strip("|").split("|")]
                    table_data.append(cells)
                if table_data:
                    rows = len(table_data)
                    cols = max(len(r) for r in table_data) if rows else 0
                    tbl = EmbeddedTable(self.text_editor, rows=rows, cols=cols, initial_data=table_data)
                    self.embedded_tables[str(tbl)] = tbl
                    self.text_editor._textbox.window_create("insert", window=tbl)
                    self.text_editor.insert("insert", "\n")
            else:
                self.text_editor.insert("insert", line + "\n")
                i += 1

    def _create_new_note(self):
        self.note_id   = create_note(self.subject_id, "Untitled Note", "")
        self.note_data = get_note_by_id(self.note_id)
        self.title_entry.insert(0, "Untitled Note")

    def _save_note(self):
        title = self.title_entry.get().strip() or "Untitled Note"
        content = ""
        for item_type, value, _ in self.text_editor._textbox.dump("1.0", "end"):
            if item_type == "text":
                content += value
            elif item_type == "window" and value in self.embedded_tables:
                content += self.embedded_tables[value].to_markdown()
        if content.endswith("\n"):
            content = content[:-1]
        if self.note_id:
            update_note(self.note_id, title=title, content=content)
            self.note_data = get_note_by_id(self.note_id)

    def _on_closing(self):
        self._save_note()
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()

    def _on_text_change(self, _event=None):
        if self.auto_save_enabled:
            if hasattr(self, "_auto_save_job"):
                self.after_cancel(self._auto_save_job)
            self._auto_save_job = self.after(2000, self._save_note)

    # ── Formatting ───────────────────────────────────────────────────────────

    def _toggle_bold(self):
        active = self.bold_btn.cget("fg_color") == ACCENT[0] if isinstance(ACCENT, tuple) else self.bold_btn.cget("fg_color") == ACCENT
        self.bold_btn.configure(fg_color=BG_CHIP if active else ACCENT)

    def _toggle_italic(self):
        active = self.italic_btn.cget("fg_color") == ACCENT[0] if isinstance(ACCENT, tuple) else self.italic_btn.cget("fg_color") == ACCENT
        self.italic_btn.configure(fg_color=BG_CHIP if active else ACCENT)

    def _toggle_underline(self):
        active = self.underline_btn.cget("fg_color") == ACCENT[0] if isinstance(ACCENT, tuple) else self.underline_btn.cget("fg_color") == ACCENT
        self.underline_btn.configure(fg_color=BG_CHIP if active else ACCENT)

    def _change_font_size(self, size):
        self.text_editor.configure(font=ctk.CTkFont(family="Segoe UI", size=int(size)))

    def _set_alignment(self, alignment):
        _inactive = BG_CHIP
        _active   = ACCENT
        self.align_left_btn.configure(fg_color=_inactive)
        self.align_center_btn.configure(fg_color=_inactive)
        self.align_right_btn.configure(fg_color=_inactive)
        {"left": self.align_left_btn,
         "center": self.align_center_btn,
         "right": self.align_right_btn}[alignment].configure(fg_color=_active)

    def _insert_bullet(self):
        self.text_editor.insert("insert", "• ")

    def _insert_number(self):
        self.text_editor.insert("insert", "1. ")

    def _insert_table(self):
        tbl = EmbeddedTable(self.text_editor, rows=3, cols=3)
        self.embedded_tables[str(tbl)] = tbl
        self.text_editor._textbox.window_create("insert", window=tbl)
        self.text_editor.insert("insert", "\n")

    def _insert_link(self):
        dialog = CustomLinkDialog(self)
        self.wait_window(dialog)
        if hasattr(dialog, "result") and dialog.result:
            text, url = dialog.result
            self.text_editor.insert("insert", f"[{text}]({url})")

    def _insert_image(self):
        from tkinter import filedialog
        fp = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")],
        )
        if fp:
            self.text_editor.insert("insert", f"![Image]({fp})")

    def _show_find_replace(self):
        dialog = FindReplaceDialog(self, self.text_editor)
        self.wait_window(dialog)


# ── Find & Replace ────────────────────────────────────────────────────────────

class FindReplaceDialog(ctk.CTkToplevel):
    """Dialog for finding and replacing text."""

    def __init__(self, parent, text_widget):
        super().__init__(parent)
        self.text_widget = text_widget
        self.title("Find and Replace")
        self.geometry("460x260")
        self.transient(parent)
        self.grab_set()
        self._create_content()

    def _create_content(self):
        c = ctk.CTkFrame(self, fg_color=BG_SURFACE)
        c.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        _lkw = dict(font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY, anchor="w")
        _ekw = dict(height=38, corner_radius=RADIUS_SM, border_width=1,
                    border_color=BORDER, fg_color=BG_INPUT, text_color=TEXT_PRIMARY)

        ctk.CTkLabel(c, text="Find:", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        self.find_entry = ctk.CTkEntry(c, placeholder_text="Text to find", **_ekw)
        self.find_entry.pack(fill="x", pady=(0, PAD_MD))
        self.find_entry.bind("<KeyRelease>", lambda _: self._find_next())

        ctk.CTkLabel(c, text="Replace with:", **_lkw).pack(anchor="w", pady=(0, PAD_SM))
        self.replace_entry = ctk.CTkEntry(c, placeholder_text="Replacement text", **_ekw)
        self.replace_entry.pack(fill="x", pady=(0, PAD_LG))

        btn_row = ctk.CTkFrame(c, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row, text="Find Next", height=36, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_ON_ACCENT,
            command=self._find_next,
        ).pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))
        ctk.CTkButton(
            btn_row, text="Replace", height=36, corner_radius=RADIUS_SM,
            fg_color=WARNING, hover_color=("#B45309", "#D97706"), text_color=TEXT_ON_ACCENT,
            command=self._replace,
        ).pack(side="left", fill="x", expand=True, padx=PAD_SM)
        ctk.CTkButton(
            btn_row, text="Replace All", height=36, corner_radius=RADIUS_SM,
            fg_color=SUCCESS, hover_color=("#15803D", "#16A34A"), text_color=TEXT_ON_ACCENT,
            command=self._replace_all,
        ).pack(side="left", fill="x", expand=True, padx=(PAD_SM, 0))

        ctk.CTkButton(
            c, text="Close", height=36, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            command=self.destroy,
        ).pack(fill="x", pady=(PAD_MD, 0))

    def _find_next(self):
        q = self.find_entry.get()
        if not q:
            return
        content = self.text_widget.get("1.0", "end-1c")
        cur = self.text_widget.index("insert")
        offset = len("".join(content.split("\n")[: int(cur.split(".")[0]) - 1]))
        start  = content.find(q, offset)
        if start == -1:
            start = content.find(q)
        if start != -1:
            before = content[:start]
            line   = before.count("\n") + 1
            col    = start - (before.rfind("\n") + 1)
            s, e   = f"{line}.{col}", f"{line}.{col + len(q)}"
            self.text_widget.tag_remove("sel", "1.0", "end")
            self.text_widget.tag_add("sel", s, e)
            self.text_widget.mark_set("insert", e)
            self.text_widget.see(s)

    def _replace(self):
        q = self.find_entry.get()
        r = self.replace_entry.get()
        if not q:
            return
        try:
            sel = self.text_widget.get("sel.first", "sel.last")
            if sel == q:
                self.text_widget.delete("sel.first", "sel.last")
                self.text_widget.insert("insert", r)
                self._find_next()
        except Exception:
            self._find_next()

    def _replace_all(self):
        q = self.find_entry.get()
        r = self.replace_entry.get()
        if not q:
            return
        content = self.text_widget.get("1.0", "end-1c").replace(q, r)
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", content)


# ── Custom link dialog ────────────────────────────────────────────────────────

class CustomLinkDialog(ctk.CTkToplevel):
    """Themed dialog for inserting hyperlinks."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Insert Link")
        self.geometry("360x230")
        self.transient(parent)
        self.grab_set()
        self.result = None

        c = ctk.CTkFrame(self, fg_color=BG_SURFACE)
        c.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        _lkw = dict(font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY, anchor="w")
        ctk.CTkLabel(c, text="Display text:", **_lkw).pack(anchor="w")
        self.text_entry = ctk.CTkEntry(c, height=36, fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
                                        border_color=BORDER, border_width=1, corner_radius=RADIUS_SM)
        self.text_entry.pack(fill="x", pady=(0, PAD_MD))
        self.text_entry.insert(0, "Click here")

        ctk.CTkLabel(c, text="URL:", **_lkw).pack(anchor="w")
        self.url_entry = ctk.CTkEntry(c, height=36, fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
                                       border_color=BORDER, border_width=1, corner_radius=RADIUS_SM)
        self.url_entry.pack(fill="x", pady=(0, PAD_LG))

        btns = ctk.CTkFrame(c, fg_color="transparent")
        btns.pack(fill="x")
        ctk.CTkButton(
            btns, text="Cancel", height=36, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))
        ctk.CTkButton(
            btns, text="Insert", height=36, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_ON_ACCENT,
            command=self._submit,
        ).pack(side="right", fill="x", expand=True)

    def _submit(self):
        url = self.url_entry.get().strip()
        if url:
            self.result = (self.text_entry.get().strip() or url, url)
            self.destroy()


# ── Embedded table ────────────────────────────────────────────────────────────

class EmbeddedTable(ctk.CTkFrame):
    """Interactive grid embedded directly into the text editor."""

    def __init__(self, master, rows=3, cols=3, initial_data=None, **kwargs):
        super().__init__(master, fg_color=BG_CARD, **kwargs)
        self.rows = rows
        self.cols = cols
        self.entries: list[list] = []

        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(side="left", padx=PAD_SM, pady=PAD_SM)

        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(side="left", padx=PAD_SM, pady=PAD_SM, fill="y")

        _cb = dict(width=44, height=22, corner_radius=RADIUS_SM,
                   fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
                   font=ctk.CTkFont(size=10))
        ctk.CTkButton(ctrl, text="+ Row", command=self._add_row, **_cb).pack(pady=2)
        ctk.CTkButton(ctrl, text="- Row", command=self._remove_row, **_cb).pack(pady=2)
        ctk.CTkButton(ctrl, text="+ Col", command=self._add_col, **_cb).pack(pady=2)
        ctk.CTkButton(ctrl, text="- Col", command=self._remove_col, **_cb).pack(pady=2)

        self._build_grid(initial_data)

    def _build_grid(self, initial_data=None):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.entries = []
        for r in range(self.rows):
            row_es = []
            bg = BG_CHIP if r == 0 else BG_INPUT
            for c in range(self.cols):
                e = ctk.CTkEntry(
                    self.grid_frame, width=100, height=28,
                    fg_color=bg, text_color=TEXT_PRIMARY,
                    border_width=1, border_color=BORDER,
                    font=ctk.CTkFont(weight="bold" if r == 0 else "normal", size=11),
                )
                e.grid(row=r, column=c, padx=1, pady=1)
                if initial_data and r < len(initial_data) and c < len(initial_data[r]):
                    e.insert(0, initial_data[r][c])
                elif r == 0 and initial_data is None:
                    e.insert(0, f"Header {c + 1}")
                row_es.append(e)
            self.entries.append(row_es)

    def _current_data(self):
        return [[e.get() for e in row] for row in self.entries]

    def _add_row(self):
        self.rows += 1; self._build_grid(self._current_data())

    def _remove_row(self):
        if self.rows > 1:
            self.rows -= 1; self._build_grid(self._current_data())

    def _add_col(self):
        self.cols += 1; self._build_grid(self._current_data())

    def _remove_col(self):
        if self.cols > 1:
            self.cols -= 1; self._build_grid(self._current_data())

    def to_markdown(self) -> str:
        md = "\n"
        for ri, row in enumerate(self._current_data()):
            padded = [v if v.strip() else " " for v in row]
            md += "| " + " | ".join(padded) + " |\n"
            if ri == 0:
                md += "|" + "|".join(["---"] * self.cols) + "|\n"
        return md + "\n"
