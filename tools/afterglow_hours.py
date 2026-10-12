"""The guide's clock: each stage is an hour of one evening, and a sheet's time is read from its place in the fall.

Spec: docs/superpowers/specs/2026-10-11-afterglow-guide-hour-design.md, §2.
"""

HOURS = ["19:12", "19:40", "20:15", "21:30"]

# (fall position, minutes after 19:12) at the four stage stops; past violet the clock keeps the violet rate until the ground
_STOPS = [(0, 0), (.30, 28), (.60, 63), (.84, 138)]
_VIOLET_RATE = (138 - 63) / (.84 - .60)


def _minutes(t):
    for (t0, m0), (t1, m1) in zip(_STOPS, _STOPS[1:]):
        if t <= t1:
            return m0 + (m1 - m0) * (t - t0) / (t1 - t0)
    return 138 + _VIOLET_RATE * (t - .84)


def hour_at(t: float) -> str:
    """The clock time at fall position t, or "dark" once the fall reaches the ground."""
    if t >= 1:
        return "dark"
    m = 12 + int(_minutes(max(0, t)) + .5)
    return f"{19 + m // 60:02d}:{m % 60:02d}"


def sheet_times(n_sheets: int = 15, n_fall: int = 13) -> list:
    """One time per sheet: the cover opens at 19:12, sheet k reads the top of its ground, sheets past the fall are dark."""
    return ["19:12"] + [hour_at((k - 1) / n_fall) if k <= n_fall else "dark" for k in range(2, n_sheets + 1)]


def stamp_times(html: str, n_fall: int) -> str:
    """Put each sheet's time before its page number, counting the sheets the document really has."""
    import re
    times = iter(sheet_times(html.count('<span class="pg">'), n_fall))
    return re.sub(r'<span class="pg">', lambda m: f'<span class="hr">{next(times)}</span>' + m.group(0), html)
