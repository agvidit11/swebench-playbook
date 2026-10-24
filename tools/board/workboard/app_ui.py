"""Interactive terminal app (`board ui`): tabs, toggle chips, search, selection with a detail panel, live refresh.

Keys: 1 board · 2 stats · ? help · ↑/↓ or j/k move · enter details · a/r/w/d toggle groups · f owner filter ·
/ search · esc clear · r refresh · q quit. Rendering reuses tui.render / tui.render_stats so the look is identical.
"""
from __future__ import annotations

import os
import select
import shutil
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime

from . import tui
from .render import fmt_age
from .tui import AMBER, BLUE, BOLD, DIM, GREEN, GREY, PINK, RED, RESET, SPINNER, VIOLET, bg, dwidth, fg, flow

GROUP_KEYS = {"a": "ATTENTION", "r": "READY", "w": "WAITING", "d": "DONE"}
OWNER_FILTERS = ["all", "free", "active", "mine"]


@dataclass
class UIState:
    tab: str = "board"
    groups: set = field(default_factory=lambda: {"ATTENTION", "READY", "WAITING"})
    owner: str = "all"
    query: str = ""
    typing: bool = False
    sel: int = 0
    detail: bool = False
    frame: int = 0


def visible(views, st: UIState, host_tag: str = "") -> list:
    out = []
    for v in views:
        f = v.fields
        if f.get("group") not in st.groups:
            continue
        h = f.get("claim_health")
        if st.owner == "free" and h not in ("FREE", "EXPIRED"):
            continue
        if st.owner == "active" and h not in ("ACTIVE", "OWNED"):
            continue
        if st.owner == "mine" and not (h in ("OWNED", "ACTIVE") and (f.get("owner") or "").startswith(host_tag + "·")):
            continue
        if st.query and st.query.lower() not in v.entity_id.lower():
            continue
        out.append(v)
    return out


def chips(st: UIState, counts: dict) -> list[str]:
    tabs = [(f"{bg(PINK)}{fg(16)}{BOLD} 1 Board {RESET}" if st.tab == "board" else f"{fg(GREY)} 1 Board {RESET}"),
            (f"{bg(PINK)}{fg(16)}{BOLD} 2 Stats {RESET}" if st.tab == "stats" else f"{fg(GREY)} 2 Stats {RESET}"),
            (f"{bg(PINK)}{fg(16)}{BOLD} ? Help {RESET}" if st.tab == "help" else f"{fg(GREY)} ? Help {RESET}")]
    if st.tab != "board":
        return tabs
    out = list(tabs)
    for key, g in GROUP_KEYS.items():
        colour, emoji, _ = tui.GROUP[g]
        on = g in st.groups
        out.append((f"{fg(colour)}{BOLD}[{key}] {emoji} {counts.get(g, 0)}{RESET}" if on
                    else f"{fg(238)}[{key}] {emoji} {counts.get(g, 0)}{RESET}"))
    out.append(f"{fg(VIOLET)}[f] 👤 {st.owner}{RESET}")
    if st.typing or st.query:
        cursor = "▏" if st.typing and st.frame % 2 == 0 else " "
        out.append(f"{fg(AMBER)}[/] 🔍 {st.query}{cursor}{RESET}")
    else:
        out.append(f"{fg(GREY)}[/] 🔍 search{RESET}")
    return out


def detail_panel(v, width: int) -> list[str]:
    f = v.fields
    lines = [f"{BOLD}{v.entity_id}{RESET}",
             f"{tui._next(f)}   {tui._pill(f.get('state', '?'), fmt_age(f.get('state_age_s')), f.get('age_level'))}",
             f"owner  {tui._owner(f)}   {fg(GREY)}({f.get('claim_health', '').lower()}){RESET}",
             f"checks validation {tui._tick_valid(f.get('valid', 'UNK'))}   presubmit {tui._check(f)}   "
             f"review {tui._ticks_review(f)}   sync {tui._sync(f.get('sync', 'OK'))}",
             f"pushes {fg(GREY)}{f.get('pushes_before_submit', 0)} before submit · {f.get('pushes_after_submit', 0)} after{RESET}"]
    for a in f.get("active") or []:
        lines.append(f"👀 {a['alias']} {fg(GREY)}touched it {fmt_age(a['ago_s'])} ago{RESET}")
    for x in v.findings:
        lines.append(f"{fg(AMBER)}⚠ {x.code}{RESET} {x.summary} {fg(GREY)}→ {x.next_action}{RESET}")
    lines.append(f"{fg(GREY)}more: board show {v.entity_id} · board explain {v.entity_id}{RESET}")
    return tui._panel("🔎 details", lines, width, BLUE)


HELP = [
    f"{BOLD}tabs{RESET}       1 board · 2 stats · ? help · tab cycles",
    f"{BOLD}move{RESET}       ↑/↓ or j/k · g top · G bottom · enter opens details",
    f"{BOLD}filters{RESET}    a 🔥 needs you · r ✨ ready · w ⏳ waiting · d 🎉 done · f owner: all → free → active → mine",
    f"{BOLD}search{RESET}     / then type part of a task name · enter keeps it · esc clears",
    f"{BOLD}live{RESET}       refreshes on its own (countdown at the bottom) · r refreshes now · ✦ marks rows that changed",
    f"{BOLD}ticks{RESET}      {fg(GREEN)}✓✓{RESET} two agent sessions approved · {fg(AMBER)}✓{RESET} one · {fg(GREY)}↻✓{RESET} approval on an older commit · ▰▰▰▰▱ confidence",
    f"{BOLD}owners{RESET}     👤 claimed · 👀 a session touched it recently · 📜 from CLAIMS.md · 💤 claim expired · 🔓 free",
    f"{BOLD}quit{RESET}       q or ctrl-c",
]


def screen(snap, cfg, st: UIState, *, width: int, height: int, changed: set, host_tag: str, status: str) -> str:
    views = snap.views
    counts = {g: sum(1 for v in views if v.fields.get("group") == g) for g in tui.GROUP}
    top = flow(chips(st, counts), width, sep="  ")
    if st.tab == "stats":
        body = tui.render_stats(snap, cfg, width=width)
        return "\n".join(top + [""] + body.splitlines() + flow([status], width))
    if st.tab == "help":
        return "\n".join(top + [""] + tui._panel("❓ keys", HELP, min(width, 130), PINK) + flow([status], width))
    vis = visible(views, st, host_tag)
    st.sel = max(0, min(st.sel, len(vis) - 1)) if vis else 0
    selected = vis[st.sel].entity_id if vis else None
    sub = type(snap)(vis, snap.observations, snap.events, snap.health, snap.findings, snap.sync_state, snap.now)
    board = tui.render(sub, cfg, width=width, changed=changed if (st.frame < 12 or st.frame % 2 == 0) else set(),
                       show_all="DONE" in st.groups, selected=selected, pulse=st.frame % 2 == 0)
    lines = top + [""] + board.splitlines()
    if st.detail and selected:
        lines += detail_panel(vis[st.sel], min(width, 140))
    if not vis:
        lines += flow([f"{fg(GREY)}no tasks match these filters — press a/r/w/d, f or esc{RESET}"], width)
    lines += flow([status], width)
    # keep the selected row on screen: if too tall, drop rows above it
    if len(lines) > height:
        sel_line = next((i for i, l in enumerate(lines) if "▶" in l or "▷" in l), 0)
        start = max(0, min(sel_line - height // 2, len(lines) - height))
        lines = lines[:len(top) + 1] + lines[len(top) + 1 + start: len(top) + 1 + start + height - len(top) - 2] + lines[-1:]
    return "\n".join(lines)


def _read_key(timeout: float) -> str | None:
    try:
        r, _, _ = select.select([sys.stdin], [], [], timeout)
    except (OSError, ValueError):
        time.sleep(timeout)
        return None
    if not r:
        return None
    ch = os.read(sys.stdin.fileno(), 1).decode("utf-8", "ignore")
    if ch == "\x1b":
        r2, _, _ = select.select([sys.stdin], [], [], 0.02)
        if r2:
            seq = os.read(sys.stdin.fileno(), 2).decode("utf-8", "ignore")
            return {"[A": "UP", "[B": "DOWN"}.get(seq, "ESC")
        return "ESC"
    return ch


def handle_key(st: UIState, key: str, n_visible: int) -> str | None:
    """Pure state transition. Returns 'quit' or 'refresh' when the loop should act."""
    if st.typing:
        if key in ("\r", "\n"):
            st.typing = False
        elif key == "ESC":
            st.typing, st.query = False, ""
        elif key in ("\x7f", "\b"):
            st.query = st.query[:-1]
        elif key and key.isprintable():
            st.query += key
            st.sel = 0
        return None
    if key in ("q", "\x03"):
        return "quit"
    if key == "1":
        st.tab = "board"
    elif key == "2":
        st.tab = "stats"
    elif key == "?":
        st.tab = "help"
    elif key == "\t":
        st.tab = {"board": "stats", "stats": "help", "help": "board"}[st.tab]
    elif key in ("j", "DOWN"):
        st.sel = min(st.sel + 1, max(0, n_visible - 1))
    elif key in ("k", "UP"):
        st.sel = max(0, st.sel - 1)
    elif key == "g":
        st.sel = 0
    elif key == "G":
        st.sel = max(0, n_visible - 1)
    elif key in ("\r", "\n"):
        st.detail = not st.detail
    elif key in GROUP_KEYS and st.tab == "board":
        st.groups ^= {GROUP_KEYS[key]}
    elif key == "f":
        st.owner = OWNER_FILTERS[(OWNER_FILTERS.index(st.owner) + 1) % len(OWNER_FILTERS)]
        st.sel = 0
    elif key == "/":
        st.typing, st.tab = True, "board"
    elif key == "ESC":
        st.query, st.detail = "", False
    elif key in ("r", "R") and st.tab != "board":
        return "refresh"
    elif key == "R":
        return "refresh"
    return None


def run(gather_fn, cfg, *, interval: int = 120, host_tag: str = "", out=sys.stdout) -> int:
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    st, prev, snap = UIState(), None, None
    out.write("\x1b[?1049h\x1b[?25l")
    try:
        tty.setcbreak(fd)
        while True:
            box = {}
            t = threading.Thread(target=lambda: box.setdefault("snap", gather_fn()), daemon=True)
            t.start()
            i = 0
            while t.is_alive():
                out.write(f"\x1b[H\x1b[2K  {fg(PINK)}{SPINNER[i % len(SPINNER)]}{RESET} refreshing your board…")
                out.flush()
                time.sleep(0.08)
                i += 1
            snap = box["snap"]
            changed = tui._changed_since(prev, snap)
            prev = {v.entity_id: {k: v.fields.get(k) for k in ("state", "valid", "next", "review", "owner")}
                    for v in snap.views}
            started, st.frame = time.monotonic(), 0
            while True:
                left = interval - (time.monotonic() - started)
                cols, rows = shutil.get_terminal_size((140, 40))
                bar_w = 20
                done_w = int(bar_w * (1 - max(0, left) / interval))
                status = (f"🕐 {fg(GREY)}{datetime.now():%H:%M:%S} · next refresh {int(max(0, left) // 60)}:"
                          f"{int(max(0, left) % 60):02d}{RESET} {fg(PINK)}{'━' * done_w}{RESET}{fg(238)}{'━' * (bar_w - done_w)}"
                          f"{RESET}  {fg(GREY)}? help · q quit{RESET}"
                          + (f"  {fg(PINK)}{'✦✧'[st.frame % 2]} {len(changed)} changed{RESET}" if changed else ""))
                out.write("\x1b[H\x1b[2J" + screen(snap, cfg, st, width=cols, height=rows, changed=changed,
                                                   host_tag=host_tag, status=status))
                out.flush()
                key = _read_key(0.5)
                st.frame += 1
                if key is None:
                    if left <= 0:
                        break
                    continue
                action = handle_key(st, key, len(visible(snap.views, st, host_tag)))
                if action == "quit":
                    return 0
                if action == "refresh":
                    break
    finally:
        out.write("\x1b[?25h\x1b[?1049l")
        out.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
