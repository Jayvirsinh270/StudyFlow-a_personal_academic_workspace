"""
StudyFlow Reusable Widgets Library
Premium, modular UI components inspired by Notion, Linear, and Todoist.
All widgets follow the StudyFlow design system.
"""

import customtkinter as ctk
from typing import Callable, Optional, Any
from utils.theme import (
    BG_SURFACE, BG_CARD, BG_CHIP, BG_HOVER, BG_INPUT, BG_OVERLAY,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    ACCENT, ACCENT_HOVER, ACCENT_LIGHT, ACCENT_SUBTLE,
    SUCCESS, WARNING, DANGER, BORDER, BORDER_FOCUS,
    PAD_XS, PAD_SM, PAD_MD, PAD_LG, PAD_XL,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
    FONT_FAMILY, FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL, FONT_2XL, FONT_3XL,
    priority_color, attendance_color,
)


# ── Typography helpers ─────────────────────────────────────────────────────────

def font(size: int = FONT_MD, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def bold(size: int = FONT_MD) -> ctk.CTkFont:
    return font(size, "bold")


# ── StatCard ──────────────────────────────────────────────────────────────────

class StatCard(ctk.CTkFrame):
    """Premium stat card with icon, value, label, and optional trend indicator."""

    def __init__(self, master, label: str, icon: str, color: str,
                 value: str = "—", subtitle: str = "", **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_LG,
            border_width=1,
            border_color=BORDER,
        )
        self._color = color
        self._build(label, icon, color, value, subtitle)

    def _build(self, label, icon, color, value, subtitle):
        # Top row: icon + value
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=PAD_MD, pady=(PAD_MD, PAD_XS))

        # Icon circle
        icon_frame = ctk.CTkFrame(
            top, fg_color=BG_CHIP,  # transparent tint
            corner_radius=RADIUS_SM,
            width=38, height=38,
        )
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(
            icon_frame, text=icon,
            font=font(FONT_LG), text_color=color,
        ).place(relx=0.5, rely=0.5, anchor="center")

        self._val_lbl = ctk.CTkLabel(
            top, text=value,
            font=bold(FONT_2XL), text_color=color,
        )
        self._val_lbl.pack(side="right")

        # Label row
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(fill="x", padx=PAD_MD, pady=(0, PAD_MD))
        ctk.CTkLabel(
            bot, text=label,
            font=font(FONT_SM), text_color=TEXT_MUTED,
        ).pack(side="left", anchor="w")

        if subtitle:
            self._sub_lbl = ctk.CTkLabel(
                bot, text=subtitle,
                font=font(FONT_XS), text_color=TEXT_MUTED,
            )
            self._sub_lbl.pack(side="right", anchor="e")
        else:
            self._sub_lbl = None

    def update(self, value: str, subtitle: str = None, color: str = None):
        c = color or self._color
        self._val_lbl.configure(text=value, text_color=c)
        if subtitle is not None and self._sub_lbl:
            self._sub_lbl.configure(text=subtitle)


# ── SectionCard ───────────────────────────────────────────────────────────────

class SectionCard(ctk.CTkFrame):
    """Card with a titled header area and content body."""

    def __init__(self, master, title: str = "", subtitle: str = "",
                 action_text: str = "", action_command: Callable = None,
                 icon: str = "", **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_LG,
            border_width=1,
            border_color=BORDER,
        )
        self.body = None
        if title:
            self._build_header(title, subtitle, action_text, action_command, icon)
        self._build_body()

    def _build_header(self, title, subtitle, action_text, action_command, icon):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, 0))

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left")

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")

        if icon:
            ctk.CTkLabel(
                title_row, text=icon,
                font=font(FONT_LG), text_color=ACCENT[1],
            ).pack(side="left", padx=(0, PAD_XS))

        ctk.CTkLabel(
            title_row, text=title,
            font=bold(FONT_LG), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        if subtitle:
            ctk.CTkLabel(
                left, text=subtitle,
                font=font(FONT_SM), text_color=TEXT_MUTED,
            ).pack(anchor="w", pady=(2, 0))

        if action_text and action_command:
            PrimaryButton(
                hdr, text=action_text, command=action_command,
                height=32, width=130,
            ).pack(side="right")

        # Divider
        ctk.CTkFrame(self, fg_color=BORDER, height=1).pack(fill="x", padx=PAD_LG, pady=(PAD_SM, 0))

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)


# ── RowItem ───────────────────────────────────────────────────────────────────

class RowItem(ctk.CTkFrame):
    """Standard list row with left dot, title, subtitle, and right badge."""

    def __init__(self, master, title: str, subtitle: str = "",
                 right_text: str = "", right_color: str = None,
                 dot_color: str = None, icon: str = "", **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=RADIUS_SM, **kwargs)

        if dot_color:
            bar = ctk.CTkFrame(self, fg_color=dot_color, width=4, corner_radius=0)
            bar.pack(side="left", fill="y")

        if icon:
            ctk.CTkLabel(
                self, text=icon,
                font=font(FONT_MD), text_color=ACCENT[1], width=32,
            ).pack(side="left", padx=(PAD_SM, 0), pady=PAD_SM)

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=PAD_MD, pady=PAD_SM)

        if subtitle:
            ctk.CTkLabel(
                info, text=subtitle,
                font=font(FONT_XS), text_color=TEXT_MUTED, anchor="w",
            ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=title,
            font=bold(FONT_MD), text_color=TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")

        if right_text:
            ctk.CTkLabel(
                self, text=right_text,
                font=bold(FONT_SM), text_color=right_color or TEXT_SECONDARY,
            ).pack(side="right", padx=PAD_MD)

        # Hover effect
        self.bind("<Enter>", lambda e: self.configure(fg_color=BG_HOVER))
        self.bind("<Leave>", lambda e: self.configure(fg_color=BG_CARD))


# ── PrimaryButton ─────────────────────────────────────────────────────────────

class PrimaryButton(ctk.CTkButton):
    """Blue primary action button with consistent styling."""

    def __init__(self, master, text: str = "Button", icon: str = "",
                 command: Callable = None, width: int = 120, height: int = 38,
                 **kwargs):
        label = f"{icon}  {text}" if icon else text
        super().__init__(
            master,
            text=label,
            width=width,
            height=height,
            corner_radius=RADIUS_SM,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            font=bold(FONT_MD),
            command=command,
            **kwargs,
        )


# ── SecondaryButton ───────────────────────────────────────────────────────────

class SecondaryButton(ctk.CTkButton):
    """Ghost/secondary button with border."""

    def __init__(self, master, text: str = "Button", icon: str = "",
                 command: Callable = None, width: int = 100, height: int = 38,
                 **kwargs):
        label = f"{icon}  {text}" if icon else text
        super().__init__(
            master,
            text=label,
            width=width,
            height=height,
            corner_radius=RADIUS_SM,
            fg_color=BG_CHIP,
            hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BORDER,
            font=font(FONT_MD),
            command=command,
            **kwargs,
        )


# ── DangerButton ──────────────────────────────────────────────────────────────

class DangerButton(ctk.CTkButton):
    """Red danger button with confirmation support."""

    def __init__(self, master, text: str = "Delete", icon: str = "✕",
                 command: Callable = None, confirm: bool = True,
                 confirm_message: str = "Are you sure?",
                 width: int = 90, height: int = 34, **kwargs):
        self._real_command = command
        self._confirm = confirm
        self._confirm_msg = confirm_message
        label = f"{icon}  {text}" if icon else text
        super().__init__(
            master,
            text=label,
            width=width,
            height=height,
            corner_radius=RADIUS_SM,
            fg_color=("#FEE2E2", "#450A0A"),
            hover_color=("#FECACA", "#7F1D1D"),
            text_color=DANGER[0],
            font=font(FONT_SM),
            command=self._handle_click,
            **kwargs,
        )

    def _handle_click(self):
        if self._confirm:
            from tkinter import messagebox
            if not messagebox.askyesno("Confirm", self._confirm_msg):
                return
        if self._real_command:
            self._real_command()


# ── IconButton ────────────────────────────────────────────────────────────────

class IconButton(ctk.CTkButton):
    """Small square icon-only button."""

    def __init__(self, master, icon: str = "✎", color: str = None,
                 command: Callable = None, size: int = 32, **kwargs):
        super().__init__(
            master,
            text=icon,
            width=size,
            height=size,
            corner_radius=RADIUS_SM,
            fg_color=BG_CHIP,
            hover_color=BG_HOVER,
            text_color=color or TEXT_PRIMARY,
            font=font(FONT_MD),
            command=command,
            **kwargs,
        )


# ── SearchBar ─────────────────────────────────────────────────────────────────

class SearchBar(ctk.CTkFrame):
    """Styled search input with icon."""

    def __init__(self, master, placeholder: str = "Search…",
                 on_change: Callable = None, **kwargs):
        super().__init__(
            master,
            fg_color=BG_INPUT,
            corner_radius=RADIUS_MD,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )
        self._on_change = on_change

        ctk.CTkLabel(
            self, text="⊘",
            font=font(FONT_MD), text_color=TEXT_MUTED, width=30,
        ).pack(side="left", padx=(PAD_SM, 0))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            font=font(FONT_MD),
            height=36,
            corner_radius=RADIUS_MD,
            border_width=0,
            fg_color="transparent",
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
        )
        self.entry.pack(fill="both", expand=True, padx=(4, PAD_SM))

        if on_change:
            self.entry.bind("<KeyRelease>", lambda e: on_change(self.entry.get()))

    def get(self) -> str:
        return self.entry.get()


# ── FormField ─────────────────────────────────────────────────────────────────

class FormField(ctk.CTkFrame):
    """Labeled form field with validation state."""

    def __init__(self, master, label: str, placeholder: str = "",
                 required: bool = False, icon: str = "",
                 widget_type: str = "entry", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Label
        lbl_text = f"{label} {'*' if required else ''}"
        label_row = ctk.CTkFrame(self, fg_color="transparent")
        label_row.pack(fill="x", pady=(0, 4))

        if icon:
            ctk.CTkLabel(
                label_row, text=icon,
                font=font(FONT_SM), text_color=ACCENT[1], width=18,
            ).pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            label_row, text=lbl_text,
            font=font(FONT_SM), text_color=TEXT_SECONDARY, anchor="w",
        ).pack(side="left")

        if widget_type == "textbox":
            self.widget = ctk.CTkTextbox(
                self, height=80,
                corner_radius=RADIUS_SM,
                border_width=1, border_color=BORDER,
                fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
                wrap="word",
            )
        else:
            self.widget = ctk.CTkEntry(
                self,
                placeholder_text=placeholder,
                height=40,
                corner_radius=RADIUS_SM,
                border_width=1, border_color=BORDER,
                fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
                placeholder_text_color=TEXT_MUTED,
            )

        self.widget.pack(fill="x")

        self._error_lbl = ctk.CTkLabel(
            self, text="",
            font=font(FONT_XS), text_color=DANGER[1], anchor="w",
        )
        self._error_lbl.pack(anchor="w")

    def get(self) -> str:
        if isinstance(self.widget, ctk.CTkTextbox):
            return self.widget.get("1.0", "end-1c").strip()
        return self.widget.get().strip()

    def insert(self, text: str):
        if isinstance(self.widget, ctk.CTkTextbox):
            self.widget.delete("1.0", "end")
            self.widget.insert("1.0", text)
        else:
            self.widget.delete(0, "end")
            self.widget.insert(0, text)

    def set_error(self, msg: str = ""):
        self._error_lbl.configure(text=msg)
        color = DANGER[1] if msg else BORDER
        self.widget.configure(border_color=color)

    def clear_error(self):
        self.set_error("")


# ── StatusBadge ───────────────────────────────────────────────────────────────

class StatusBadge(ctk.CTkLabel):
    """Colored status chip/badge."""

    _COLORS = {
        "pending":   (("#FEF3C7", "#451A03"), ("#D97706", "#F59E0B")),
        "completed": (("#F0FDF4", "#052E16"), ("#16A34A", "#22C55E")),
        "overdue":   (("#FEF2F2", "#450A0A"), ("#DC2626", "#EF4444")),
        "good":      (("#F0FDF4", "#052E16"), ("#16A34A", "#22C55E")),
        "warning":   (("#FEF3C7", "#451A03"), ("#D97706", "#F59E0B")),
        "critical":  (("#FEF2F2", "#450A0A"), ("#DC2626", "#EF4444")),
        "high":      (("#FEF2F2", "#450A0A"), ("#DC2626", "#EF4444")),
        "medium":    (("#FEF3C7", "#451A03"), ("#D97706", "#F59E0B")),
        "low":       (("#F0FDF4", "#052E16"), ("#16A34A", "#22C55E")),
    }

    def __init__(self, master, status: str, **kwargs):
        bg_colors, text_colors = self._COLORS.get(status.lower(),
            ((BG_CHIP, BG_CHIP), (TEXT_SECONDARY, TEXT_SECONDARY)))
        super().__init__(
            master,
            text=status.title(),
            font=bold(FONT_XS),
            fg_color=bg_colors,
            text_color=text_colors,
            corner_radius=RADIUS_SM,
            padx=8, pady=2,
            **kwargs,
        )


# ── ProgressCard ──────────────────────────────────────────────────────────────

class ProgressCard(ctk.CTkFrame):
    """Subject attendance/progress card with progress bar."""

    def __init__(self, master, name: str, percentage: float,
                 detail: str = "", color: str = None, **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=RADIUS_SM, **kwargs)

        pct_color = color or attendance_color(percentage)

        # Left accent strip
        strip = ctk.CTkFrame(self, fg_color=pct_color, width=4, corner_radius=0)
        strip.pack(side="left", fill="y")

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=PAD_MD, pady=PAD_SM)

        ctk.CTkLabel(
            content, text=name,
            font=bold(FONT_MD), text_color=TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")

        if detail:
            ctk.CTkLabel(
                content, text=detail,
                font=font(FONT_XS), text_color=TEXT_MUTED, anchor="w",
            ).pack(anchor="w", pady=(2, 4))

        bar = ctk.CTkProgressBar(
            content, height=6, corner_radius=3,
            fg_color=BG_INPUT, progress_color=pct_color,
        )
        bar.set(min(percentage / 100.0, 1.0))
        bar.pack(fill="x", pady=(4, 0))

        # Right: percentage
        ctk.CTkLabel(
            self, text=f"{percentage:.0f}%",
            font=bold(FONT_LG), text_color=pct_color, width=52,
        ).pack(side="right", padx=PAD_MD)

        # Hover
        self.bind("<Enter>", lambda e: self.configure(fg_color=BG_HOVER))
        self.bind("<Leave>", lambda e: self.configure(fg_color=BG_CARD))


# ── EmptyState ────────────────────────────────────────────────────────────────

class EmptyState(ctk.CTkFrame):
    """Empty state illustration with icon, title, subtitle, and optional CTA."""

    def __init__(self, master, icon: str = "⊟", title: str = "Nothing here yet",
                 subtitle: str = "", action_text: str = "",
                 action_command: Callable = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        # Large icon
        icon_frame = ctk.CTkFrame(
            inner, fg_color=BG_CHIP,
            corner_radius=RADIUS_XL,
            width=72, height=72,
        )
        icon_frame.pack()
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(
            icon_frame, text=icon,
            font=font(FONT_3XL), text_color=TEXT_MUTED,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text=title,
            font=bold(FONT_XL), text_color=TEXT_PRIMARY,
        ).pack(pady=(PAD_MD, PAD_XS))

        if subtitle:
            ctk.CTkLabel(
                inner, text=subtitle,
                font=font(FONT_MD), text_color=TEXT_MUTED,
                wraplength=280, justify="center",
            ).pack()

        if action_text and action_command:
            PrimaryButton(
                inner, text=action_text, icon="＋",
                command=action_command, width=180, height=42,
            ).pack(pady=PAD_MD)


# ── PageHeader ────────────────────────────────────────────────────────────────

class PageHeader(ctk.CTkFrame):
    """Consistent page header with title, subtitle, and optional action button."""

    def __init__(self, master, title: str, subtitle: str = "",
                 action_text: str = "", action_command: Callable = None,
                 icon: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_LG,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)

        left = ctk.CTkFrame(wrap, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")

        if icon:
            ctk.CTkLabel(
                title_row, text=icon,
                font=font(FONT_XL), text_color=ACCENT[1],
            ).pack(side="left", padx=(0, PAD_SM))

        ctk.CTkLabel(
            title_row, text=title,
            font=bold(FONT_XL), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        if subtitle:
            ctk.CTkLabel(
                left, text=subtitle,
                font=font(FONT_SM), text_color=TEXT_MUTED,
            ).pack(anchor="w", pady=(2, 0))

        if action_text and action_command:
            PrimaryButton(
                wrap, text=action_text, icon="＋",
                command=action_command, height=38,
            ).pack(side="right", padx=(PAD_MD, 0))


# ── Divider ───────────────────────────────────────────────────────────────────

class Divider(ctk.CTkFrame):
    """Horizontal divider line."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BORDER, height=1, **kwargs)


# ── ToastNotification ─────────────────────────────────────────────────────────

class Toast(ctk.CTkFrame):
    """Temporary toast notification that auto-dismisses."""

    def __init__(self, master, message: str, type_: str = "success",
                 duration: int = 3000):
        super().__init__(
            master,
            fg_color=BG_SURFACE,
            corner_radius=RADIUS_MD,
            border_width=1,
            border_color=BORDER,
        )

        colors = {
            "success": SUCCESS[1],
            "error": DANGER[1],
            "warning": WARNING[1],
            "info": ACCENT[1],
        }
        icons = {
            "success": "✓",
            "error": "✕",
            "warning": "⚠",
            "info": "ℹ",
        }

        color = colors.get(type_, ACCENT[1])
        icon = icons.get(type_, "ℹ")

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=PAD_MD, pady=PAD_SM)

        ctk.CTkLabel(
            inner, text=icon,
            font=bold(FONT_MD), text_color=color,
        ).pack(side="left", padx=(0, PAD_SM))

        ctk.CTkLabel(
            inner, text=message,
            font=font(FONT_MD), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self.place(relx=0.5, rely=0.95, anchor="s")
        self.after(duration, self._dismiss)

    def _dismiss(self):
        try:
            self.place_forget()
            self.destroy()
        except Exception:
            pass


# ── QuickActionButton ─────────────────────────────────────────────────────────

class QuickActionButton(ctk.CTkFrame):
    """Large quick action tile used on dashboard."""

    def __init__(self, master, text: str, icon: str, color: str,
                 command: Callable = None, **kwargs):
        super().__init__(
            master,
            fg_color=BG_CARD,
            corner_radius=RADIUS_LG,
            border_width=1,
            border_color=BORDER,
            cursor="hand2",
            **kwargs,
        )
        self._color = color
        self._command = command

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        # Icon
        icon_frame = ctk.CTkFrame(
            inner, fg_color=BG_CHIP,
            corner_radius=RADIUS_SM,
            width=44, height=44,
        )
        icon_frame.pack()
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(
            icon_frame, text=icon,
            font=font(FONT_XL), text_color=color,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text=text,
            font=bold(FONT_SM), text_color=TEXT_PRIMARY,
            wraplength=90, justify="center",
        ).pack(pady=(PAD_SM, 0))

        # Hover effect
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        inner.bind("<Button-1>", self._on_click)

    def _on_enter(self, e=None):
        self.configure(fg_color=BG_HOVER, border_color=self._color)

    def _on_leave(self, e=None):
        self.configure(fg_color=BG_CARD, border_color=BORDER)

    def _on_click(self, e=None):
        if self._command:
            self._command()
