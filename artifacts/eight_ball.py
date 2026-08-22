#!/usr/bin/env python3
"""Magic Eight Ball — a desktop GUI built with Tkinter.

HOW TO RUN
----------
This file uses only Python's standard library. You do not need pip.

    python3 eight_ball.py

WHAT YOU WILL LEARN IN THIS FILE
--------------------------------
- Importing modules from the standard library
- Constants (names in ALL_CAPS by convention)
- Classes and methods (how we group GUI state and behavior)
- Type hints (the ``str | None`` and ``-> None`` notes)
- Tkinter widgets: Tk, Frame, Label, Canvas, Text, Button
- Geometry managers: pack()
- Event handling: button command= and bind()
- Drawing shapes on a Canvas
- Simple animation with root.after() (a timer, not a thread)
- The Tk event loop: mainloop()

PROGRAM FLOW
------------
1. Python starts at the bottom: ``if __name__ == "__main__"``.
2. ``main()`` creates the window (``tk.Tk``) and builds ``EightBallApp``.
3. ``root.mainloop()`` sits and waits for mouse/keyboard events.
4. Clicking "Shake Ball" calls ``shake()``, which plays a short animation
   and then writes a random fortune into the text box.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
# ``from __future__ import annotations`` is a Python 3.7+ feature that makes
# all type hints strings under the hood. That lets us write modern hints like
# ``str | None`` even on slightly older Pythons (3.9/3.10).
from __future__ import annotations

# ``os`` lets us read environment variables with os.environ.get(...).
import os

# ``random`` is the standard-library RNG. We use random.choice() to pick
# one fortune from the list of answers.
import random

# Tkinter is Python's built-in GUI toolkit. The common convention is:
#     import tkinter as tk
# so widget classes are written tk.Label, tk.Button, etc.
import tkinter as tk

# Fonts live in a sub-module. Importing it as ``tkfont`` keeps the name short.
from tkinter import font as tkfont


# ---------------------------------------------------------------------------
# Data: the classic 20 Magic 8-Ball answers
# ---------------------------------------------------------------------------
# A tuple (round parentheses) is an *immutable* sequence: you cannot append
# or assign into it later. We use a tuple because this list never changes
# while the program runs. A list [ ... ] would also work.
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

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
# These are hex color strings: "#RRGGBB". Tkinter accepts this format
# anywhere you pass bg= (background) or fg= (foreground / text color).
# Putting them in named constants means we change a color in one place.
BG = "#0a0a0b"          # window background (near-black)
FG = "#f4f4f5"          # main text (off-white)
MUTED = "#a1a1aa"       # secondary text (gray)
CARD = "#121214"        # text-box background (a step lighter than BG)
BUTTON_BG = "#e8e8ec"   # Shake Ball fill
BUTTON_FG = "#0a0a0b"   # Shake Ball label
BALL = "#141418"        # eight-ball body
WELL = "#07080c"        # dark circle in the center of the ball
WINDOW_BLUE = "#0e2248" # fortune window (the "liquid" inside the ball)
WINDOW_INK = "#f4f6fa"  # fortune text drawn on the triangle
PLACEHOLDER = "Your fortune appears here."


class EightBallApp:
    """The whole user interface, stored as one object.

    Why a class?
        A GUI has *state* that many functions need to share: the current
        fortune, whether we are mid-animation, the Canvas we draw on, the
        Text widget we write into. Putting those on ``self`` (the instance)
        is cleaner than a pile of global variables.

    Leading underscores (``self._answer``) are a Python *convention* that
    means "this is internal; other code should not touch it." It is not
    enforced by the language.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Build every widget and store them on ``self``.

        ``__init__`` is the constructor. Python calls it automatically
        when you write ``EightBallApp(root)``.

        Parameters
        ----------
        root:
            The main window, created with ``tk.Tk()``. Every widget we
            create is a child of this window (or of a Frame inside it).

        The ``-> None`` is a type hint: this method does not return a
        useful value. ``root: tk.Tk`` says "root should be a Tk window."
        Type hints are optional — they help you (and editors) read the
        code, but Python does not require them at runtime.
        """
        # Keep a reference to the window so later methods can call
        # root.after(...) and root.bind(...).
        self.root = root
        self.root.title("Eight Ball")          # text in the title bar
        self.root.configure(bg=BG)             # window background color
        self.root.resizable(False, False)      # (width, height) — lock size

        # Application state -------------------------------------------------
        # ``str | None`` means "a string, or None". Before the first shake
        # there is no fortune yet, so we start at None.
        self._answer: str | None = None
        self._shaking = False   # True while the shake animation is running
        self._shake_step = 0    # which frame of the shake we are on

        # Fonts -------------------------------------------------------------
        # tkfont.Font objects can be reused on many widgets. Creating them
        # once (instead of passing family= every time) keeps sizes consistent.
        self._title_font = tkfont.Font(family="Times", size=28, weight="bold")
        self._label_font = tkfont.Font(family="Helvetica", size=10)
        self._body_font = tkfont.Font(family="Helvetica", size=12)
        self._answer_font = tkfont.Font(family="Times", size=18)
        self._eight_font = tkfont.Font(family="Times", size=42, weight="bold")
        self._window_font = tkfont.Font(family="Helvetica", size=8, weight="bold")
        self._button_font = tkfont.Font(family="Helvetica", size=13, weight="bold")
        self._eyebrow_font = tkfont.Font(family="Helvetica", size=9)

        # Outer padding frame ----------------------------------------------
        # A Frame is an invisible (or colored) box that holds other widgets.
        # padx/pady add empty space *inside* the frame, like CSS padding.
        shell = tk.Frame(root, bg=BG, padx=36, pady=28)
        # pack() is Tk's simplest layout manager: widgets stack from top
        # to bottom (by default). expand=True lets the frame grow if the
        # window is stretched.
        shell.pack(expand=True)

        # Title block -------------------------------------------------------
        # Label is a widget that shows a single string of text.
        # We do not keep a variable for these labels because we never
        # change them later. (If we needed to, we would store self.title = ...)
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
        ).pack(pady=(4, 2))  # (top, bottom) padding in pixels

        tk.Label(
            shell,
            text="Hold a yes-or-no question in mind, then shake.",
            bg=BG,
            fg=MUTED,
            font=self._body_font,
            wraplength=360,       # wrap onto the next line after 360 px
            justify="center",
        ).pack(pady=(0, 16))

        # The eight-ball drawing -------------------------------------------
        # Canvas is a drawing surface. We paint ovals, a triangle, and text
        # onto it in _draw_ball(). Coordinates are in pixels, origin (0, 0)
        # at the top-left corner of the canvas.
        self.canvas = tk.Canvas(
            shell,
            width=280,
            height=280,
            bg=BG,
            highlightthickness=0,  # hide the focus ring Tk draws by default
            bd=0,                  # no border
        )
        self.canvas.pack(pady=8)
        self._draw_ball()  # first paint: the "8" face, no fortune yet

        # Response text box -------------------------------------------------
        tk.Label(
            shell,
            text="Response",
            bg=BG,
            fg=MUTED,
            font=self._label_font,
            anchor="w",            # west = left-align the label text
        ).pack(fill="x", pady=(18, 6))  # fill="x" stretches it horizontally

        # A thin Frame around the Text widget gives us a 1-pixel border.
        # (Text itself has no easy "border color" option.)
        text_wrap = tk.Frame(
            shell,
            bg=CARD,
            highlightbackground="#2a2a30",
            highlightthickness=1,
        )
        text_wrap.pack(fill="x")

        # Text is a multi-line text box. We use it as a *read-only display*
        # of the fortune. (An Entry widget is single-line; Text can wrap.)
        self.response = tk.Text(
            text_wrap,
            height=3,              # roughly 3 lines tall
            width=36,              # roughly 36 characters wide
            wrap="word",           # wrap at word boundaries, not mid-word
            font=self._answer_font,
            bg=CARD,
            fg=MUTED,              # placeholder starts in the muted color
            insertbackground=FG,   # caret color (rarely seen; box is read-only)
            relief="flat",
            padx=14,
            pady=12,
            highlightthickness=0,
        )
        self.response.pack(fill="both")

        # Text positions use a special index syntax: "line.column"
        # "1.0" means line 1, character 0 (the very start).
        # "end" means just after the last character.
        self.response.insert("1.0", PLACEHOLDER)
        # A *tag* is a named style you can apply to a range of characters.
        self.response.tag_configure("center", justify="center")
        self.response.tag_add("center", "1.0", "end")
        # Disabled = the user cannot type into it. We temporarily re-enable
        # it in _set_response() whenever we need to change the contents.
        self.response.configure(state="disabled")

        # The one button the assignment asked for ---------------------------
        # command=self.shake means: when clicked, call the shake method.
        # Notice there are no parentheses: we pass the *function itself*,
        # we do not call it yet. Tkinter will call it later, on click.
        self.shake_btn = tk.Button(
            shell,
            text="Shake Ball",
            command=self.shake,
            font=self._button_font,
            bg=BUTTON_BG,
            fg=BUTTON_FG,
            activebackground="#ffffff",  # color while the mouse is held down
            activeforeground=BUTTON_FG,
            relief="flat",
            padx=16,
            pady=12,
            cursor="hand2",          # pointer finger on hover
            highlightthickness=0,
            bd=0,
        )
        # ipady adds *internal* padding, making the button taller.
        self.shake_btn.pack(fill="x", pady=(18, 0), ipady=4)

        # Keyboard shortcuts ------------------------------------------------
        # bind() connects a key to a function. Tkinter always passes an
        # Event object as the first argument, which we do not need, so the
        # lambda ignores it (the leading underscore marks "unused").
        self.root.bind("<Return>", lambda _event: self.shake())  # Enter key
        self.root.bind("<space>", lambda _event: self.shake())   # Space bar

    def _draw_ball(self, offset: tuple[int, int] = (0, 0)) -> None:
        """Paint the eight-ball onto the canvas.

        Parameters
        ----------
        offset:
            ``(x, y)`` pixel shift from the resting position. During the
            shake animation we pass small values like ``(-10, 6)`` so the
            ball appears to jiggle.

        How Canvas drawing works
        ------------------------
        Every ``create_oval`` / ``create_polygon`` / ``create_text`` call
        adds a *shape item*. Items stay until you delete them. We wipe the
        canvas with ``delete("all")`` and redraw from scratch each frame.
        That is simple (and plenty fast for one ball).

        An oval is defined by the bounding box of a rectangle:
            create_oval(x0, y0, x1, y1)
        where (x0, y0) is the top-left of that box and (x1, y1) the
        bottom-right. A circle is just an oval whose box is a square.
        """
        self.canvas.delete("all")

        # Unpack the offset tuple into two names. This is equivalent to:
        #     ox = offset[0]
        #     oy = offset[1]
        ox, oy = offset

        # Center of the ball. The canvas is 280x280, so 140, 140 is the
        # middle. Adding ox/oy slides the whole drawing during a shake.
        cx, cy = 140 + ox, 140 + oy
        r = 118  # radius of the outer sphere, in pixels

        # Soft drop shadow: a slightly larger, darker oval shifted down-right.
        self.canvas.create_oval(
            cx - r + 6,
            cy - r + 12,
            cx + r + 6,
            cy + r + 12,
            fill="#050506",
            outline="",            # empty string = no outline
        )
        # Main sphere.
        self.canvas.create_oval(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            fill=BALL,
            outline="#2a2a32",
            width=2,
        )
        # Specular highlight (the "shine" on the upper-left).
        self.canvas.create_oval(
            cx - 70,
            cy - 96,
            cx - 8,
            cy - 42,
            fill="#3a3a44",
            outline="",
        )

        # The circular "window" cut into the front of a real eight-ball.
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

        # Two faces: the fortune (after a shake) or the number 8 (idle).
        if self._answer and not self._shaking:
            # Blue "liquid" behind the triangle.
            self.canvas.create_oval(
                cx - well_r + 4,
                cy - well_r + 4,
                cx + well_r - 4,
                cy + well_r - 4,
                fill=WINDOW_BLUE,
                outline="",
            )
            # create_polygon takes a flat list of coordinates:
            #     x1, y1, x2, y2, x3, y3
            # Three points make a triangle, point-down like a real 8-ball die.
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
            # ``.upper()`` is a string method: "Yes" becomes "YES".
            # ``width=70`` tells Tk to wrap the text inside a 70-px column.
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
            # Idle face: white circle with a big "8".
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
        """Put ``text`` into the read-only response box.

        A disabled Text widget ignores insert/delete, so the recipe is:
        1. enable it
        2. clear the old contents
        3. insert the new string
        4. re-center with a tag
        5. disable it again
        """
        self.response.configure(state="normal", fg=FG)
        self.response.delete("1.0", "end")
        self.response.insert("1.0", text)
        self.response.tag_configure("center", justify="center")
        self.response.tag_add("center", "1.0", "end")
        self.response.configure(state="disabled")

    def shake(self) -> None:
        """Start a shake. Bound to the button, Enter, and Space.

        If a shake is already running we ``return`` immediately. That
        prevents a second click from stacking another animation on top
        of the first one (a common GUI bug called re-entrancy).
        """
        if self._shaking:
            return
        self._shaking = True
        self.shake_btn.configure(state="disabled", text="Shaking…")
        self._shake_step = 0
        self._animate_shake()

    def _animate_shake(self) -> None:
        """Play one frame of the shake, then schedule the next.

        This is the standard Tkinter animation pattern:

            1. Draw the current frame.
            2. Call ``root.after(milliseconds, callback)`` to ask Tk to
               run this method again later.
            3. When the last frame is done, pick the fortune.

        Why not a ``for`` loop with ``time.sleep()``?
            ``sleep()`` would freeze the entire window — no redraws, no
            clicks — because Tk can only paint when it is inside mainloop.
            ``after()`` hands control back to mainloop between frames.

        ``pattern`` is a tuple of (x, y) offsets, one per frame. The last
        offset is (0, 0) so the ball settles back in the center.
        """
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
            # Draw this frame, then bump the counter for next time.
            self._draw_ball(pattern[self._shake_step])
            self._shake_step += 1
            # 80 milliseconds ≈ 12 frames per second. Fast enough to look
            # like a shake, slow enough to see.
            self.root.after(80, self._animate_shake)
            return

        # Animation finished — pick a fortune --------------------------------
        # List comprehension: build a new list of every answer except the
        # one currently showing, so we do not repeat twice in a row.
        #
        #     [expression for item in sequence if condition]
        #
        # The ``or list(ANSWERS)`` is a fallback: if the filtered list were
        # empty (it never is, unless ANSWERS had only one item), use all
        # answers. ``or`` returns the left side if it is "truthy" (non-empty),
        # otherwise the right side.
        pool = [answer for answer in ANSWERS if answer != self._answer] or list(ANSWERS)
        self._answer = random.choice(pool)  # one element, uniform odds
        self._shaking = False
        self._draw_ball()                   # now shows the triangle + fortune
        self._set_response(self._answer)
        self.shake_btn.configure(state="normal", text="Shake Ball")


def main() -> None:
    """Create the window, build the app, and start the event loop.

    ``mainloop()`` is a long-running ``while True`` inside Tkinter. It:
      - waits for mouse and keyboard events
      - calls the handlers we registered (shake, bind, after callbacks)
      - redraws the window
    It only returns when the user closes the window.
    """
    # tk.Tk() is the one root window every Tkinter program needs.
    # Creating a second Tk() in the same process is almost always a bug.
    root = tk.Tk()
    EightBallApp(root)

    # update_idletasks() forces Tk to compute widget sizes *now*, before
    # we ask for winfo_width() / winfo_height(). Without it those can
    # still be 1, because the window has not been mapped to the screen yet.
    root.update_idletasks()

    # EIGHT_BALL_FILL is an optional environment variable used when this
    # file is shown in a small virtual display. On your own computer you
    # normally will not have it set, so the else-branch runs: we center
    # the window on the screen.
    #
    # os.environ.get(name) returns the value, or None if it is unset.
    # A non-empty string is "truthy", so ``if os.environ.get(...)`` works
    # as a simple on/off flag.
    if os.environ.get("EIGHT_BALL_FILL"):
        try:
            # attributes() sets window-manager flags. "-fullscreen" may
            # raise TclError on a display that has no window manager, so
            # we catch that and fall back to a manual size.
            root.attributes("-fullscreen", True)
        except tk.TclError:
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            # geometry() accepts strings like "800x600+100+40"
            # meaning width x height + x_offset + y_offset.
            root.geometry(f"{sw}x{sh}+0+0")
    else:
        width = root.winfo_width()
        height = root.winfo_height()
        # Integer division // so we get a whole number of pixels.
        # max(..., 0) keeps the window on-screen if it is larger than
        # the display (otherwise x or y could go negative).
        x = max((root.winfo_screenwidth() - width) // 2, 0)
        y = max((root.winfo_screenheight() - height) // 2, 0)
        root.geometry(f"+{x}+{y}")

    root.mainloop()


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------
# Every Python file has a built-in name ``__name__``.
#
# - When you *run* the file (``python3 eight_ball.py``), Python sets
#   __name__ to the string "__main__" and this block runs.
# - When you *import* the file (``import eight_ball``), __name__ is
#   "eight_ball" instead, so main() is *not* called. That lets another
#   program reuse EightBallApp without popping up a window.
if __name__ == "__main__":
    main()
