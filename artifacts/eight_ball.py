#!/usr/bin/env python3
"""Magic Eight Ball — desktop GUI built with Tkinter.

Standard library only. No pip packages required.

    python3 eight_ball.py
"""

from __future__ import annotations

import os
import random
import tkinter as tk
from tkinter import font as tkfont

ANSWERS = (
    "It is certain",
    "It is decidedly so",
    "Without a doubt",
    "Yes definitely",
    "You may rely on it",
    "As I see it, yes",
    "Most likely",
    "Outlook good",
    "Yes",
    "Signs point to yes",
    "Reply hazy, try again",
    "Ask again later",
    "Better not tell you now",
    "Cannot predict now",
    "Concentrate and ask again",
    "Don't count on it",
    "My reply is no",
    "My sources say no",
    "Outlook not so good",
    "Very doubtful",
)

BG = "#0a0a0b"
FG = "#f4f4f5"
MUTED = "#a1a1aa"
CARD = "#121214"
BUTTON_BG = "#e8e8ec"
BUTTON_FG = "#0a0a0b"
BALL = "#141418"
WELL = "#07080c"
WINDOW_BLUE = "#0e2248"
WINDOW_INK = "#f4f6fa"
PLACEHOLDER = "Your fortune appears here."


class EightBallApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Eight Ball")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self._answer: str | None = None
        self._shaking = False
        self._shake_step = 0

        self._title_font = tkfont.Font(family="Times", size=28, weight="bold")
        self._label_font = tkfont.Font(family="Helvetica", size=10)
        self._body_font = tkfont.Font(family="Helvetica", size=12)
        self._answer_font = tkfont.Font(family="Times", size=18)
        self._eight_font = tkfont.Font(family="Times", size=42, weight="bold")
        self._window_font = tkfont.Font(family="Helvetica", size=8, weight="bold")
        self._button_font = tkfont.Font(family="Helvetica", size=13, weight="bold")
        self._eyebrow_font = tkfont.Font(family="Helvetica", size=9)

        shell = tk.Frame(root, bg=BG, padx=36, pady=28)
        shell.pack(expand=True)

        tk.Label(
            shell,
            text="THE ORACLE",
            bg=BG,
            fg=MUTED,
            font=self._eyebrow_font,
        ).pack()

        tk.Label(
            shell,
            text="Eight Ball",
            bg=BG,
            fg=FG,
            font=self._title_font,
        ).pack(pady=(4, 2))

        tk.Label(
            shell,
            text="Hold a yes-or-no question in mind, then shake.",
            bg=BG,
            fg=MUTED,
            font=self._body_font,
            wraplength=360,
            justify="center",
        ).pack(pady=(0, 16))

        self.canvas = tk.Canvas(
            shell,
            width=280,
            height=280,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(pady=8)
        self._draw_ball()

        tk.Label(
            shell,
            text="Response",
            bg=BG,
            fg=MUTED,
            font=self._label_font,
            anchor="w",
        ).pack(fill="x", pady=(18, 6))

        text_wrap = tk.Frame(
            shell,
            bg=CARD,
            highlightbackground="#2a2a30",
            highlightthickness=1,
        )
        text_wrap.pack(fill="x")

        self.response = tk.Text(
            text_wrap,
            height=3,
            width=36,
            wrap="word",
            font=self._answer_font,
            bg=CARD,
            fg=MUTED,
            insertbackground=FG,
            relief="flat",
            padx=14,
            pady=12,
            highlightthickness=0,
        )
        self.response.pack(fill="both")
        self.response.insert("1.0", PLACEHOLDER)
        self.response.tag_configure("center", justify="center")
        self.response.tag_add("center", "1.0", "end")
        self.response.configure(state="disabled")

        self.shake_btn = tk.Button(
            shell,
            text="Shake Ball",
            command=self.shake,
            font=self._button_font,
            bg=BUTTON_BG,
            fg=BUTTON_FG,
            activebackground="#ffffff",
            activeforeground=BUTTON_FG,
            relief="flat",
            padx=16,
            pady=12,
            cursor="hand2",
            highlightthickness=0,
            bd=0,
        )
        self.shake_btn.pack(fill="x", pady=(18, 0), ipady=4)

        self.root.bind("<Return>", lambda _event: self.shake())
        self.root.bind("<space>", lambda _event: self.shake())

    def _draw_ball(self, offset: tuple[int, int] = (0, 0)) -> None:
        self.canvas.delete("all")
        ox, oy = offset
        cx, cy = 140 + ox, 140 + oy
        r = 118

        self.canvas.create_oval(
            cx - r + 6,
            cy - r + 12,
            cx + r + 6,
            cy + r + 12,
            fill="#050506",
            outline="",
        )
        self.canvas.create_oval(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            fill=BALL,
            outline="#2a2a32",
            width=2,
        )
        self.canvas.create_oval(
            cx - 70,
            cy - 96,
            cx - 8,
            cy - 42,
            fill="#3a3a44",
            outline="",
        )

        well_r = 54
        self.canvas.create_oval(
            cx - well_r - 4,
            cy - well_r - 4,
            cx + well_r + 4,
            cy + well_r + 4,
            fill="#0c0c10",
            outline="#3a3a42",
            width=2,
        )
        self.canvas.create_oval(
            cx - well_r,
            cy - well_r,
            cx + well_r,
            cy + well_r,
            fill=WELL,
            outline="",
        )

        if self._answer and not self._shaking:
            self.canvas.create_oval(
                cx - well_r + 4,
                cy - well_r + 4,
                cx + well_r - 4,
                cy + well_r - 4,
                fill=WINDOW_BLUE,
                outline="",
            )
            self.canvas.create_polygon(
                cx,
                cy + 38,
                cx - 38,
                cy - 28,
                cx + 38,
                cy - 28,
                fill="#06102a",
                outline="",
            )
            self.canvas.create_text(
                cx,
                cy - 2,
                text=self._answer.upper(),
                fill=WINDOW_INK,
                font=self._window_font,
                width=70,
                justify="center",
            )
        else:
            inner = 36
            self.canvas.create_oval(
                cx - inner,
                cy - inner,
                cx + inner,
                cy + inner,
                fill=FG,
                outline="",
            )
            self.canvas.create_text(
                cx,
                cy + 2,
                text="8",
                fill=BUTTON_FG,
                font=self._eight_font,
            )

    def _set_response(self, text: str) -> None:
        self.response.configure(state="normal", fg=FG)
        self.response.delete("1.0", "end")
        self.response.insert("1.0", text)
        self.response.tag_configure("center", justify="center")
        self.response.tag_add("center", "1.0", "end")
        self.response.configure(state="disabled")

    def shake(self) -> None:
        if self._shaking:
            return
        self._shaking = True
        self.shake_btn.configure(state="disabled", text="Shaking…")
        self._shake_step = 0
        self._animate_shake()

    def _animate_shake(self) -> None:
        pattern = (
            (-10, 6),
            (12, -5),
            (-9, 8),
            (10, -6),
            (-4, 3),
            (3, -2),
            (0, 0),
        )
        if self._shake_step < len(pattern):
            self._draw_ball(pattern[self._shake_step])
            self._shake_step += 1
            self.root.after(80, self._animate_shake)
            return

        pool = [answer for answer in ANSWERS if answer != self._answer] or list(ANSWERS)
        self._answer = random.choice(pool)
        self._shaking = False
        self._draw_ball()
        self._set_response(self._answer)
        self.shake_btn.configure(state="normal", text="Shake Ball")


def main() -> None:
    root = tk.Tk()
    EightBallApp(root)
    root.update_idletasks()

    if os.environ.get("EIGHT_BALL_FILL"):
        try:
            root.attributes("-fullscreen", True)
        except tk.TclError:
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            root.geometry(f"{sw}x{sh}+0+0")
    else:
        width = root.winfo_width()
        height = root.winfo_height()
        x = max((root.winfo_screenwidth() - width) // 2, 0)
        y = max((root.winfo_screenheight() - height) // 2, 0)
        root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
