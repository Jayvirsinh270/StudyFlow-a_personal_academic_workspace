"""
Calendar Module
Month view with per-day events, colour-coded by type.
Backed by the calendar_events table.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date
from tkcalendar import Calendar

from database import (
    add_calendar_event,
    get_calendar_events,
    delete_calendar_event,
    get_timetable,
    get_setting,
    set_setting,
)
from utils.theme import (
    BG_MAIN, BG_SURFACE, BG_CARD, BG_INPUT, BG_CHIP, BG_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT, ACCENT_HOVER, ACCENT_LIGHT,
    SUCCESS, WARNING, DANGER, INFO,
    BORDER,
    PAD_SM, PAD_MD, PAD_LG, PAD_XL,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
)

# ── Event-type colour registry ────────────────────────────────────────────────
EVENT_TYPES = {
    "personal": {"light": "#4F8EF7", "dark": "#4F8EF7", "label": "Personal"},
    "academic": {"light": "#F2994A", "dark": "#F59E0B", "label": "Academic"},
    "exam":     {"light": "#EB5757", "dark": "#EF4444", "label": "Exam"},
    "holiday":  {"light": "#22C55E", "dark": "#22C55E", "label": "Holiday"},
    "reminder": {"light": "#A855F7", "dark": "#C084FC", "label": "Reminder"},
}

# Flat colour (used for calendar tag backgrounds and dot indicators)
EVENT_TYPE_COLORS = {k: v["light"] for k, v in EVENT_TYPES.items()}


def _event_dot_color(event_type: str) -> str:
    return EVENT_TYPE_COLORS.get(event_type, ACCENT[0])


def _build_day_summary(day_events: list, timetable_entries: list, day_name: str) -> str:
    """Return a short human-readable summary for the selected day."""
    ev  = len(day_events)
    cls = len(timetable_entries)
    parts = []
    if ev:
        parts.append(f"{ev} event{'s' if ev != 1 else ''}")
    if cls:
        parts.append(f"{cls} class{'es' if cls != 1 else ''}")
    if not parts:
        return "Nothing scheduled — enjoy the free time!"
    return f"{' and '.join(parts)} planned for {day_name}."


# ─────────────────────────────────────────────────────────────────────────────
class CalendarView(ctk.CTkFrame):
    """
    Calendar module: two-panel layout.
    Left  – tkcalendar month picker with event markers.
    Right – scrollable event list for the selected day + all upcoming events.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Restore last-viewed date (or fall back to today)
        saved = get_setting("calendar_selected_date")
        self.selected_date: str = saved if saved else datetime.now().strftime("%Y-%m-%d")

        self._build_ui()

        # Pre-select the restored date on the calendar widget
        try:
            y, m, d = (int(p) for p in self.selected_date.split("-"))
            self.calendar_widget.selection_set(datetime(y, m, d))
        except ValueError:
            pass

        self.after(100, self._refresh_events)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)   # left panel – fixed width
        self.grid_columnconfigure(1, weight=1)   # right panel – expands
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    # ── Left panel: month picker + legend ─────────────────────────────────────

    def _build_left_panel(self):
        panel = ctk.CTkFrame(
            self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
            border_width=1, border_color=BORDER,
        )
        panel.grid(row=0, column=0, sticky="ns", padx=(0, PAD_MD))

        # Section title
        title_row = ctk.CTkFrame(panel, fg_color="transparent")
        title_row.pack(padx=PAD_LG, pady=(PAD_LG, PAD_MD), anchor="w")
        ctk.CTkLabel(
            title_row, text="▦",
            font=ctk.CTkFont(size=17), text_color=ACCENT[1],
        ).pack(side="left", padx=(0, PAD_SM))
        ctk.CTkLabel(
            title_row, text="Calendar",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXT_PRIMARY, anchor="w",
        ).pack(side="left")

        # tkcalendar widget
        self.calendar_widget = Calendar(
            panel,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            font="Helvetica 11",
            borderwidth=0,
            relief="flat",
        )
        self.calendar_widget.pack(padx=PAD_LG, pady=(0, PAD_SM))
        self.calendar_widget.bind("<<CalendarSelected>>", self._on_date_selected)

        # Register colour tags for event markers
        for ev_type, color in EVENT_TYPE_COLORS.items():
            self.calendar_widget.tag_config(ev_type, background=color, foreground="white")

        # Legend
        legend_frame = ctk.CTkFrame(panel, fg_color="transparent")
        legend_frame.pack(padx=PAD_LG, pady=(0, PAD_LG), anchor="w")

        ctk.CTkLabel(
            legend_frame,
            text="Event Types",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, PAD_SM))

        for etype, meta in EVENT_TYPES.items():
            row = ctk.CTkFrame(legend_frame, fg_color="transparent")
            row.pack(anchor="w", pady=2)
            ctk.CTkLabel(
                row,
                text="●",
                font=ctk.CTkFont(size=11),
                text_color=meta["light"],
                width=16,
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=meta["label"],
                font=ctk.CTkFont(size=12),
                text_color=TEXT_SECONDARY,
            ).pack(side="left", padx=(4, 0))

    # ── Right panel: events list ───────────────────────────────────────────────

    def _build_right_panel(self):
        panel = ctk.CTkFrame(
            self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
            border_width=1, border_color=BORDER,
        )
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Header row (title + add button)
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=PAD_LG, pady=PAD_LG)
        hdr.grid_columnconfigure(0, weight=1)

        title_col = ctk.CTkFrame(hdr, fg_color="transparent")
        title_col.grid(row=0, column=0, rowspan=2, sticky="w")

        self.day_label = ctk.CTkLabel(
            title_col,
            text="Events",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.day_label.pack(anchor="w")

        self.event_count_label = ctk.CTkLabel(
            title_col,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        )
        self.event_count_label.pack(anchor="w")

        add_btn = ctk.CTkButton(
            hdr,
            text="＋  Add Event",
            width=140, height=36,
            corner_radius=RADIUS_SM,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._show_add_event_dialog,
        )
        add_btn.grid(row=0, column=1, rowspan=2, sticky="e")

        # Divider
        ctk.CTkFrame(panel, fg_color=BORDER, height=1).grid(
            row=1, column=0, sticky="ew", padx=PAD_LG, pady=(0, PAD_SM)
        )

        # Day summary bar
        self.summary_frame = ctk.CTkFrame(
            panel, fg_color=ACCENT_LIGHT, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER,
        )
        self.summary_frame.grid(row=2, column=0, sticky="ew", padx=PAD_LG, pady=(0, PAD_MD))
        self.summary_frame.grid_columnconfigure(0, weight=1)

        self.summary_label = ctk.CTkLabel(
            self.summary_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=ACCENT,
            anchor="w",
            wraplength=500,
        )
        self.summary_label.grid(row=0, column=0, sticky="ew", padx=PAD_MD, pady=PAD_SM)

        # Scrollable events list
        self.events_list = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.events_list.grid(row=3, column=0, sticky="nsew", padx=PAD_LG, pady=(0, PAD_LG))
        self.events_list.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

    # ── Event callbacks ────────────────────────────────────────────────────────

    def _on_date_selected(self, _event=None):
        self.selected_date = self.calendar_widget.get_date()
        set_setting("calendar_selected_date", self.selected_date)
        self._refresh_events()

    # ── Data refresh ──────────────────────────────────────────────────────────

    def _refresh_events(self):
        """Reload and render events for the selected date."""
        for w in self.events_list.winfo_children():
            w.destroy()

        # Update header date label
        try:
            display_date = datetime.strptime(self.selected_date, "%Y-%m-%d").strftime("%B %d, %Y")
        except ValueError:
            display_date = self.selected_date
        self.day_label.configure(text=f"Events — {display_date}")

        all_events: list = get_calendar_events()

        # Mark all events on the month picker
        self._mark_calendar_events(all_events)

        day_events = [e for e in all_events if e.get("event_date") == self.selected_date]
        other_events = sorted(
            [e for e in all_events if e.get("event_date") != self.selected_date],
            key=lambda e: e.get("event_date", ""),
        )

        # Update count badge
        total = len(day_events)
        self.event_count_label.configure(
            text=f"{total} event{'s' if total != 1 else ''} today" if total else "No events today"
        )

        # Update summary bar
        self._refresh_summary(day_events)

        # Today's events section
        if day_events:
            self._render_section_header("Today's Events", count=len(day_events))
            for i, event in enumerate(day_events):
                self._create_event_card(event, alternate=i % 2 == 1)
        else:
            self._render_empty_state()

        # Upcoming / all-other events section
        if other_events:
            self._render_section_header("All Other / Upcoming Events", count=len(other_events), top_pad=PAD_LG)
            for i, event in enumerate(other_events):
                self._create_event_card(event, show_date=True, alternate=i % 2 == 1)

    def _mark_calendar_events(self, all_events: list):
        try:
            self.calendar_widget.calevent_remove("all")
            for ev in all_events:
                raw = ev.get("event_date")
                if not raw:
                    continue
                try:
                    e_date = datetime.strptime(raw, "%Y-%m-%d").date()
                    ev_type = ev.get("event_type", "personal")
                    self.calendar_widget.calevent_create(e_date, ev.get("title", ""), ev_type)
                except ValueError:
                    pass
        except Exception:
            pass

    def _refresh_summary(self, day_events: list):
        try:
            day_name = datetime.strptime(self.selected_date, "%Y-%m-%d").strftime("%A")
        except ValueError:
            day_name = "this day"

        timetable = get_timetable()
        classes = [c for c in timetable if c.get("day") == day_name]
        text = _build_day_summary(day_events, classes, day_name)
        self.summary_label.configure(text=text)

    # ── Rendering helpers ─────────────────────────────────────────────────────

    def _render_section_header(self, title: str, count: int = 0, top_pad: int = 0):
        hdr = ctk.CTkFrame(self.events_list, fg_color="transparent")
        hdr.pack(fill="x", pady=(top_pad, PAD_SM))

        ctk.CTkLabel(
            hdr,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        if count:
            badge = ctk.CTkLabel(
                hdr,
                text=str(count),
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=ACCENT,
                fg_color=ACCENT_LIGHT,
                corner_radius=RADIUS_SM,
                width=24,
                height=20,
            )
            badge.pack(side="left", padx=(PAD_SM, 0))

    def _render_empty_state(self):
        empty = ctk.CTkFrame(
            self.events_list,
            fg_color=BG_CHIP,
            corner_radius=RADIUS_MD,
        )
        empty.pack(fill="x", pady=PAD_SM)

        ctk.CTkLabel(
            empty,
            text="🗓  No events for this day.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(padx=PAD_LG, pady=PAD_MD, anchor="w")

        ctk.CTkLabel(
            empty,
            text='Click "+ Add Event" to create one.',
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(padx=PAD_LG, pady=(0, PAD_MD), anchor="w")

    def _create_event_card(
        self,
        event: dict,
        row: int = None,
        show_date: bool = False,
        alternate: bool = False,
    ):
        """Render a single event card with type dot, title, description and delete button."""
        card_bg = BG_CHIP if alternate else BG_CARD
        card = ctk.CTkFrame(self.events_list, fg_color=card_bg, corner_radius=RADIUS_MD)
        card.pack(fill="x", pady=(0, PAD_SM))
        card.grid_columnconfigure(1, weight=1)

        # Colour accent strip on left edge
        ev_type = event.get("event_type", "personal")
        dot_color = _event_dot_color(ev_type)

        strip = ctk.CTkFrame(card, fg_color=dot_color, width=4, corner_radius=0)
        strip.grid(row=0, column=0, sticky="ns", padx=(0, PAD_MD), pady=0, rowspan=2)

        # Type badge chip
        type_badge = ctk.CTkLabel(
            card,
            text=EVENT_TYPES.get(ev_type, {}).get("label", ev_type).upper(),
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=dot_color,
            fg_color=BG_CHIP,
            corner_radius=RADIUS_SM,
            height=18,
            padx=PAD_SM,
        )
        type_badge.grid(row=0, column=1, sticky="w", padx=(0, PAD_SM), pady=(PAD_MD, 2))

        # Title (+ date when in "all other events" list)
        title_text = event.get("title", "Untitled")
        if show_date and event.get("event_date"):
            try:
                d = datetime.strptime(event["event_date"], "%Y-%m-%d").strftime("%b %d")
                title_text = f"{title_text}  ·  {d}"
            except ValueError:
                title_text = f"{title_text}  ({event['event_date']})"

        ctk.CTkLabel(
            card,
            text=title_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", padx=(0, PAD_SM), pady=(0, PAD_SM))

        # Description (optional)
        if event.get("description"):
            ctk.CTkLabel(
                card,
                text=event["description"],
                font=ctk.CTkFont(size=12),
                text_color=TEXT_SECONDARY,
                anchor="w",
                wraplength=420,
            ).grid(row=2, column=1, sticky="ew", padx=(0, PAD_SM), pady=(0, PAD_MD))

        # Delete button
        del_btn = ctk.CTkButton(
            card,
            text="Delete",
            width=72,
            height=28,
            corner_radius=RADIUS_SM,
            fg_color="transparent",
            border_width=1,
            border_color=DANGER[0],
            text_color=DANGER[0],
            hover_color=("#FEE2E2", "#450A0A"),
            font=ctk.CTkFont(size=12),
            command=lambda eid=event["id"]: self._delete_event(eid),
        )
        del_btn.grid(row=0, column=2, rowspan=3, padx=PAD_MD, pady=PAD_MD, sticky="e")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _delete_event(self, event_id: int):
        if messagebox.askyesno(
            "Delete Event",
            "Are you sure you want to delete this event?",
            icon="warning",
        ):
            delete_calendar_event(event_id)
            self._refresh_events()

    def _show_add_event_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Event")
        dialog.geometry("420x560")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.lift()

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=0)

        # ── Scrollable form ──────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_LG, pady=(PAD_LG, PAD_SM))
        scroll.grid_columnconfigure(0, weight=1)

        def field_label(parent, text: str):
            ctk.CTkLabel(
                parent,
                text=text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_SECONDARY,
                anchor="w",
            ).pack(fill="x", pady=(0, 4))

        # Title field
        field_label(scroll, "Event Title *")
        title_entry = ctk.CTkEntry(
            scroll,
            height=40,
            corner_radius=RADIUS_SM,
            fg_color=BG_INPUT,
            border_color=BORDER,
            placeholder_text="e.g. Mid-term Exam",
            font=ctk.CTkFont(size=13),
        )
        title_entry.pack(fill="x", pady=(0, PAD_MD))

        # Date picker
        field_label(scroll, "Date *")
        date_picker = Calendar(
            scroll,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            font="Helvetica 11",
        )
        try:
            y, m, d = (int(p) for p in self.selected_date.split("-"))
            date_picker.selection_set(datetime(y, m, d))
        except ValueError:
            pass
        date_picker.pack(pady=(0, PAD_MD))

        # Event type
        field_label(scroll, "Event Type")
        type_menu = ctk.CTkOptionMenu(
            scroll,
            values=list(EVENT_TYPES.keys()),
            height=40,
            corner_radius=RADIUS_SM,
            fg_color=BG_INPUT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=13),
        )
        type_menu.set("personal")
        type_menu.pack(fill="x", pady=(0, PAD_MD))

        # Description
        field_label(scroll, "Description (optional)")
        description_entry = ctk.CTkEntry(
            scroll,
            height=40,
            corner_radius=RADIUS_SM,
            fg_color=BG_INPUT,
            border_color=BORDER,
            placeholder_text="Short notes about this event",
            font=ctk.CTkFont(size=13),
        )
        description_entry.pack(fill="x", pady=(0, PAD_MD))

        # ── Bottom buttons ────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=PAD_LG, pady=(0, PAD_LG))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=110,
            height=40,
            corner_radius=RADIUS_MD,
            fg_color=BG_CHIP,
            hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=13),
            command=dialog.destroy,
        ).pack(side="right", padx=(PAD_SM, 0))

        def _save():
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning(
                    "Missing Title",
                    "Please enter a title for the event.",
                    parent=dialog,
                )
                return

            event_date  = date_picker.get_date()
            event_type  = type_menu.get()
            description = description_entry.get().strip() or None

            try:
                add_calendar_event(
                    title=title,
                    event_date=event_date,
                    event_type=event_type,
                    description=description,
                )
            except Exception as exc:
                messagebox.showerror("Save Failed", str(exc), parent=dialog)
                return

            dialog.destroy()

            # Navigate calendar view to the newly created event's date
            self.selected_date = event_date
            set_setting("calendar_selected_date", self.selected_date)
            try:
                y, m, d = (int(p) for p in event_date.split("-"))
                self.calendar_widget.selection_set(datetime(y, m, d))
            except Exception:
                pass
            self._refresh_events()

        ctk.CTkButton(
            btn_row,
            text="Save Event",
            width=130,
            height=40,
            corner_radius=RADIUS_MD,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=_save,
        ).pack(side="right")
