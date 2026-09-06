# Interactive EW viewer

The experimental viewer is a small keyboard-driven terminal pager for one EW
decision. It is deliberately closer to a custom `less` than to a general GUI.

Launch it directly at a sequence index:

```bash
uv run ew-observe view 10000
```

The viewer opens in the terminal alternate screen and restores the ordinary
terminal when it exits.

## Design boundary

The viewer contains no EW decision mathematics. It obtains the canonical
queue trace from `EWObserver` and delegates all presentation to the existing
human renderers. Its state consists only of transient display choices and
scroll offsets.

Consequently, changing a viewer option cannot change, thin, reorder, or
otherwise degrade JSON/TSV/CSV output. The machine-readable commands remain
independent of the viewer.

The canonical trace itself uses the safe **fresh-prime frontier reduction**. If
`Q_n` is the least globally unintroduced prime before `a_n`, candidates whose
prime support contains any prime greater than `Q_n` are discarded from the race.
The viewer therefore never displays such a candidate as a threat, queue
competitor, or live candidate. Every viewer representation prints the current
`Q_n` in its header. Primitive candidate admissibility remains separately
auditable through the `candidate` command; see `fresh-prime-frontier.md`.

## Layout

The viewer uses the current terminal width as the same soft table-width target
used by the ordinary human-readable `step` command. Long decisions are therefore
split into multiple self-contained incidence tables instead of being forced into
one giant row. Every mini-table repeats the fixed `B`, `A`, and `W` context.

When the terminal is resized, the viewer re-renders the document using the new
width, so the number of mini-tables adjusts automatically. Horizontal scrolling
remains available as a fallback when even one self-contained table is
intrinsically wider than the terminal.

## Semantic color

Color is deliberately viewer-only. The underlying static text renderers keep
their explicit signs, and machine-readable formats are unchanged.

Inside incidence rows:

- an introduced-prime cell that the static renderer writes as `+e` is displayed
  as a **green** `e` with the sign visually removed;
- a negative/dropped marker written as `-e`, when present, is displayed as a
  **red** `e`;
- a bare exponent remains uncolored and means retained/shared prime incidence.

The removed sign is replaced by one blank character before coloring, so table
column widths and horizontal-scroll coordinates remain unchanged. Styling is
applied to the complete logical line before viewport cropping, so the color is
preserved even when horizontal scrolling hides the original sign position.

Row roles also receive restrained colors: `W` is highlighted as the winner,
`B/A` share a continuity-context color family, and losing/threat/head rows use a
secondary accent. These colors are only reading aids; they encode no additional
mathematics.

## Keys

### Navigation

| Key | Action |
| --- | --- |
| `h`, left arrow | scroll left |
| `l`, right arrow | scroll right |
| `j`, down arrow | scroll down |
| `k`, up arrow | scroll up |
| `H`, `L` | larger horizontal jump |
| `J`, `K` | larger vertical jump |
| `g`, `G` | top / bottom |
| `0`, `$` | far left / far right |
| `p` or `[` | previous EW step |
| `n` or `]` | next EW step |

### Presentation

| Key | Action |
| --- | --- |
| `c` | collapse / expand exact queues |
| `f` | serviced frontier / current-head representation |
| `v` | sort by numerical value |
| `x` | sort by corrected prime-exponent lex order |
| `d` | sort by queue depth |
| `r` | sort by retained continuity prime |
| `i` | toggle diagnostics/details |

The `x` ordering treats `(v_2,v_3,v_5,...)` as prime digits with `v_2` least
significant: the largest prime where two exponent vectors differ decides the
comparison. For example `12=2^2*3` sorts before `18=2*3^2`, and both sort before
`20=2^2*5`.

### Other

| Key | Action |
| --- | --- |
| `?` | toggle in-view help |
| `q` | quit |

## Initial state

The viewer starts with:

- exact queues collapsed;
- the serviced-frontier representation (largest prior service for a losing
  queue, actual term for the winner);
- numerical-value sorting;
- diagnostics hidden.

Every representation is rendered with the same `B`, `A`, `W` context used by
the ordinary human-readable `step` command and shows the current fresh-prime
ceiling `Q_n`.

## Implementation notes

The first experiment uses Rich directly for alternate-screen redraws and plain
POSIX cbreak input for single-key commands. It intentionally does not introduce
a TUI framework, widgets, mouse controls, saved preferences, or persistence.
Rendered documents are cached by `(step, representation, collapse, sort,
diagnostics, terminal width)`, so ordinary scrolling only crops the cached text
and does not rerun the formatter. A resize naturally selects a different cached
layout because the width changes.

The raw-terminal imports are isolated to `run_viewer`; importing or using the
ordinary CLI does not require POSIX terminal modules. The interactive `view`
command itself currently requires a POSIX terminal.
