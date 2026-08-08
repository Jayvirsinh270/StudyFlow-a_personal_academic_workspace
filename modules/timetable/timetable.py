"""
Timetable Module
Weekly schedule with subject, teacher, and classroom information.
- Full 24-hour time slots from 06:00 to 23:00
- Click any empty cell to add an entry pre-filled with that day & time
- Dialog is fully scrollable so nothing gets cut off
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from database import (
    add_timetable_entry, get_timetable, update_timetable_entry,
    delete_timetable_entry, get_subjects, get_calendar_events,
)
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_INPUT, BG_CHIP, BG_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    ACCENT, ACCENT_HOVER, SUCCESS, WARNING, DANGER,
    BORDER, PAD_XS, PAD_SM, PAD_MD, PAD_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL,
)


def _font(size=FONT_MD, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def _bold(size=FONT_MD) -> ctk.CTkFont:
    return _font(size, "bold")


# ── Build all hour slots 06:00 → 23:00 ───────────────────────────────────────
def _build_slot_map() -> dict:
    """Return an ordered dict of display label → (start_HH:MM, end_HH:MM)."""
    slots = {}
    for h in range(6, 23):           # 06:00 up to 22:00–23:00
        end_h = h + 1
        # Display label keeps the informal "6:00-7:00" style
        if h < 12:
            start_lbl = f"{h}:00"
        elif h == 12:
            start_lbl = "12:00"
        else:
            start_lbl = f"{h}:00"

        if end_h < 12:
            end_lbl = f"{end_h}:00"
        elif end_h == 12:
            end_lbl = "12:00"
        else:
            end_lbl = f"{end_h}:00"

        label = f"{start_lbl}-{end_lbl}"
        slots[label] = (f"{h:02d}:00", f"{end_h:02d}:00")
    return slots


_SLOT_MAP: dict = _build_slot_map()   # 17 slots: 6:00-7:00 … 22:00-23:00
_ALL_SLOTS: list = list(_SLOT_MAP.keys())


def build_planner_focus_summary(today_entries: list, day_events: list) -> str:
    class_count = len(today_entries)
    event_count = len(day_events)
    if not class_count and not event_count:
        return "A calm day ahead — no classes or events planned yet."
    parts = []
    if class_count:
        parts.append(f"{class_count} class{'es' if class_count != 1 else ''}")
    if event_count:
        parts.append(f"{event_count} event{'s' if event_count != 1 else ''}")
    return f"Today's focus: {' and '.join(parts)} on your schedule."


def _safe_cell_key(day: str, slot: str) -> str:
    """Convert day + slot string into a safe Python attribute name."""
    return f"cell_{day}_{slot.replace(':', '_').replace('-', '_')}"


class PlannerSummary(ctk.CTkFrame):
    """Compact overview for today's planner state."""

    def __init__(self, master, entries, subjects, **kwargs):
        super().__init__(master, **kwargs)
        self.entries  = entries
        self.subjects = subjects
        self.configure(fg_color="transparent")
        self._create_content()

    def _create_content(self):
        today = datetime.now().strftime("%A")
        today_entries = [e for e in self.entries if e.get("day") == today]
        day_events    = [ev for ev in get_calendar_events()
                         if ev.get("event_date") == datetime.now().strftime("%Y-%m-%d")]

        if not today_entries and not day_events:
            ctk.CTkLabel(
                self, text="No classes scheduled for today yet.",
                font=_font(FONT_SM), text_color=TEXT_MUTED, anchor="w",
            ).pack(anchor="w")
            return

        ctk.CTkLabel(
            self, text=build_planner_focus_summary(today_entries, day_events),
            font=_bold(FONT_MD), text_color=TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w", pady=(0, PAD_SM))

        next_entry = next(
            (e for e in sorted(today_entries, key=lambda x: x.get("time_slot", ""))
             if self._is_upcoming(e)),
            None,
        )
        if next_entry:
            subj = self._subject_name(next_entry.get("subject_id"))
            ctk.CTkLabel(
                self, text=f"Next up: {subj} at {next_entry.get('time_slot', 'TBD')}",
                font=_font(FONT_SM), text_color=ACCENT[1], anchor="w",
            ).pack(anchor="w")

    def _subject_name(self, sid):
        return next((s["name"] for s in self.subjects if s.get("id") == sid), "Unknown")

    def _is_upcoming(self, entry) -> bool:
        if entry.get("day") != datetime.now().strftime("%A"):
            return False
        now    = datetime.now().strftime("%H:%M")
        bounds = _SLOT_MAP.get(entry.get("time_slot"))
        if not bounds:
            return False
        start, end = bounds
        return start <= now < end or now < start


class Timetable(ctk.CTkFrame):
    """Timetable view — full 24-hr grid, click-to-add, scrollable dialog."""

    DAYS  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    SLOTS = _ALL_SLOTS          # 06:00-07:00 … 22:00-23:00

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.subjects_data = get_subjects()
        self._create_content()
        self._load_timetable()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _create_content(self):
        # ── Header bar ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(
            self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
            border_width=1, border_color=BORDER,
        )
        header.pack(fill="x", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=PAD_LG, pady=PAD_MD)
        ctk.CTkLabel(
            left, text="▦  Weekly Timetable",
            font=_bold(FONT_XL), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        # Hint label
        ctk.CTkLabel(
            left,
            text="  — tap any empty cell or use ＋ Add Entry",
            font=_font(FONT_SM), text_color=TEXT_MUTED,
        ).pack(side="left")

        ctk.CTkButton(
            header, text="＋  Add Entry",
            width=126, height=34, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT, font=_bold(FONT_SM),
            command=self._show_add_entry_dialog,
        ).pack(side="right", padx=PAD_LG, pady=PAD_MD)

        # ── Today summary strip ───────────────────────────────────────────────
        self.summary_frame = ctk.CTkFrame(
            self, fg_color=BG_CHIP, corner_radius=RADIUS_MD,
            border_width=1, border_color=BORDER,
        )
        self.summary_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_SM))
        self.summary_content = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        self.summary_content.pack(fill="x", padx=PAD_LG, pady=PAD_SM)

        # ── Grid card ─────────────────────────────────────────────────────────
        grid_card = ctk.CTkFrame(
            self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
            border_width=1, border_color=BORDER,
        )
        grid_card.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        self._create_grid(grid_card)

    def _create_grid(self, parent):
        # Day-name header row (fixed, not scrollable)
        hdr_wrap = ctk.CTkFrame(parent, fg_color="transparent")
        hdr_wrap.pack(fill="x", padx=PAD_MD, pady=(PAD_MD, 0))

        # Time-label column spacer
        ctk.CTkLabel(hdr_wrap, text="Time", width=84,
                     font=_bold(FONT_XS), text_color=TEXT_MUTED).pack(side="left", padx=PAD_SM)

        today = datetime.now().strftime("%A")
        for day in self.DAYS:
            is_today = day == today
            lbl_frame = ctk.CTkFrame(
                hdr_wrap,
                fg_color=(("#EFF6FF", "#1E2F50") if is_today else "transparent"),
                corner_radius=RADIUS_SM,
                width=104, height=28,
            )
            lbl_frame.pack(side="left", padx=2)
            lbl_frame.pack_propagate(False)
            ctk.CTkLabel(
                lbl_frame,
                text=day[:3].upper(),
                font=_bold(FONT_SM) if is_today else _font(FONT_SM),
                text_color=ACCENT[1] if is_today else TEXT_SECONDARY,
                width=100,
            ).place(relx=0.5, rely=0.5, anchor="center")

        # Thin divider
        ctk.CTkFrame(parent, fg_color=BORDER, height=1).pack(fill="x", padx=PAD_MD, pady=(PAD_SM, 0))

        # Scrollable grid body
        self.entries_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.entries_frame.pack(fill="both", expand=True, padx=PAD_MD, pady=(0, PAD_MD))

        for slot in self.SLOTS:
            row = ctk.CTkFrame(self.entries_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # Time label
            ctk.CTkLabel(
                row, text=slot,
                font=_font(FONT_XS), text_color=TEXT_MUTED, width=84, anchor="e",
            ).pack(side="left", padx=(PAD_SM, 4))

            for day in self.DAYS:
                cell = ctk.CTkFrame(
                    row, fg_color=BG_CARD, corner_radius=RADIUS_SM,
                    width=104, height=62,
                    cursor="hand2",
                )
                cell.pack(side="left", padx=2)
                cell.pack_propagate(False)

                key = _safe_cell_key(day, slot)
                setattr(self, key, cell)

                # Clicking an empty cell pre-fills the dialog
                cell.bind(
                    "<Button-1>",
                    lambda e, d=day, s=slot: self._cell_clicked(d, s),
                )

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_timetable(self):
        data = get_timetable()

        # Refresh summary
        for w in self.summary_content.winfo_children():
            w.destroy()
        PlannerSummary(
            self.summary_content, data, self.subjects_data,
        ).pack(side="left", fill="x", expand=True)

        today = datetime.now().strftime("%A")
        today_entries = [e for e in data if e.get("day") == today]
        if today_entries:
            ctk.CTkLabel(
                self.summary_content,
                text=f"{len(today_entries)} class{'es' if len(today_entries) != 1 else ''} today",
                font=_bold(FONT_SM), text_color=ACCENT[1],
            ).pack(side="right")

        # Populate filled cells
        for entry in data:
            day  = entry.get("day")
            slot = entry.get("time_slot")
            if day and slot:
                key = _safe_cell_key(day, slot)
                if hasattr(self, key):
                    self._update_cell(getattr(self, key), entry)

    def _update_cell(self, cell, entry: dict):
        """Render an occupied cell — click it to reveal Edit / Delete popup."""
        for w in cell.winfo_children():
            w.destroy()

        # Remove the click-to-add binding — cell is occupied
        cell.unbind("<Button-1>")

        subject_name = next(
            (s["name"] for s in self.subjects_data if s.get("id") == entry.get("subject_id")),
            "Unknown",
        )
        subj_color = next(
            (s.get("color") or ACCENT[1] for s in self.subjects_data
             if s.get("id") == entry.get("subject_id")),
            ACCENT[1],
        )

        today      = datetime.now().strftime("%A")
        now        = datetime.now().strftime("%H:%M")
        bounds     = _SLOT_MAP.get(entry.get("time_slot"))
        is_current = bool(
            entry.get("day") == today and bounds
            and bounds[0] <= now < bounds[1]
        )
        is_today = entry.get("day") == today

        if is_current:
            cell.configure(fg_color=BG_CHIP, border_width=2, border_color=ACCENT[1])
        elif is_today:
            cell.configure(fg_color=BG_HOVER, border_width=1, border_color=SUCCESS[1])
        else:
            cell.configure(fg_color=BG_CARD, border_width=1, border_color=subj_color)

        # Coloured top accent bar
        bar = ctk.CTkFrame(cell, fg_color=subj_color, height=3, corner_radius=0)
        bar.pack(fill="x")

        # Subject name
        name_lbl = ctk.CTkLabel(
            cell, text=subject_name,
            font=_bold(FONT_XS), text_color=TEXT_PRIMARY, wraplength=96,
        )
        name_lbl.pack(pady=(4, 0))

        # Room / classroom
        if entry.get("classroom"):
            room_lbl = ctk.CTkLabel(
                cell, text=entry["classroom"],
                font=_font(FONT_XS - 1), text_color=TEXT_MUTED,
            )
            room_lbl.pack(pady=(0, 1))

        # "Now" badge
        if is_current:
            ctk.CTkLabel(
                cell, text="● Now",
                font=_bold(FONT_XS - 1), text_color=ACCENT[1],
            ).pack()

        # Bind the whole cell (and every child) to open the action popup on click
        def _open_popup(event, e=entry, c=cell):
            self._show_cell_popup(e, c)

        for widget in [cell, bar, name_lbl] + list(cell.winfo_children()):
            widget.bind("<Button-1>", _open_popup)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _cell_clicked(self, day: str, slot: str):
        """Open Add Entry dialog pre-filled with the clicked day & time slot."""
        # Only act when cell is still empty (no children that are CTkButtons)
        key  = _safe_cell_key(day, slot)
        cell = getattr(self, key, None)
        if cell:
            has_entry = any(
                isinstance(w, ctk.CTkButton)
                for w in cell.winfo_children()
            )
            if has_entry:
                return  # occupied — let the edit button handle it

        # Pre-fill with this day & slot
        prefill = {"day": day, "time_slot": slot}
        dialog = TimetableEntryDialog(self, "Add Entry", self.subjects_data,
                                      prefill=prefill)
        self.wait_window(dialog)
        if dialog.result:
            try:
                add_timetable_entry(**dialog.result)
                self._refresh()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def _show_cell_popup(self, entry: dict, cell):
        """Show a small popup over the clicked cell with Edit and Delete options."""
        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        # Position popup right below the cell
        popup.update_idletasks()
        cx = cell.winfo_rootx()
        cy = cell.winfo_rooty() + cell.winfo_height()
        popup.geometry(f"200x118+{cx}+{cy}")

        subject_name = next(
            (s["name"] for s in self.subjects_data if s.get("id") == entry.get("subject_id")),
            "Unknown",
        )

        # Popup frame
        frame = ctk.CTkFrame(
            popup, fg_color=BG_SURFACE,
            corner_radius=RADIUS_MD, border_width=1, border_color=BORDER,
        )
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Header: subject name + close
        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 0))

        ctk.CTkLabel(
            hdr, text=subject_name,
            font=_bold(FONT_SM), text_color=TEXT_PRIMARY, anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            hdr, text="✕", width=22, height=22, corner_radius=4,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_MUTED, font=_font(FONT_XS),
            command=popup.destroy,
        ).pack(side="right")

        ctk.CTkFrame(frame, fg_color=BORDER, height=1).pack(fill="x", padx=PAD_SM, pady=(PAD_XS, PAD_SM))

        # ── Action buttons ────────────────────────────────────────────────────
        btn_kw = dict(height=32, corner_radius=RADIUS_SM, font=_bold(FONT_SM))

        def _do_edit():
            popup.withdraw()        # hide instantly so it vanishes before dialog opens
            popup.update()          # force OS repaint
            popup.destroy()
            self.after(30, lambda: self._show_edit_entry_dialog(entry))

        def _do_delete():
            popup.withdraw()
            popup.update()
            popup.destroy()
            self.after(30, lambda: self._delete_entry(entry))

        ctk.CTkButton(
            frame, text="✎  Edit Entry",
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=("#FFFFFF", "#FFFFFF"),
            command=_do_edit, **btn_kw,
        ).pack(fill="x", padx=PAD_SM, pady=(0, PAD_XS))

        ctk.CTkButton(
            frame, text="✕  Delete Entry",
            fg_color=("#FEE2E2", "#450A0A"), hover_color=("#FECACA", "#7F1D1D"),
            text_color=DANGER[0],
            command=_do_delete, **btn_kw,
        ).pack(fill="x", padx=PAD_SM, pady=(0, PAD_SM))

    def _show_add_entry_dialog(self, day: str = None, slot: str = None):
        prefill = {}
        if day:
            prefill["day"] = day
        if slot:
            prefill["time_slot"] = slot
        dialog = TimetableEntryDialog(self, "Add Entry", self.subjects_data,
                                      prefill=prefill if prefill else None)
        self.wait_window(dialog)
        if dialog.result:
            try:
                add_timetable_entry(**dialog.result)
                self._refresh()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def _show_edit_entry_dialog(self, entry: dict):
        dialog = TimetableEntryDialog(self, "Edit Entry", self.subjects_data,
                                      entry_data=entry)
        self.wait_window(dialog)
        if dialog.result:
            try:
                update_timetable_entry(entry_id=entry["id"], **dialog.result)
                self._refresh()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def _delete_entry(self, entry: dict):
        if messagebox.askyesno("Delete Entry",
                               f"Remove this timetable entry?"):
            try:
                delete_timetable_entry(entry["id"])
                self._refresh()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def _refresh(self):
        """Clear all cells and reload from DB."""
        for day in self.DAYS:
            for slot in self.SLOTS:
                key = _safe_cell_key(day, slot)
                if hasattr(self, key):
                    cell = getattr(self, key)
                    for w in cell.winfo_children():
                        w.destroy()
                    cell.configure(fg_color=BG_CARD, border_width=0)
                    # Restore click-to-add binding
                    cell.bind(
                        "<Button-1>",
                        lambda e, d=day, s=slot: self._cell_clicked(d, s),
                    )
        self.subjects_data = get_subjects()
        self._load_timetable()


# ── Dialog ────────────────────────────────────────────────────────────────────

class TimetableEntryDialog(ctk.CTkToplevel):
    """
    Scrollable dialog for adding / editing timetable entries.
    - Full 24-hr time slots (06:00–23:00)
    - Accepts an optional `prefill` dict to pre-select day & time from a cell click
    - All content inside a CTkScrollableFrame so nothing is cut off
    """

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday"]

    def __init__(self, parent, title: str, subjects: list,
                 entry_data: dict = None, prefill: dict = None):
        super().__init__(parent)
        self.result     = None
        self.subjects   = subjects
        self.entry_data = entry_data
        self._prefill   = prefill or {}

        self.title(title)
        self.geometry("460x540")
        self.resizable(False, True)          # allow vertical resize if needed
        self.minsize(420, 460)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_content()

        # Pre-fill from existing entry (edit mode)
        if entry_data:
            self._load_data(entry_data)
        # Pre-fill from cell click (add mode)
        elif self._prefill:
            self._apply_prefill(self._prefill)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _create_content(self):
        # Coloured header strip
        hdr = ctk.CTkFrame(self, fg_color=ACCENT, height=50, corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr_icon = "✎  Edit Entry" if self.entry_data else "＋  New Timetable Entry"
        ctk.CTkLabel(
            hdr, text=hdr_icon,
            font=_bold(FONT_LG), text_color="#FFFFFF",
        ).pack(side="left", padx=PAD_LG, pady=PAD_MD)

        # Scrollable form body
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_SURFACE)
        scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.grid_rowconfigure(1, weight=1)

        pad_v = (0, PAD_MD)
        _lkw  = dict(font=_bold(FONT_SM), text_color=TEXT_PRIMARY, anchor="w")
        _ekw  = dict(height=42, corner_radius=RADIUS_SM,
                     border_width=1, border_color=BORDER,
                     fg_color=BG_INPUT, text_color=TEXT_PRIMARY)
        _om   = dict(height=42, corner_radius=RADIUS_SM,
                     fg_color=BG_INPUT, button_color=BG_INPUT,
                     button_hover_color=BG_HOVER, dropdown_fg_color=BG_SURFACE,
                     text_color=TEXT_PRIMARY, dynamic_resizing=False)

        inner = ctk.CTkFrame(scroll, fg_color="transparent")
        inner.pack(fill="x", padx=PAD_LG, pady=PAD_LG)

        # ── Day ──────────────────────────────────────────────────────────────
        ctk.CTkLabel(inner, text="Day *", **_lkw).pack(anchor="w", pady=(0, 4))
        self.day_var = ctk.StringVar(value=self._prefill.get("day", "Monday"))
        ctk.CTkOptionMenu(
            inner, values=self.DAYS, variable=self.day_var, **_om,
        ).pack(fill="x", pady=pad_v)

        # ── Time Slot ─────────────────────────────────────────────────────────
        ctk.CTkLabel(inner, text="Time Slot *", **_lkw).pack(anchor="w", pady=(0, 4))

        self.time_var = ctk.StringVar(
            value=self._prefill.get("time_slot", _ALL_SLOTS[2])  # default 08:00-09:00
        )

        # Two-column time picker: Start hour | End hour
        time_row = ctk.CTkFrame(inner, fg_color="transparent")
        time_row.pack(fill="x", pady=pad_v)
        time_row.grid_columnconfigure(0, weight=1)
        time_row.grid_columnconfigure(1, weight=1)

        # Build hour lists for spinboxes
        start_hours = [f"{h:02d}:00" for h in range(6, 23)]   # 06:00 .. 22:00
        end_hours   = [f"{h:02d}:00" for h in range(7, 24)]   # 07:00 .. 23:00

        start_wrap = ctk.CTkFrame(time_row, fg_color="transparent")
        start_wrap.grid(row=0, column=0, sticky="ew", padx=(0, PAD_SM))
        ctk.CTkLabel(start_wrap, text="Start",
                     font=_font(FONT_XS), text_color=TEXT_MUTED).pack(anchor="w")
        self.start_var = ctk.StringVar(value="08:00")
        ctk.CTkOptionMenu(
            start_wrap, values=start_hours, variable=self.start_var,
            command=self._sync_time_var, **_om,
        ).pack(fill="x")

        end_wrap = ctk.CTkFrame(time_row, fg_color="transparent")
        end_wrap.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(end_wrap, text="End",
                     font=_font(FONT_XS), text_color=TEXT_MUTED).pack(anchor="w")
        self.end_var = ctk.StringVar(value="09:00")
        ctk.CTkOptionMenu(
            end_wrap, values=end_hours, variable=self.end_var,
            command=self._sync_time_var, **_om,
        ).pack(fill="x")

        # Live preview of the combined slot label
        self._slot_preview = ctk.CTkLabel(
            inner, text="",
            font=_font(FONT_SM), text_color=ACCENT[1], anchor="w",
        )
        self._slot_preview.pack(anchor="w", pady=(0, PAD_MD))
        self._sync_time_var()   # initialise preview

        # ── Subject ───────────────────────────────────────────────────────────
        ctk.CTkLabel(inner, text="Subject *", **_lkw).pack(anchor="w", pady=(0, 4))
        names = [s.get("name", "Unknown") for s in self.subjects]
        self.subject_var = ctk.StringVar(value=names[0] if names else "")
        ctk.CTkOptionMenu(
            inner,
            values=names if names else ["No subjects — add one first"],
            variable=self.subject_var, **_om,
        ).pack(fill="x", pady=pad_v)

        if not names:
            ctk.CTkLabel(
                inner,
                text="⚠  No subjects found. Add subjects first from the Subjects page.",
                font=_font(FONT_XS), text_color=WARNING[1],
                wraplength=380, justify="left",
            ).pack(anchor="w", pady=(0, PAD_MD))

        # ── Room / Location ───────────────────────────────────────────────────
        ctk.CTkLabel(inner, text="Room / Location", **_lkw).pack(anchor="w", pady=(0, 4))
        self.room_entry = ctk.CTkEntry(
            inner, placeholder_text="e.g., Room 101, Lab 3, Online…",
            **_ekw,
        )
        self.room_entry.pack(fill="x", pady=pad_v)

        # ── Notes (optional) ──────────────────────────────────────────────────
        ctk.CTkLabel(inner, text="Notes  (optional)", **_lkw).pack(anchor="w", pady=(0, 4))
        self.notes_entry = ctk.CTkEntry(
            inner, placeholder_text="e.g., Bring textbook, attendance mandatory…",
            **_ekw,
        )
        self.notes_entry.pack(fill="x", pady=pad_v)

        # ── Repeat pattern info ───────────────────────────────────────────────
        info = ctk.CTkFrame(
            inner, fg_color=(("#EFF6FF", "#1E2F50")),
            corner_radius=RADIUS_SM, border_width=1, border_color=BORDER,
        )
        info.pack(fill="x", pady=(PAD_SM, 0))
        ctk.CTkLabel(
            info,
            text="ℹ  This entry will appear every week on the selected day.",
            font=_font(FONT_XS), text_color=ACCENT[1],
        ).pack(padx=PAD_MD, pady=PAD_SM)

        # ── Button bar (outside scroll, always visible) ───────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE,
                                 border_width=1, border_color=BORDER)
        btn_frame.grid(row=2, column=0, sticky="ew")

        btn_inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_inner.pack(fill="x", padx=PAD_LG, pady=PAD_MD)

        ctk.CTkButton(
            btn_inner, text="Cancel", height=40, corner_radius=RADIUS_SM,
            fg_color=BG_CHIP, hover_color=BG_HOVER, text_color=TEXT_PRIMARY,
            font=_font(FONT_MD),
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, PAD_SM))

        ctk.CTkButton(
            btn_inner,
            text="✎  Update Entry" if self.entry_data else "＋  Add Entry",
            height=40, corner_radius=RADIUS_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT, font=_bold(FONT_MD),
            command=self._save,
        ).pack(side="right", fill="x", expand=True)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sync_time_var(self, _=None):
        """Build the combined 'HH:MM-HH:MM' slot string and update preview."""
        start = self.start_var.get()          # e.g. "08:00"
        end   = self.end_var.get()            # e.g. "09:00"

        # Convert "08:00" → "8:00" style to match existing DB values
        sh = int(start.split(":")[0])
        eh = int(end.split(":")[0])
        slot_label = f"{sh}:00-{eh}:00"

        self.time_var.set(slot_label)
        self._slot_preview.configure(
            text=f"  ▸  Slot:  {start} – {end}  ({slot_label})"
        )

        # Auto-advance end hour if start ≥ end
        if sh >= eh:
            new_end = min(sh + 1, 23)
            self.end_var.set(f"{new_end:02d}:00")
            slot_label = f"{sh}:00-{new_end}:00"
            self.time_var.set(slot_label)
            self._slot_preview.configure(
                text=f"  ▸  Slot:  {start} – {new_end:02d}:00  ({slot_label})"
            )

    def _apply_prefill(self, prefill: dict):
        """Set day and time pickers from a cell-click prefill dict."""
        if "day" in prefill:
            self.day_var.set(prefill["day"])

        if "time_slot" in prefill:
            slot = prefill["time_slot"]   # e.g. "8:00-9:00"
            parts = slot.split("-")
            if len(parts) == 2:
                sh_raw, eh_raw = parts[0].strip(), parts[1].strip()
                try:
                    sh = int(sh_raw.split(":")[0])
                    eh = int(eh_raw.split(":")[0])
                    self.start_var.set(f"{sh:02d}:00")
                    self.end_var.set(f"{eh:02d}:00")
                    self._sync_time_var()
                except ValueError:
                    pass

    def _load_data(self, e: dict):
        """Pre-fill all fields for edit mode."""
        if e.get("day"):
            self.day_var.set(e["day"])
        if e.get("time_slot"):
            self._apply_prefill({"time_slot": e["time_slot"]})
        for s in self.subjects:
            if s.get("id") == e.get("subject_id"):
                self.subject_var.set(s.get("name", "Unknown"))
                break
        if e.get("classroom"):
            self.room_entry.insert(0, e["classroom"])
        if e.get("remarks"):
            self.notes_entry.insert(0, e["remarks"])

    def _save(self):
        subject_id = next(
            (s["id"] for s in self.subjects if s.get("name") == self.subject_var.get()),
            None,
        )
        if not subject_id:
            messagebox.showerror("No Subject", "Please select a valid subject.")
            return

        slot = self.time_var.get()
        if not slot:
            messagebox.showerror("No Time", "Please select a start and end time.")
            return

        # Validate start < end
        parts = slot.split("-")
        if len(parts) == 2:
            try:
                sh = int(parts[0].split(":")[0])
                eh = int(parts[1].split(":")[0])
                if sh >= eh:
                    messagebox.showerror(
                        "Invalid Time",
                        "End time must be after start time."
                    )
                    return
            except ValueError:
                pass

        classroom = self.room_entry.get().strip() or None
        remarks   = self.notes_entry.get().strip() or None

        self.result = {
            "day":        self.day_var.get(),
            "time_slot":  slot,
            "subject_id": subject_id,
            "classroom":  classroom,
            "remarks":    remarks,
        }
        self.destroy()
