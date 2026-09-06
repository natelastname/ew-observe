"""Small Rich-based interactive pager for EW decision traces.

This module intentionally contains no EW mathematics. It owns only ephemeral
human-presentation state and delegates all mathematical reconstruction to
``EWObserver`` and the existing renderers.
"""

from __future__ import annotations

import os
import re
import select
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass

from rich.console import Console, Group
from rich.live import Live
from rich.text import Text

from .exhaustive_human_presentation import render_exhaustive_human_trace
from .observer import EWObserver
from .presentation import OutputFormat
from .queue_frontier_presentation import render_queue_frontier_trace
from .queue_head_human_presentation import render_queue_head_human_trace
from .queue_heads import QueueHeadTrace

TermLoader = Callable[[int], tuple[int, ...]]
TraceLoader = Callable[[int], QueueHeadTrace]

SORT_KEYS = {
    "v": "value",
    "x": "prime-lex",
    "d": "depth",
    "r": "retained",
}

_TABLE_ROLE = re.compile(r"^(\s*)([BAWLTH])(\s+)")
_SIGNED_EXPONENT = re.compile(r"(?<!\S)([+-])(\d+)(?=\s|$)")
_ROLE_STYLES = {
    "B": "dim cyan",
    "A": "bold cyan",
    "W": "bold yellow",
    "L": "magenta",
    "T": "magenta",
    "H": "bright_magenta",
}

HELP_TEXT = """EW interactive viewer

Navigation
  h / left      scroll left
  l / right     scroll right
  j / down      scroll down
  k / up        scroll up
  H / L         scroll left/right by a larger jump
  J / K         scroll down/up by a larger jump
  g / G         top / bottom
  0 / $         far left / far right
  p or [        previous EW step
  n or ]        next EW step

Presentation
  c             collapse / expand exact queues
  f             frontier / current-head queue representation
  v             sort by numerical value
  x             prime-lex: highest differing prime exponent wins (2 is LSB)
  d             sort by queue depth
  r             sort by retained continuity prime
  i             toggle diagnostics/details

Color
  green exponent    introduced prime (replaces +e)
  red exponent      dropped/negative prime marker (replaces -e)
  plain exponent    retained/shared prime

Other
  ?             toggle this help
  q             quit

Tables are automatically split to fit the current terminal width. Every
mini-table repeats B, A, and W. Horizontal scrolling remains available for an
individual table that is intrinsically wider than the terminal.

The viewer only changes human presentation. It never mutates or weakens the
canonical decision/queue trace used for machine-readable output.
"""


@dataclass(slots=True)
class ViewerState:
    """Ephemeral presentation state for the custom pager."""

    n: int
    collapsed: bool = True
    queue_representation: str = "frontier"
    sort_order: str = "value"
    diagnostics: bool = False
    show_help: bool = False
    x: int = 0
    y: int = 0

    def reset_scroll(self) -> None:
        self.x = 0
        self.y = 0

    @property
    def mode_label(self) -> str:
        if not self.collapsed:
            return "expanded"
        return self.queue_representation


class ViewerSession:
    """Pure-ish controller used by the interactive loop and unit tests."""

    def __init__(self, initial_n: int, trace_loader: TraceLoader) -> None:
        if initial_n < 3:
            raise ValueError("EW decision viewer requires n >= 3")
        self.state = ViewerState(n=initial_n)
        self._trace_loader = trace_loader
        self._cache: dict[int, QueueHeadTrace] = {}
        self._document_cache: dict[tuple[int, bool, str, str, bool, int], str] = {}
        self._error: str | None = None
        self._cache[initial_n] = trace_loader(initial_n)

    @property
    def trace(self) -> QueueHeadTrace:
        return self._cache[self.state.n]

    @property
    def error(self) -> str | None:
        return self._error

    def status_line(self) -> str:
        state = self.state
        parts = [
            f"step {state.n}",
            f"view:{state.mode_label}",
            f"sort:{state.sort_order}",
            f"details:{'on' if state.diagnostics else 'off'}",
        ]
        if state.show_help:
            parts.append("HELP")
        if self._error:
            parts.append(f"error:{self._error}")
        return "  |  ".join(parts)

    def _document_key(self, render_width: int) -> tuple[int, bool, str, str, bool, int]:
        state = self.state
        return (
            state.n,
            state.collapsed,
            state.queue_representation,
            state.sort_order,
            state.diagnostics,
            render_width,
        )

    def document(self, *, render_width: int = 160) -> str:
        """Render the complete un-cropped human document for current state.

        ``render_width`` is a soft table-width target. The existing human
        renderers use it to split the body into multiple self-contained tables,
        each repeating B, A, and W.
        """

        if self.state.show_help:
            return HELP_TEXT

        render_width = max(1, render_width)
        key = self._document_key(render_width)
        cached = self._document_cache.get(key)
        if cached is not None:
            return cached

        trace = self.trace
        if not self.state.collapsed:
            rendered = render_exhaustive_human_trace(
                trace.decision,
                output_format=OutputFormat.TEXT,
                diagnostics=self.state.diagnostics,
                max_width=render_width,
                candidates_per_table=0,
                sort_order=self.state.sort_order,
            )
        elif self.state.queue_representation == "head":
            rendered = render_queue_head_human_trace(
                trace,
                output_format=OutputFormat.TEXT,
                diagnostics=self.state.diagnostics,
                max_width=render_width,
                candidates_per_table=0,
                sort_order=self.state.sort_order,
            )
        else:
            rendered = render_queue_frontier_trace(
                trace,
                output_format=OutputFormat.TEXT,
                diagnostics=self.state.diagnostics,
                max_width=render_width,
                candidates_per_table=0,
                sort_order=self.state.sort_order,
            )
        self._document_cache[key] = rendered
        return rendered

    def _change_step(self, n: int) -> None:
        if n < 3:
            return
        try:
            if n not in self._cache:
                self._cache[n] = self._trace_loader(n)
        except Exception as exc:  # surfaced in the status bar without killing the pager
            self._error = f"{type(exc).__name__}: {exc}"
            return
        self._error = None
        self.state.n = n
        self.state.show_help = False
        self.state.reset_scroll()

    def handle_key(self, key: str) -> bool:
        """Apply one normalized key. Return False when the viewer should quit."""

        state = self.state
        if key == "q":
            return False
        if key in {"p", "["}:
            self._change_step(state.n - 1)
            return True
        if key in {"n", "]"}:
            self._change_step(state.n + 1)
            return True
        if key == "c":
            state.collapsed = not state.collapsed
            state.show_help = False
            state.reset_scroll()
            return True
        if key == "f":
            state.queue_representation = (
                "head" if state.queue_representation == "frontier" else "frontier"
            )
            state.show_help = False
            state.reset_scroll()
            return True
        if key in SORT_KEYS:
            state.sort_order = SORT_KEYS[key]
            state.show_help = False
            state.reset_scroll()
            return True
        if key == "i":
            state.diagnostics = not state.diagnostics
            state.show_help = False
            state.reset_scroll()
            return True
        if key == "?":
            state.show_help = not state.show_help
            state.reset_scroll()
            return True

        if key == "h":
            state.x = max(0, state.x - 8)
        elif key == "l":
            state.x += 8
        elif key == "H":
            state.x = max(0, state.x - 40)
        elif key == "L":
            state.x += 40
        elif key == "j":
            state.y += 1
        elif key == "k":
            state.y = max(0, state.y - 1)
        elif key == "J":
            state.y += 10
        elif key == "K":
            state.y = max(0, state.y - 10)
        elif key == "g":
            state.y = 0
        elif key == "G":
            state.y = 10**12
        elif key == "0":
            state.x = 0
        elif key == "$":
            state.x = 10**12
        return True


def viewport_lines(
    document: str,
    state: ViewerState,
    *,
    width: int,
    height: int,
) -> tuple[str, ...]:
    """Crop a document to the current pager viewport and clamp scroll offsets."""

    width = max(1, width)
    height = max(1, height)
    lines = document.splitlines() or [""]
    max_width = max((len(line) for line in lines), default=0)
    state.x = min(max(0, state.x), max(0, max_width - width))
    state.y = min(max(0, state.y), max(0, len(lines) - height))

    visible = lines[state.y : state.y + height]
    cropped = tuple(line[state.x : state.x + width] for line in visible)
    if len(cropped) < height:
        cropped += ("",) * (height - len(cropped))
    return cropped


def colorize_viewer_line(line: str) -> Text:
    """Apply viewer-only semantic color while preserving exact display width.

    In incidence rows, ``+e`` is rendered as a green ``e`` and ``-e`` as a red
    ``e``. The sign itself becomes one blank character so column alignment is
    unchanged. Bare exponents remain uncolored and therefore mean retained or
    shared primes exactly as in the static text notation.
    """

    text = Text(line, no_wrap=True, overflow="crop")

    role_match = _TABLE_ROLE.match(line)
    if role_match is not None:
        role_start = len(role_match.group(1))
        role = role_match.group(2)
        text.stylize(_ROLE_STYLES[role], role_start, role_start + 1)

        # Work from right to left so replacing sign characters cannot invalidate
        # the offsets of earlier matches. Replacement is always one character,
        # preserving exact visible width.
        matches = list(_SIGNED_EXPONENT.finditer(line))
        for match in reversed(matches):
            sign_start = match.start(1)
            exponent_start = match.start(2)
            exponent_end = match.end(2)
            text.plain = text.plain[:sign_start] + " " + text.plain[sign_start + 1 :]
            style = "bold green" if match.group(1) == "+" else "bold red"
            text.stylize(style, exponent_start, exponent_end)
        return text

    stripped = line.strip()
    if stripped.startswith("role "):
        text.stylize("bold", 0, len(line))
    elif stripped and set(stripped) <= {"-", " "}:
        text.stylize("dim", 0, len(line))
    elif line.startswith("EW step "):
        text.stylize("bold", 0, len(line))
    elif "mode:" in line or "human sort=" in line:
        text.stylize("dim", 0, len(line))
    return text


def _frame(session: ViewerSession, *, width: int, height: int) -> Group:
    """Build the Rich renderable for one terminal frame."""

    width = max(1, width)
    height = max(3, height)
    body_height = max(1, height - 2)
    body = viewport_lines(
        session.document(render_width=width),
        session.state,
        width=width,
        height=body_height,
    )
    status = Text(session.status_line()[:width], style="bold reverse", no_wrap=True)
    body_renderables = [colorize_viewer_line(line) for line in body]
    keys = Text(
        "q quit | hjkl scroll | n/p step | c collapse | f frontier/head | "
        "v/x/d/r sort | i details | ? help"[:width],
        style="dim",
        no_wrap=True,
    )
    return Group(status, *body_renderables, keys)


def _read_key(fd: int) -> str:
    """Read one key in cbreak mode, normalizing common terminal escape sequences."""

    first = os.read(fd, 1)
    if first != b"\x1b":
        return first.decode("utf-8", errors="ignore")

    sequence = bytearray(first)
    while len(sequence) < 8:
        ready, _, _ = select.select([fd], [], [], 0.005)
        if not ready:
            break
        sequence.extend(os.read(fd, 1))

    mapping = {
        b"\x1b[A": "k",
        b"\x1b[B": "j",
        b"\x1b[C": "l",
        b"\x1b[D": "h",
        b"\x1b[5~": "K",
        b"\x1b[6~": "J",
        b"\x1b[H": "g",
        b"\x1b[F": "G",
        b"\x1bOH": "g",
        b"\x1bOF": "G",
    }
    return mapping.get(bytes(sequence), "")


def _trace_loader(term_loader: TermLoader) -> TraceLoader:
    def load(n: int) -> QueueHeadTrace:
        observer = EWObserver(term_loader(n))
        return observer.trace_queue_heads(n)

    return load


def run_viewer(initial_n: int, term_loader: TermLoader) -> None:
    """Run the interactive EW pager in the current terminal."""

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError("ew-observe view requires an interactive terminal")

    try:
        import termios
        import tty
    except ImportError as exc:
        raise ValueError("ew-observe view currently requires a POSIX terminal") from exc

    session = ViewerSession(initial_n, _trace_loader(term_loader))
    console = Console()
    fd = sys.stdin.fileno()
    previous_attributes = termios.tcgetattr(fd)
    previous_size: tuple[int, int] | None = None

    try:
        tty.setcbreak(fd)
        size = shutil.get_terminal_size(fallback=(120, 40))
        previous_size = (size.columns, size.lines)
        with Live(
            _frame(session, width=size.columns, height=size.lines),
            console=console,
            screen=True,
            auto_refresh=False,
            transient=False,
        ) as live:
            live.refresh()
            while True:
                size = shutil.get_terminal_size(fallback=(120, 40))
                current_size = (size.columns, size.lines)
                if current_size != previous_size:
                    previous_size = current_size
                    live.update(
                        _frame(session, width=size.columns, height=size.lines),
                        refresh=True,
                    )

                ready, _, _ = select.select([fd], [], [], 0.15)
                if not ready:
                    continue
                key = _read_key(fd)
                if not key:
                    continue
                if not session.handle_key(key):
                    break
                size = shutil.get_terminal_size(fallback=(120, 40))
                live.update(
                    _frame(session, width=size.columns, height=size.lines),
                    refresh=True,
                )
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous_attributes)
