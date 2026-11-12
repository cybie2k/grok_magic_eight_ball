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
5. The window opens larger than the original layout. One scale factor
   multiplies the ball, the type, and the padding so the contents fill
   that window. Dragging the window border applies the same scale again.
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

# How much larger than the natural layout the window opens. The natural
# size is measured at startup (sans-serif faces are wider than the Times
# layout this file started from, which was about 536×690). Every font, gap,
# and the ball are multiplied by the same scale so the contents fill it.
DEFAULT_SCALE = 1.6
MIN_SCALE = 1.0
MAX_SCALE = 4.0

# Shake offsets in design pixels, the units of the original 280px ball.
# _draw_ball multiplies them by the current scale.
SHAKE_OFFSETS = (
    (-10, 6),
    (12, -5),
    (-9, 8),
    (10, -6),
    (-4, 3),
    (3, -2),
    (0, 0),
)

# Sans-serif families, in the order we prefer them. The first one that is
# actually installed is used for every label, the button, and the ball.
SANS_FAMILIES = (
    "DejaVu Sans",
    "Liberation Sans",
    "Nimbus Sans",
    "Noto Sans",
    "Arial",
    "Helvetica",
)


def sans_family(root: tk.Misc) -> str:
    """Return an installed sans-serif family.

    Tk has no generic "sans-serif" name that works on every operating
    system, so we look for known sans faces and use the first match.
    """
    installed = set(tkfont.families(root))
    for name in SANS_FAMILIES:
        if name in installed:
            return name
    return "Helvetica"


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
        # The user can resize. _on_root_configure scales the contents to fit.
        # minsize is set once the scale-1 layout has been measured.
        self.root.resizable(True, True)

        # Application state -------------------------------------------------
        # ``str | None`` means "a string, or None". Before the first shake
        # there is no fortune yet, so we start at None.
        self._answer: str | None = None
        self._shaking = False   # True while the shake animation is running
        self._shake_step = 0    # which frame of the shake we are on
        self._scale = 1.0       # 1.0 is the original 536×690 layout
        self._fitting = False   # True while we are applying a scale
        self._fit_size: tuple[int, int] | None = None

        # Fonts -------------------------------------------------------------
        # One sans-serif family for the whole window. Font objects are
        # created once and resized in _apply_scale; widgets that share a
        # Font pick up the new size automatically.
        sans = sans_family(root)
        self._title_font = tkfont.Font(family=sans, size=28, weight="bold")
        self._label_font = tkfont.Font(family=sans, size=10)
        self._body_font = tkfont.Font(family=sans, size=12)
        self._answer_font = tkfont.Font(family=sans, size=18)
        self._eight_font = tkfont.Font(family=sans, size=42, weight="bold")
        self._window_font = tkfont.Font(family=sans, size=8, weight="bold")
        self._button_font = tkfont.Font(family=sans, size=13, weight="bold")
        self._eyebrow_font = tkfont.Font(family=sans, size=9)

        # Outer padding frame ----------------------------------------------
        # A Frame is an invisible (or colored) box that holds other widgets.
        # padx/pady add empty space *inside* the frame, like CSS padding.
        # The outer frame tracks the window. The inner frame keeps its
        # natural size and is centered in whatever space is left, so a
        # resize that is wider than it is tall stays balanced.
        outer = tk.Frame(root, bg=BG)
        outer.pack(expand=True, fill="both")
        self._shell = tk.Frame(outer, bg=BG, padx=36, pady=28)
        self._shell.pack(expand=True)

        # Title block -------------------------------------------------------
        # Label is a widget that shows a single string of text.
        # A few labels are stored on self so _apply_scale can adjust their
        # padding when the window size changes. Their text stays put.
        tk.Label(
            self._shell,
            text="THE ORACLE",
            bg=BG,
            fg=MUTED,
            font=self._eyebrow_font,
        ).pack()

        self._title = tk.Label(
            self._shell,
            text="Eight Ball",
            bg=BG,
            fg=FG,
            font=self._title_font,
        )
        self._title.pack(pady=(4, 2))  # (top, bottom) padding in pixels

        self._subtitle = tk.Label(
            self._shell,
            text="Hold a yes-or-no question in mind, then shake.",
            bg=BG,
            fg=MUTED,
            font=self._body_font,
            wraplength=360,       # wrap onto the next line after 360 px
            justify="center",
        )
        self._subtitle.pack(pady=(0, 16))

        # The eight-ball drawing -------------------------------------------
        # Canvas is a drawing surface. We paint ovals, a triangle, and text
        # onto it in _draw_ball(). Coordinates are in pixels, origin (0, 0)
        # at the top-left corner of the canvas.
        self.canvas = tk.Canvas(
            self._shell,
            width=280,
            height=280,
            bg=BG,
            highlightthickness=0,  # hide the focus ring Tk draws by default
            bd=0,                  # no border
        )
        self.canvas.pack(pady=8)
        self._draw_ball()  # first paint: the "8" face, no fortune yet

        # Response text box -------------------------------------------------
        self._response_label = tk.Label(
            self._shell,
            text="Response",
            bg=BG,
            fg=MUTED,
            font=self._label_font,
            anchor="w",            # west = left-align the label text
        )
        self._response_label.pack(fill="x", pady=(18, 6))  # fill="x" stretches it

        # A thin Frame around the Text widget gives us a 1-pixel border.
        # (Text itself has no easy "border color" option.)
        text_wrap = tk.Frame(
            self._shell,
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
            self._shell,
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

        # Open larger than the original layout, then keep the contents
        # fitted if the user drags a border. The binding is added after the
        # widgets exist so the first Configure cannot fire too early.
        self._layout_for_screen()
        self.root.bind("<Configure>", self._on_root_configure)

    def _layout_for_screen(self) -> None:
        """Open a larger window and scale the current layout to fill it.

        The scale-1 size is measured from the widgets, not assumed. Sans-serif
        faces are wider than the Times layout this file started with, so a
        hardcoded 536×690 would leave a gap or clip the title. ``DEFAULT_SCALE``
        is the size we want; a short display clamps it so the title bar stays
        on screen. The window is then set to the scaled widgets' requested
        size, which is what "fill the window" means at startup.
        """
        self.root.update_idletasks()
        self._base_w = max(self.root.winfo_reqwidth(), 1)
        self._base_h = max(self.root.winfo_reqheight(), 1)
        self.root.minsize(self._base_w, self._base_h)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        max_w = int(screen_w * 0.92)
        max_h = int(screen_h * 0.88)
        scale = min(DEFAULT_SCALE, max_w / self._base_w, max_h / self._base_h)
        scale = max(MIN_SCALE, scale)
        self._apply_scale(scale)
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        if width > max_w or height > max_h:
            scale *= min(max_w / width, max_h / height)
            self._apply_scale(max(MIN_SCALE, scale * 0.99))
            self.root.update_idletasks()
            width = self.root.winfo_reqwidth()
            height = self.root.winfo_reqheight()
        self.root.geometry(f"{width}x{height}")
        self._fit_size = (width, height)

    def _on_root_configure(self, event: tk.Event) -> None:
        """Refit when the window itself changes size.

        Configure fires for child widgets too. ``event.widget is self.root``
        keeps those out. ``_fitting`` ignores the events caused by our own
        geometry change, and the 4-pixel slack ignores a one-pixel window-
        manager adjustment so we do not rescale forever.
        """
        if self._fitting or event.widget is not self.root:
            return
        if event.width < 100 or event.height < 100:
            return
        if self._fit_size is not None:
            if (
                abs(event.width - self._fit_size[0]) < 4
                and abs(event.height - self._fit_size[1]) < 4
            ):
                return
        self._fit_to(int(event.width), int(event.height))

    def _fit_to(self, width: int, height: int) -> None:
        """Scale every measurement so the layout fits inside ``width`` × ``height``.

        The scale is the smaller of the two axes, compared with the measured
        scale-1 window. A very wide window letterboxes instead of stretching
        the ball into an oval. If rounding makes the widgets ask for a few
        pixels more than the window, the scale is nudged down once.
        """
        scale = min(width / self._base_w, height / self._base_h)
        scale = max(MIN_SCALE, min(scale, MAX_SCALE))
        self._fitting = True
        try:
            self._apply_scale(scale)
            self.root.update_idletasks()
            req_w = self.root.winfo_reqwidth()
            req_h = self.root.winfo_reqheight()
            if req_w > width or req_h > height:
                shrink = min(width / req_w, height / req_h)
                self._apply_scale(max(MIN_SCALE, scale * shrink * 0.99))
            self._fit_size = (width, height)
        finally:
            self._fitting = False

    def _apply_scale(self, scale: float) -> None:
        """Resize fonts, padding, and the canvas to ``scale``.

        Sizes below are the original design pixels. ``px`` rounds them to
        a whole number of screen pixels. Shared Font objects update every
        widget that uses them, including text drawn on the canvas the next
        time ``_draw_ball`` runs.
        """
        self._scale = scale

        def px(design_px: float) -> int:
            return max(1, int(round(design_px * scale)))

        self._title_font.configure(size=px(28))
        self._label_font.configure(size=px(10))
        self._body_font.configure(size=px(12))
        self._answer_font.configure(size=px(18))
        self._eight_font.configure(size=px(42))
        self._window_font.configure(size=max(6, px(8)))
        self._button_font.configure(size=px(13))
        self._eyebrow_font.configure(size=px(9))

        self._shell.configure(padx=px(36), pady=px(28))
        self._title.pack_configure(pady=(px(4), px(2)))
        self._subtitle.configure(wraplength=px(360))
        self._subtitle.pack_configure(pady=(0, px(16)))
        side = px(280)
        self.canvas.configure(width=side, height=side)
        self.canvas.pack_configure(pady=px(8))
        self._response_label.pack_configure(pady=(px(18), px(6)))
        self.response.configure(padx=px(14), pady=px(12))
        self.shake_btn.configure(padx=px(16), pady=px(12))
        self.shake_btn.pack_configure(pady=(px(18), 0), ipady=px(4))
        self._draw_ball(self._shown_offset())

    def _shown_offset(self) -> tuple[int, int]:
        """Offset of the frame currently on screen, in design pixels."""
        if self._shaking and 0 < self._shake_step <= len(SHAKE_OFFSETS):
            return SHAKE_OFFSETS[self._shake_step - 1]
        return (0, 0)

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

        # ``s`` turns design pixels (the original 280px ball) into screen
        # pixels. The shake offsets are in those same design pixels.
        s = self._scale
        ox = offset[0] * s
        oy = offset[1] * s

        def d(design_px: float) -> float:
            return design_px * s

        # Center of the canvas. Adding ox/oy slides the whole drawing.
        cw = int(self.canvas["width"])
        ch = int(self.canvas["height"])
        cx, cy = cw / 2 + ox, ch / 2 + oy
        r = d(118)  # radius of the outer sphere
        stroke = max(1, int(round(d(2))))

        # Soft drop shadow: a slightly larger, darker oval shifted down-right.
        self.canvas.create_oval(
            cx - r + d(6),
            cy - r + d(12),
            cx + r + d(6),
            cy + r + d(12),
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
            width=stroke,
        )
        # Specular highlight (the "shine" on the upper-left).
        self.canvas.create_oval(
            cx - d(70),
            cy - d(96),
            cx - d(8),
            cy - d(42),
            fill="#3a3a44",
            outline="",
        )

        # The circular "window" cut into the front of a real eight-ball.
        well_r = d(54)
        self.canvas.create_oval(
            cx - well_r - d(4),
            cy - well_r - d(4),
            cx + well_r + d(4),
            cy + well_r + d(4),
            fill="#0c0c10",
            outline="#3a3a42",
            width=stroke,
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
                cx - well_r + d(4),
                cy - well_r + d(4),
                cx + well_r - d(4),
                cy + well_r - d(4),
                fill=WINDOW_BLUE,
                outline="",
            )
            # create_polygon takes a flat list of coordinates:
            #     x1, y1, x2, y2, x3, y3
            # Three points make a triangle, point-down like a real 8-ball die.
            self.canvas.create_polygon(
                cx,
                cy + d(38),
                cx - d(38),
                cy - d(28),
                cx + d(38),
                cy - d(28),
                fill="#06102a",
                outline="",
            )
            # ``.upper()`` is a string method: "Yes" becomes "YES".
            # ``width`` tells Tk to wrap the text inside that column.
            self.canvas.create_text(
                cx,
                cy - d(2),
                text=self._answer.upper(),
                fill=WINDOW_INK,
                font=self._window_font,
                width=d(70),
                justify="center",
            )
        else:
            # Idle face: white circle with a big "8".
            inner = d(36)
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
                cy + d(2),
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

        ``SHAKE_OFFSETS`` is a tuple of (x, y) offsets, one per frame. The
        last offset is (0, 0) so the ball settles back in the center.
        Those numbers are design pixels; ``_draw_ball`` scales them.
        """
        if self._shake_step < len(SHAKE_OFFSETS):
            # Draw this frame, then bump the counter for next time.
            self._draw_ball(SHAKE_OFFSETS[self._shake_step])
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
        # Before the window is on screen, winfo_width() can still be 1.
        # The fitted size is the requested size in that case. Including
        # width and height in geometry() keeps the larger size while we
        # move the window to the center.
        width = root.winfo_width()
        height = root.winfo_height()
        if width <= 1 or height <= 1:
            width = root.winfo_reqwidth()
            height = root.winfo_reqheight()
        # Integer division // so we get a whole number of pixels.
        # max(..., 0) keeps the window on-screen if it is larger than
        # the display (otherwise x or y could go negative).
        x = max((root.winfo_screenwidth() - width) // 2, 0)
        y = max((root.winfo_screenheight() - height) // 2, 0)
        root.geometry(f"{width}x{height}+{x}+{y}")

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
