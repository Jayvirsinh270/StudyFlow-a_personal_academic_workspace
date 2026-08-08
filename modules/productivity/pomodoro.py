"""
Pomodoro Timer Module — production-ready focus timer for StudyFlow.
"""

import customtkinter as ctk
from tkinter import messagebox
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_CHIP, BG_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT, ACCENT_HOVER,
    SUCCESS, WARNING, DANGER, BORDER,
    PAD_SM, PAD_MD, PAD_LG, PAD_XL, RADIUS_SM, RADIUS_MD, RADIUS_LG,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL, FONT_2XL,
)


def _font(size=FONT_MD, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

def _bold(size=FONT_MD) -> ctk.CTkFont:
    return _font(size, "bold")


class PomodoroTimer(ctk.CTkFrame):
    """Pomodoro timer with work/break sessions, custom durations, and session history."""

    _WORK_DEFAULT  = 25
    _BREAK_DEFAULT = 5

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

        self.work_minutes  = self._WORK_DEFAULT
        self.break_minutes = self._BREAK_DEFAULT
        self._reset_state()
        self._build()

    # ── State helpers ─────────────────────────────────────────────────────────
    def _reset_state(self):
        self.timer_running  = False
        self.timer_paused   = False
        self.is_work        = True
        self.current_time   = self.work_minutes * 60
        self.sessions_done  = 0
        self.total_focus    = 0
        self._job           = None

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        outer = ctk.CTkScrollableFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True)

        # ── Title card ───────────────────────────────────────────────────────
        title_card = ctk.CTkFrame(outer, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
                                  border_width=1, border_color=BORDER)
        title_card.pack(fill="x", pady=(0, PAD_MD))
        ctk.CTkLabel(title_card, text="◷  Focus Timer",
                     font=_bold(FONT_XL),
                     text_color=TEXT_PRIMARY).pack(side="left", padx=PAD_LG, pady=PAD_MD)
        ctk.CTkLabel(title_card, text="Pomodoro technique — 25 min focus · 5 min break",
                     font=_font(FONT_SM),
                     text_color=TEXT_MUTED).pack(side="left")

        # ── Main timer card ───────────────────────────────────────────────────
        timer_card = ctk.CTkFrame(outer, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
                                  border_width=1, border_color=BORDER)
        timer_card.pack(fill="x", pady=(0, PAD_MD))

        inner = ctk.CTkFrame(timer_card, fg_color="transparent")
        inner.pack(padx=PAD_XL, pady=PAD_XL)

        # Session type label
        self._session_lbl = ctk.CTkLabel(
            inner, text="Work Session",
            font=_bold(FONT_LG),
            text_color=ACCENT[1],
        )
        self._session_lbl.pack(pady=(0, PAD_SM))

        # Big timer display
        timer_bg = ctk.CTkFrame(inner, fg_color=BG_CARD, corner_radius=20,
                                width=260, height=130)
        timer_bg.pack()
        timer_bg.pack_propagate(False)

        self._time_lbl = ctk.CTkLabel(
            timer_bg, text="25:00",
            font=_bold(72),
            text_color=TEXT_PRIMARY,
        )
        self._time_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Progress bar
        self._progress = ctk.CTkProgressBar(
            inner, height=8, corner_radius=4, progress_color=ACCENT[1],
        )
        self._progress.set(1.0)
        self._progress.pack(fill="x", pady=(PAD_MD, 0))

        # Status text
        self._status_lbl = ctk.CTkLabel(
            inner, text="Ready to focus — press Start when you're set.",
            font=_font(FONT_SM),
            text_color=TEXT_MUTED,
        )
        self._status_lbl.pack(pady=(PAD_SM, PAD_MD))

        # Control buttons
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(pady=(0, PAD_SM))

        self._start_btn = ctk.CTkButton(
            btn_row, text="▶  Start",
            width=110, height=44, corner_radius=RADIUS_MD,
            fg_color=SUCCESS[1], hover_color=SUCCESS[0],
            text_color=("#FFFFFF", "#FFFFFF"),
            font=_bold(FONT_LG),
            command=self._start,
        )
        self._start_btn.pack(side="left", padx=PAD_SM)

        self._pause_btn = ctk.CTkButton(
            btn_row, text="⏸  Pause",
            width=110, height=44, corner_radius=RADIUS_MD,
            fg_color=WARNING[1], hover_color=WARNING[0],
            text_color=("#FFFFFF", "#FFFFFF"),
            font=_bold(FONT_LG),
            command=self._pause, state="disabled",
        )
        self._pause_btn.pack(side="left", padx=PAD_SM)

        self._reset_btn = ctk.CTkButton(
            btn_row, text="↺  Reset",
            width=110, height=44, corner_radius=RADIUS_MD,
            fg_color=DANGER[1], hover_color=DANGER[0],
            text_color=("#FFFFFF", "#FFFFFF"),
            font=_bold(FONT_LG),
            command=self._reset,
        )
        self._reset_btn.pack(side="left", padx=PAD_SM)

        # ── Stats row ─────────────────────────────────────────────────────────
        stats_row = ctk.CTkFrame(inner, fg_color="transparent")
        stats_row.pack(fill="x")

        self._sessions_lbl = ctk.CTkLabel(
            stats_row, text="Sessions: 0",
            font=_font(FONT_SM),
            text_color=TEXT_SECONDARY,
        )
        self._sessions_lbl.pack(side="left")

        self._focus_lbl = ctk.CTkLabel(
            stats_row, text="Focus time: 0 min",
            font=_font(FONT_SM),
            text_color=TEXT_SECONDARY,
        )
        self._focus_lbl.pack(side="right")

        # ── Custom duration card ──────────────────────────────────────────────
        dur_card = ctk.CTkFrame(outer, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
                                border_width=1, border_color=BORDER)
        dur_card.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(dur_card, text="Custom Durations",
                     font=_bold(FONT_LG),
                     text_color=TEXT_PRIMARY).pack(anchor="w", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        dur_inner = ctk.CTkFrame(dur_card, fg_color="transparent")
        dur_inner.pack(fill="x", padx=PAD_LG, pady=(0, PAD_MD))

        ctk.CTkLabel(dur_inner, text="Work (min):",
                     font=_font(FONT_SM), text_color=TEXT_SECONDARY).pack(side="left")
        self._work_entry = ctk.CTkEntry(
            dur_inner, width=56, height=34, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER, fg_color=BG_CHIP,
            text_color=TEXT_PRIMARY,
        )
        self._work_entry.insert(0, str(self.work_minutes))
        self._work_entry.pack(side="left", padx=(PAD_SM, PAD_LG))

        ctk.CTkLabel(dur_inner, text="Break (min):",
                     font=_font(FONT_SM), text_color=TEXT_SECONDARY).pack(side="left")
        self._break_entry = ctk.CTkEntry(
            dur_inner, width=56, height=34, corner_radius=RADIUS_SM,
            border_width=1, border_color=BORDER, fg_color=BG_CHIP,
            text_color=TEXT_PRIMARY,
        )
        self._break_entry.insert(0, str(self.break_minutes))
        self._break_entry.pack(side="left", padx=(PAD_SM, PAD_LG))

        ctk.CTkButton(
            dur_inner, text="Apply", height=34, width=72, corner_radius=RADIUS_SM,
            fg_color=ACCENT[1], hover_color=ACCENT_HOVER[1],
            text_color=("#FFFFFF", "#FFFFFF"),
            font=_bold(FONT_SM),
            command=self._apply_custom_durations,
        ).pack(side="left")

        # ── Tips card ─────────────────────────────────────────────────────────
        tips_card = ctk.CTkFrame(outer, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
                                 border_width=1, border_color=BORDER)
        tips_card.pack(fill="x", pady=(0, PAD_MD))
        ctk.CTkLabel(
            tips_card,
            text=(
                "⚡  Pomodoro Tips\n\n"
                "  • Work on a single task for the full 25 minutes\n"
                "  • Note distractions on paper and return to focus\n"
                "  • After 4 pomodoros take a longer 15–30 min break\n"
                "  • Keep your phone face-down during work sessions"
            ),
            font=_font(FONT_SM),
            text_color=TEXT_SECONDARY,
            justify="left", anchor="w",
        ).pack(anchor="w", padx=PAD_LG, pady=PAD_MD)

    # ── Timer logic ───────────────────────────────────────────────────────────
    def _start(self):
        if not self.timer_running:
            self.timer_running = True
            self.timer_paused  = False
            self._start_btn.configure(state="disabled")
            self._pause_btn.configure(state="normal", text="⏸  Pause")
            self._status_lbl.configure(text="Stay focused — one task, full block.")
            self._tick()

    def _pause(self):
        if self.timer_running and not self.timer_paused:
            self.timer_paused = True
            self._pause_btn.configure(text="▶  Resume", command=self._resume)
            self._status_lbl.configure(text="Paused — take a breath and resume when ready.")
            if self._job:
                self.after_cancel(self._job)

    def _resume(self):
        if self.timer_paused:
            self.timer_paused = False
            self._pause_btn.configure(text="⏸  Pause", command=self._pause)
            self._status_lbl.configure(text="Back in focus mode.")
            self._tick()

    def _reset(self):
        if self._job:
            self.after_cancel(self._job)
        self.is_work      = True
        self.current_time = self.work_minutes * 60
        self.timer_running = False
        self.timer_paused  = False

        self._time_lbl.configure(text=f"{self.work_minutes:02d}:00")
        self._session_lbl.configure(text="Work Session", text_color=ACCENT[1])
        self._progress.set(1.0)
        self._progress.configure(progress_color=ACCENT[1])
        self._status_lbl.configure(text="Timer reset — ready for a new session.")
        self._start_btn.configure(state="normal")
        self._pause_btn.configure(state="disabled", text="⏸  Pause", command=self._pause)

    def _tick(self):
        if not (self.timer_running and not self.timer_paused):
            return
        if self.current_time > 0:
            self.current_time -= 1
            self._update_display()
            self._job = self.after(1000, self._tick)
        else:
            self._session_end()

    def _update_display(self):
        m, s = divmod(self.current_time, 60)
        self._time_lbl.configure(text=f"{m:02d}:{s:02d}")
        total = (self.work_minutes if self.is_work else self.break_minutes) * 60
        self._progress.set(self.current_time / total if total else 0)

    def _session_end(self):
        self.timer_running = False
        if self.is_work:
            self.sessions_done += 1
            self.total_focus   += self.work_minutes
            self._sessions_lbl.configure(text=f"Sessions: {self.sessions_done}")
            self._focus_lbl.configure(text=f"Focus time: {self.total_focus} min")
            self.is_work      = False
            self.current_time = self.break_minutes * 60
            self._session_lbl.configure(text="Break Time 🎉", text_color=SUCCESS[1])
            self._progress.configure(progress_color=SUCCESS[1])
            self._status_lbl.configure(text="Great work! Enjoy your break.")
            messagebox.showinfo("Session Complete!",
                                f"Pomodoro #{self.sessions_done} complete!\n\n"
                                f"Take a {self.break_minutes}-minute break, then come back strong.")
        else:
            self.is_work      = True
            self.current_time = self.work_minutes * 60
            self._session_lbl.configure(text="Work Session", text_color=ACCENT[1])
            self._progress.configure(progress_color=ACCENT[1])
            self._status_lbl.configure(text="Break over — ready for the next sprint!")
            messagebox.showinfo("Break Over!", "Time to focus again. Start your next session!")

        self._update_display()
        self._start_btn.configure(state="normal")
        self._pause_btn.configure(state="disabled", text="⏸  Pause", command=self._pause)

    def _apply_custom_durations(self):
        if self.timer_running:
            messagebox.showwarning("Timer Running", "Stop the timer before changing durations.")
            return
        try:
            w = int(self._work_entry.get().strip())
            b = int(self._break_entry.get().strip())
            if not (1 <= w <= 120) or not (1 <= b <= 60):
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Duration", "Work: 1–120 min, Break: 1–60 min.")
            return
        self.work_minutes  = w
        self.break_minutes = b
        self._reset()
