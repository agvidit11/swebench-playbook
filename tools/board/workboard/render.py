"""Terminal rendering. Reads TaskViews only; never fetches. Words carry meaning, colour only repeats them."""
from __future__ import annotations

import os
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime

GROUPS = ("ATTENTION", "READY", "WAITING")
COMPACT = ["task", "next", "state", "owner", "valid", "review", "sync"]
WIDE_EXTRA = ["round", "pushes", "check", "track"]
DROP_ORDER = ["track", "round", "check", "pushes", "sync", "review", "valid", "owner", "state"]  # never "task"/"next"
HEAD = {"task": "TASK", "next": "NEXT", "state": "STATE/AGE", "owner": "OWNER", "valid": "VALID", "review": "REVIEW",
        "sync": "SYNC", "round": "ROUND", "pushes": "PUSHES", "check": "CHECK", "track": "TRACK"}
MAXW = {"task": 44, "next": 18, "state": 14, "owner": 28, "valid": 5, "review": 7, "sync": 11, "round": 5,
        "pushes": 7, "check": 12, "track": 8}
MINW = {"task": 18, "owner": 10}

C = {"green": "32", "amber": "33", "red": "31", "blue": "34", "dim": "2", "bold": "1"}
WORD_COLOUR = {"PASS": "green", "RUN": "amber", "FAIL": "red", "UNK": "dim", "OK": "green", "FREE": "blue",
               "EXPIRED": "dim", "CONFLICT": "red", "R2": "green", "R1": "amber", "R0": "dim", "R~": "dim"}
NEXT_COLOUR = {"FIX": "red", "RESOLVE": "red", "SUBMIT": "green", "WAIT": "dim"}


@dataclass
class Style:
    color: bool
    unicode: bool

    @classmethod
    def detect(cls, color: str = "auto", unicode: str = "auto", *, isatty: bool | None = None, env=None) -> "Style":
        env = os.environ if env is None else env
        isatty = os.isatty(1) if isatty is None else isatty
        dumb = env.get("TERM", "") == "dumb"
        use_color = color == "always" or (color == "auto" and isatty and not dumb and "NO_COLOR" not in env)
        utf = "UTF-8" in (env.get("LC_ALL") or env.get("LC_CTYPE") or env.get("LANG") or "").upper()
        use_uni = unicode == "always" or (unicode == "auto" and not dumb and (utf or isatty))
        return cls(use_color, use_uni)

    def paint(self, text: str, colour: str | None) -> str:
        if not self.color or not colour or not text.strip():
            return text
        return f"\x1b[{C[colour]}m{text}\x1b[0m"

    def g(self, uni: str, ascii_: str) -> str:
        return uni if self.unicode else ascii_


_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def wrap(text: str, width: int, indent: str = "  ") -> list[str]:
    """Wrap plain prose at word boundaries; continuation lines are indented. Never truncates."""
    if len(text) <= width:
        return [text]
    return textwrap.wrap(text, width=width, subsequent_indent=indent, break_long_words=True, break_on_hyphens=False)


def fmt_age(seconds) -> str:
    if seconds is None:
        return "?"
    if seconds < 60:
        return "<1m"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def middle(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    head = (width - 1) // 2
    tail = width - 1 - head
    return text[:head] + "…" + text[-tail:]


def _cells(v, style: Style) -> dict[str, tuple[str, str | None]]:
    """column -> (plain text, colour). Plain text is what width maths use."""
    f = v.fields
    stale = style.g("↻", "~")
    claim_health = f.get("claim_health", "")
    if claim_health in ("FREE", "DONE") or not f.get("owner"):
        owner = ("FREE", "blue") if claim_health != "DONE" else ("", None)
    elif claim_health in ("EXPIRED", "CONFLICT"):
        owner = (f"{claim_health} {f['owner']}", WORD_COLOUR[claim_health])
    elif claim_health == "LEGACY":
        owner = (f"LEGACY {f['owner']}", "dim")
    elif claim_health == "ACTIVE":
        owner = (f"ACTIVE {f['owner']}", "amber")
    else:
        owner = (f["owner"], None)
    review = f.get("review", "R0")
    if f.get("confidence"):
        review += f" C{f['confidence']}" if not f.get("confidence_stale") else f" {stale}C{f['confidence']}"
    conf = f.get("confidence") or 0
    review_colour = WORD_COLOUR.get(f.get("review"), None)
    if f.get("review") in ("R1", "R2") and conf:
        review_colour = "red" if conf <= 2 else ("amber" if conf == 3 else "green")
    check = f.get("check", "NONE")
    if f.get("check_stale") and check != "NONE":
        check = stale + check
    next_ = f.get("next", "")
    age_colour = {"warn": "amber", "block": "red"}.get(f.get("age_level"), None)
    pushes = f.get("pushes") or "0+0"
    track = "MT" if "multi" in (f.get("track") or "") else ("ST" if f.get("track") else "")
    return {
        "task": (v.entity_id, None),
        "next": (next_, NEXT_COLOUR.get(next_.split(" ")[0])),
        "state": (f"{f.get('state', '?')} {fmt_age(f.get('state_age_s'))}", age_colour),
        "owner": owner,
        "valid": (f.get("valid", "UNK"), WORD_COLOUR.get(f.get("valid"))),
        "review": (review, review_colour),
        "sync": (f.get("sync", "OK"), "green" if str(f.get("sync", "OK")).startswith("OK") else "amber"),
        "round": ("" if f.get("round") is None else str(f["round"]), None),
        "pushes": (pushes, None),
        "check": (check, "dim" if f.get("check_stale") or check == "NONE" else
                  ("red" if f.get("check_fail") else None)),
        "track": (track, None),
    }


def _layout(cols, rows, width):
    """Choose column widths; drop low-priority columns until the table fits the terminal."""
    cols = list(cols)
    while True:
        widths = {}
        for c in cols:
            longest = max([len(HEAD[c])] + [len(r[c][0]) for r in rows])
            widths[c] = min(longest, MAXW[c])
        total = sum(widths.values()) + 2 * (len(cols) - 1) + 2
        if total <= width:
            return cols, widths
        # shrink flexible columns first, then drop
        over = total - width
        for c in ("task", "owner"):
            if c in widths and over > 0:
                give = max(0, widths[c] - MINW[c])
                cut = min(give, over)
                widths[c] -= cut
                over -= cut
        if over <= 0:
            return cols, widths
        droppable = [c for c in DROP_ORDER if c in cols]
        if not droppable:
            return cols, widths
        cols.remove(droppable[0])


def banner(health: dict, style: Style, sync_state=None, now: datetime | None = None, width: int = 120) -> str:
    parts, failed = [], []
    ok_mark, bad_mark = style.g("✓", "ok"), style.g("!", "FAIL")
    for name, h in health.items():
        age = fmt_age(int((now - h.observed_at).total_seconds())) if (now and h.observed_at) else "?"
        parts.append((f"{name} {ok_mark} {age}", None) if h.ok else (f"{name} {bad_mark} {age}", "red"))
        if not h.ok:
            failed.append(f"{name}: {h.detail}")
    if sync_state is not None:
        if sync_state.last_pull_ok and (sync_state.last_push_ok or not sync_state.pending):
            parts.append((f"ledger {ok_mark}", None))
        else:
            parts.append((f"ledger {bad_mark} {sync_state.pending} pending", "red"))
            if sync_state.error:
                failed.append(f"ledger: {sync_state.error}")
    lines = []
    if failed:
        for i, l in enumerate(wrap("SYNC FAILED — " + "; ".join(failed), width)):
            lines.append(style.paint(l, "red") if i == 0 else l)
    # status parts: wrap on the separator
    cur, cur_len = "", 0
    for text, colour in parts:
        sep = " · " if cur else ""
        if cur and cur_len + len(sep) + len(text) > width:
            lines.append(cur)
            cur, cur_len, sep = "", 0, ""
        cur += sep + style.paint(text, colour)
        cur_len += len(sep) + len(text)
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def legend(symbols: set[str], style: Style, everything: bool = False, width: int = 120) -> str:
    stale = style.g("↻", "~")
    items = [
        ("PASS", "PASS passing"), ("RUN", "RUN validating"), ("FAIL", "FAIL failing"), ("UNK", "UNK unknown"),
        ("R0", "R0 no agent-session review"), ("R1", "R1 one agent session approved"),
        ("R2", "R2 two agent sessions approved"), ("R~", "R~ agent review on an older commit"),
        ("C", "C4 confidence 4/5"), ("STALE", f"{stale} result from an older commit"),
        ("FREE", "FREE nobody owns it"), ("ACTIVE", "ACTIVE a session touched it recently (no claim)"), ("LEGACY", "LEGACY owner from CLAIMS.md (advisory, 7 days)"), ("EXPIRED", "EXPIRED owner idle 24h+"), ("CONFLICT", "CONFLICT two owners"),
        ("HEAD≠SERVER", "HEAD≠SERVER newer push not on server"), ("STALE_VALID", "STALE_VALID validated an older commit"),
        ("OK·doc", "OK·doc only docs changed since validation"), ("UNCHECKED", "UNCHECKED drift not checked"),
        ("PUSHES", "2+1 commits before+after submit"),
    ]
    shown = [text for key, text in items if everything or key in symbols]
    if not shown:
        return ""
    lines, cur = [], "Legend:"
    for t in shown:
        if len(cur) + 2 + len(t) > width:
            lines.append(cur)
            cur = "       "
        cur += "  " + t
    lines.append(cur)
    if style.color:
        lines += wrap("colour only repeats the word: green good · amber waiting · red blocking · dim stale", width, "        ")
    return "\n".join(lines)


def _symbols(views, cols) -> set[str]:
    s = set()
    for v in views:
        f = v.fields
        for key in ("valid", "review", "claim_health", "sync"):
            if f.get(key):
                s.add(f[key])
        if f.get("confidence"):
            s.add("C")
        if f.get("confidence_stale") or (f.get("check_stale") and "check" in cols):
            s.add("STALE")
    if "pushes" in cols:
        s.add("PUSHES")
    return s


def render_list(views, health, cfg=None, *, width=120, color="auto", unicode="auto", wide=False, show_all=False,
                header="", sync_state=None, warnings=(), group="attention", now: datetime | None = None) -> str:
    """Public entry point: detects style from color/unicode (+ NO_COLOR, TERM, TTY) and renders the board."""
    from datetime import timezone
    style = Style.detect(color, unicode)
    return _render_list(views, health, now=now or datetime.now(timezone.utc), width=width, style=style, wide=wide,
                        show_all=show_all, header=header, sync_state=sync_state, warnings=warnings, group=group)


def _group_key(v, mode):
    if mode == "state":
        return v.fields.get("state", "?")
    if mode == "owner":
        return v.fields.get("owner") or v.fields.get("claim_health", "FREE")
    return v.fields.get("group")


def _render_list(views, health, *, now, width=120, style: Style, wide=False, show_all=False, header="",
                 sync_state=None, warnings=(), group="attention") -> str:
    out = [banner(health, style, sync_state, now, width)]
    if header:
        out += wrap(header, width)
    for w in warnings:
        out += [style.paint(l, "amber") for l in wrap(f"warning: {w}", width)]
    active = [v for v in views if v.fields.get("group") != "DONE"]
    done = [v for v in views if v.fields.get("group") == "DONE"]
    if not active and not (show_all and done):
        out.append("No tasks need attention." if done else "No tasks.")
        if done:
            out.append(f"Done: {len(done)} (use --all)")
        return "\n".join(out)
    cols = COMPACT + (WIDE_EXTRA if wide else [])
    visible = active + (done if show_all else [])
    rows = [_cells(v, style) for v in visible]
    cols, widths = _layout(cols, rows, width)
    head = "  " + "  ".join(HEAD[c].ljust(widths[c]) for c in cols)
    out.append(style.paint(head.rstrip(), "bold"))
    if group == "attention":
        groups = list(GROUPS) + (["DONE"] if show_all else [])
    else:
        groups = sorted({_group_key(v, group) for v in visible}, key=str)
    for g in groups:
        members = [(v, r) for v, r in zip(visible, rows) if _group_key(v, group) == g]
        if not members:
            continue
        for line in wrap(f"{g} ({len(members)})", width):
            out.append(style.paint(line, "bold"))
        for v, r in members:
            cells = []
            for c in cols:
                text, colour = r[c]
                text = middle(text, widths[c]) if c in ("task", "owner") else text[:widths[c]] if c != "next" else text
                cells.append(style.paint(text.ljust(widths[c]), colour))
            out.append(("  " + "  ".join(cells)).rstrip())
    if done and not show_all:
        out.append(f"Done: {len(done)} (use --all)")
    leg = legend(_symbols(visible, cols), style, width=width)
    if leg:
        out.append(leg)
    return "\n".join(out)
