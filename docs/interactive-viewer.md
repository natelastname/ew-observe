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
| `x` | sort by prime-factor lexicographic order |
| `d` | sort by queue depth |
| `r` | sort by retained continuity prime |
| `i` | toggle diagnostics/details |

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
the ordinary human-readable `step` command.

## Implementation notes

The first experiment uses Rich directly for alternate-screen redraws and plain
POSIX cbreak input for single-key commands. It intentionally does not introduce
a TUI framework, widgets, mouse controls, saved preferences, or persistence.
Rendered documents are cached by `(step, representation, collapse, sort,
diagnostics)`, so ordinary scrolling only crops the cached text and does not
rerun the formatter.

The raw-terminal imports are isolated to `run_viewer`; importing or using the
ordinary CLI does not require POSIX terminal modules. The interactive `view`
command itself currently requires a POSIX terminal.
