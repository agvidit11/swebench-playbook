"""Pretty board: boxed table, state pills, emoji, ticks, and a live `watch` mode with small animations.

Pure stdlib ANSI. Everything is measured in *display* width (emoji count as two cells), so columns stay aligned.
The classic renderer (render.py) remains the plain/piped output; this one is for colour TTYs.
"""
from __future__ import annotations

import os
import re
import select
import shutil
import sys
import time
import unicodedata
from datetime import datetime, timezone

from .render import fmt_age

ANSI = re.compile(r"\x1b\[[0-9;]*m")
RESET = "\x1b[0m"


def fg(n):
    return f"\x1b[38;5;{n}m"


def bg(n):
    return f"\x1b[48;5;{n}m"


BOLD, DIM, ITALIC = "\x1b[1m", "\x1b[2m", "\x1b[3m"

# palette (256-colour; readable on dark and light backgrounds)
GREEN, AMBER, RED, BLUE, VIOLET, GREY, PINK, TEAL = 114, 221, 203, 111, 141, 245, 211, 80
GROUP = {"ATTENTION": (RED, "🔥", "needs you"), "READY": (GREEN, "✨", "ready to act"),
         "WAITING": (BLUE, "⏳", "waiting"), "DONE": (GREY, "🎉", "done")}
PILL = {"DRAFT": (179, 16), "QUEUE": (110, 16), "REVIEW": (75, 16), "NEEDS_REV": (209, 16),
        "ACCEPTED": (114, 16), "ARCHIVED": (244, 16), "NOT_IMPORTED": (240, 255)}
NEXT_EMOJI = {"FIX": "🔧", "RESOLVE": "🤺", "RERUN": "🔁", "SUBMIT": "🚀", "GET": "👀", "RUN": "🧪",
              "WAIT": "⏳", "ADDRESS": "📝", "IMPORT": "📥", "CHECK": "🕐", "CLAIM": "✋", "—": "🎉"}
SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


# ------------------------------------------------------------------------------------------- width
def cell_width(ch: str) -> int:
    if ch in ("‍", "️", "︎") or unicodedata.combining(ch):
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    cp = ord(ch)
    if 0x1F300 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF and ch in "⚔✍✋✨⏳":
        return 2
    return 1


def dwidth(text: str) -> int:
    plain = ANSI.sub("", text)
    w = 0
    for i, ch in enumerate(plain):
        if ch == "️" and i and cell_width(plain[i - 1]) == 1:
            w += 1                      # emoji presentation selector widens the previous symbol
        else:
            w += cell_width(ch)
    return w


def pad(text: str, width: int, align: str = "left") -> str:
    gap = max(0, width - dwidth(text))
    return (" " * gap + text) if align == "right" else (text + " " * gap)


def clip(text: str, width: int) -> str:
    """Clip plain text to display width, keeping both ends (middle ellipsis)."""
    if dwidth(text) <= width:
        return text
    if width <= 1:
        return "…"[:width]
    head, tail = "", ""
    for ch in text:
        if dwidth(head + ch) > (width - 1) // 2:
            break
        head += ch
    for ch in reversed(text):
        if dwidth(head + "…" + ch + tail) > width:
            break
        tail = ch + tail
    return head + "…" + tail


# ------------------------------------------------------------------------------------------- cells
def _pill(state: str, age: str, level: str) -> str:
    b, f = PILL.get(state, (240, 255))
    label = state.replace("_", " ").title().replace("Needs Rev", "Sent Back")
    age_col = {"warn": AMBER, "block": RED}.get(level, GREY)
    return f"{bg(b)}{fg(f)} {label} {RESET} {fg(age_col)}{age}{RESET}"


def _tick_valid(v: str) -> str:
    return {"PASS": f"{fg(GREEN)}✔ pass{RESET}", "RUN": f"{fg(AMBER)}○ running{RESET}",
            "FAIL": f"{fg(RED)}✘ failed{RESET}"}.get(v, f"{fg(GREY)}· {v.lower() if v else '—'}{RESET}")


def _ticks_review(f) -> str:
    r, c, stale = f.get("review", "R0"), f.get("confidence") or 0, f.get("confidence_stale")
    bars = ("▰" * c + "▱" * (5 - c)) if c else ""
    colour = RED if c and c <= 2 else AMBER if c == 3 else GREEN
    if r == "R2":
        tick = f"{BOLD}{fg(GREEN)}✓✓{RESET}"
    elif r == "R1":
        tick = f"{fg(AMBER)}✓{RESET} "
    elif r == "R~":
        tick = f"{fg(GREY)}↻✓{RESET}"
    else:
        tick = f"{fg(GREY)}· {RESET}"
    conf = f" {fg(GREY if stale else colour)}{bars}{RESET}" if bars else ""
    return tick + conf


def _check(f) -> str:
    chk = f.get("check", "NONE")
    if chk == "NONE":
        return f"{fg(GREY)}· not run{RESET}"
    stale = f.get("check_stale")
    if f.get("check_fail"):
        return f"{fg(RED)}✘ {chk.split()[-1]}{RESET}" + (f" {fg(GREY)}↻{RESET}" if stale else "")
    return (f"{fg(GREY)}↻ ✔ old{RESET}" if stale else f"{fg(GREEN)}✔ {chk.split()[0]}{RESET}")


def _sync(s: str) -> str:
    if str(s).startswith("OK"):
        return f"{fg(GREEN)}✔{RESET}" + (f" {fg(GREY)}doc{RESET}" if "doc" in str(s) else "")
    if s in ("HEAD≠SERVER", "STALE_VALID"):
        return f"{fg(AMBER)}⚠ {'push' if s == 'HEAD≠SERVER' else 'stale'}{RESET}"
    return f"{fg(GREY)}·{RESET}"


def _owner(f) -> str:
    h, o = f.get("claim_health"), f.get("owner") or ""
    if h in ("FREE", None) or (not o and h != "DONE"):
        return f"{fg(BLUE)}🔓 free{RESET}"
    if h == "DONE":
        return ""
    if h == "CONFLICT":
        return f"{fg(RED)}🤺 {o}{RESET}"
    if h == "ACTIVE":
        ago = (f.get("active") or [{}])[0].get("ago_s")
        return f"{fg(AMBER)}👀 {o}{RESET}" + (f" {fg(GREY)}{fmt_age(ago)}{RESET}" if ago is not None else "")
    if h in ("EXPIRED", "LEGACY"):
        return f"{fg(GREY)}💤 {o}{RESET}" if h == "EXPIRED" else f"{fg(GREY)}📜 {o}{RESET}"
    return f"{fg(VIOLET)}👤 {o}{RESET}"


def _next(f) -> str:
    n = f.get("next", "")
    emoji = NEXT_EMOJI.get(n.split(" ")[0], "•")
    col = RED if n.startswith(("FIX", "RESOLVE")) else GREEN if n.startswith("SUBMIT") else \
        AMBER if n.startswith(("RERUN", "ADDRESS", "RUN", "GET", "CHECK")) else GREY
    return f"{emoji} {fg(col)}{n}{RESET}"


# ------------------------------------------------------------------------------------------- frame
COLUMNS = [  # key, title, min, max
    ("task", "Task", 18, 40), ("next", "Next", 14, 20), ("state", "State", 14, 18), ("owner", "Owner", 10, 24),
    ("valid", "Validation", 9, 11), ("check", "Presubmit", 8, 10), ("review", "Review", 6, 9), ("sync", "Sync", 4, 8),
]
DROP = ["check", "sync", "owner", "review", "valid"]


def _row_cells(v, changed: set) -> dict:
    f = v.fields
    star = f"{fg(PINK)}✦{RESET} " if v.entity_id in changed else "  "
    return {"task": (star, v.entity_id), "next": _next(f),
            "state": _pill(f.get("state", "?"), fmt_age(f.get("state_age_s")), f.get("age_level")),
            "owner": _owner(f), "valid": _tick_valid(f.get("valid", "UNK")), "check": _check(f),
            "review": _ticks_review(f), "sync": _sync(f.get("sync", "OK"))}


def _choose(widths_needed, width):
    cols = [c for c in COLUMNS]
    while True:
        total = 4 + sum(min(mx, max(mn, widths_needed[k])) for k, _, mn, mx in cols) + 3 * (len(cols) - 1) + 2
        if total <= width or not any(k in DROP for k, *_ in cols):
            return cols, total
        for d in DROP:
            if any(k == d for k, *_ in cols):
                cols = [c for c in cols if c[0] != d]
                break


def render(snap, cfg, *, width=None, changed: set | None = None, show_all=False, status_line: str = "",
           header_extra: str = "") -> str:
    from .stats import week_numbers
    width = width or shutil.get_terminal_size((140, 40)).columns
    changed = changed or set()
    views = snap.views
    active = [v for v in views if v.fields.get("group") != "DONE"]
    done = [v for v in views if v.fields.get("group") == "DONE"]
    shown = active + (done if show_all else [])
    counts = {g: sum(1 for v in views if v.fields.get("group") == g) for g in GROUP}
    out = []

    # header
    n = week_numbers(snap.observations, cfg, snap.now)
    trend = "📈" if n["this_week"] >= n["same_point_last_week"] else "📉"
    out.append(f"  🧭 {BOLD}{fg(PINK)}workboard{RESET}  {ITALIC}{fg(GREY)}your tasks across every server and session{RESET}"
               + (f"   {header_extra}" if header_extra else ""))
    out.append(f"  {trend} {BOLD}W{n['week']}{RESET}: {fg(GREEN)}{BOLD}{n['this_week']}{RESET} accepted"
               f" {fg(GREY)}· last week at this point {n['same_point_last_week']} · 4-week median {n['median_4wk']:g}{RESET}")
    # colour bar
    total = max(1, sum(counts.values()))
    bar_w = max(10, width - 4)
    segs, used = [], 0
    for g in ("ATTENTION", "READY", "WAITING", "DONE"):
        w = round(bar_w * counts[g] / total) if g != "DONE" else bar_w - used
        used += w
        segs.append(f"{fg(GROUP[g][0])}{'━' * max(0, w)}{RESET}")
    out.append("  " + "".join(segs))
    chips = "   ".join(f"{fg(GROUP[g][0])}●{RESET} {GROUP[g][1]} {GROUP[g][2]} {BOLD}{counts[g]}{RESET}"
                       for g in ("ATTENTION", "READY", "WAITING", "DONE"))
    out.append("  " + chips)
    health = []
    for name, h in snap.health.items():
        health.append(f"{fg(GREEN)}✔{RESET} {name}" if h.ok else f"{fg(RED)}✘ {name}{RESET}")
    st = snap.sync_state
    if st is not None:
        ok = st.last_pull_ok and (st.last_push_ok or not st.pending)
        health.append(f"{fg(GREEN)}✔{RESET} ledger" if ok else f"{fg(RED)}✘ ledger ({st.pending} pending){RESET}")
    out.append("  " + f"{fg(GREY)} · {RESET}".join(health))
    bad = [f"{k}: {h.detail}" for k, h in snap.health.items() if not h.ok]
    if bad:
        out.append(f"  {fg(RED)}{BOLD}⚠ showing cached data —{RESET} {fg(RED)}{'; '.join(bad)[:width - 26]}{RESET}")
    out.append("")

    if not shown:
        out.append(f"  🌈 nothing needs you right now — {len(done)} done")
        return "\n".join(out)

    rows = [(v, _row_cells(v, changed)) for v in shown]
    need = {k: dwidth(t) for k, t, *_ in COLUMNS}
    for _, c in rows:
        for k, *_ in COLUMNS:
            val = c[k][1] if k == "task" else c[k]
            need[k] = max(need[k], dwidth(val) + (2 if k == "task" else 0))
    cols, tot = _choose(need, width - 2)
    w = {k: min(mx, max(mn, need[k])) for k, _, mn, mx in cols}
    spare = (width - 2) - tot
    if spare < 0:                                        # shrink the task column to fit
        w["task"] = max(12, w["task"] + spare)
    inner = sum(w.values()) + 3 * (len(cols) - 1) + 2
    out.append(f"  {fg(238)}╭{'─' * (inner + 2)}╮{RESET}")
    head = "   ".join(f"{BOLD}{pad(t, w[k])}{RESET}" for k, t, *_ in cols)
    out.append(f"  {fg(238)}│{RESET}   {head} {fg(238)}│{RESET}")
    out.append(f"  {fg(238)}├{'─' * (inner + 2)}┤{RESET}")
    last_group = None
    for i, (v, c) in enumerate(rows):
        g = v.fields.get("group")
        if g != last_group and last_group is not None:
            out.append(f"  {fg(238)}│{' ' * (inner + 2)}│{RESET}")
        last_group = g
        stripe = f"{fg(GROUP.get(g, (GREY,))[0])}▌{RESET}"
        star, name = c["task"]
        cells = []
        for k, *_ in cols:
            if k == "task":
                cells.append(star + f"{BOLD}{clip(name, w[k] - 2)}{RESET}" + " " * max(0, w[k] - 2 - dwidth(clip(name, w[k] - 2))))
            else:
                val = c[k]
                if dwidth(val) > w[k]:
                    val = clip(ANSI.sub("", val), w[k])
                cells.append(pad(val, w[k]))
        line = f"  {fg(238)}│{RESET}{stripe} " + "   ".join(cells) + RESET
        out.append(pad(line, inner + 4) + f" {fg(238)}│{RESET}")
    out.append(f"  {fg(238)}╰{'─' * (inner + 2)}╯{RESET}")
    if done and not show_all:
        out.append(f"  🎉 {fg(GREY)}{len(done)} done (board --all){RESET}")
    out.append(f"  {fg(PINK)}✦{RESET} changed since last look   {fg(GREEN)}✓✓{RESET} two sessions approved   "
               f"{fg(AMBER)}✓{RESET} one   {fg(GREY)}↻✓{RESET} approved an older commit   ▰▰▰▰▱ confidence   "
               f"{fg(AMBER)}⚠{RESET} server out of date   🔓 free   👤 owner   📜 from CLAIMS.md")
    if status_line:
        out.append(status_line)
    return "\n".join(out)


# ------------------------------------------------------------------------------------------- watch
def _changed_since(prev: dict | None, snap) -> set:
    if not prev:
        return set()
    out = set()
    for v in snap.views:
        before = prev.get(v.entity_id)
        now = {k: v.fields.get(k) for k in ("state", "valid", "next", "review", "owner")}
        if before is None or any(before.get(k) != now[k] for k in now):
            out.add(v.entity_id)
    return out


def _key_ready(timeout: float) -> str | None:
    try:
        r, _, _ = select.select([sys.stdin], [], [], timeout)
        return sys.stdin.read(1) if r else None
    except (OSError, ValueError):
        time.sleep(timeout)
        return None


def watch(gather_fn, cfg, *, interval: int = 120, once: bool = False, out=sys.stdout) -> int:
    """Live view: alternate screen, spinner while refreshing, countdown bar, ✦ sparkle on changed rows.
    Keys: r refresh now · a toggle done · q quit."""
    import termios
    import tty
    fd = sys.stdin.fileno() if sys.stdin.isatty() else None
    old = termios.tcgetattr(fd) if fd is not None else None
    show_all, prev, snap = False, None, None
    out.write("\x1b[?1049h\x1b[?25l")                      # alternate screen, hide cursor
    try:
        if fd is not None:
            tty.setcbreak(fd)
        while True:
            # refreshing: small spinner animation while sources load
            import threading
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
            changed = _changed_since(prev, snap)
            prev = {v.entity_id: {k: v.fields.get(k) for k in ("state", "valid", "next", "review", "owner")}
                    for v in snap.views}
            started = time.monotonic()
            frame = 0
            while True:
                left = interval - (time.monotonic() - started)
                width = shutil.get_terminal_size((140, 40)).columns
                bar_w = 24
                done_w = int(bar_w * (1 - max(0, left) / interval))
                sparkle = "✦✧"[frame % 2] if changed else ""
                status = (f"  🕐 {fg(GREY)}refreshed {datetime.now():%H:%M:%S} · next in "
                          f"{int(left // 60)}:{int(left % 60):02d}{RESET} {fg(PINK)}{'━' * done_w}{RESET}"
                          f"{fg(238)}{'━' * (bar_w - done_w)}{RESET}   {fg(GREY)}r refresh · a show done · q quit{RESET}"
                          + (f"   {fg(PINK)}{sparkle} {len(changed)} changed{RESET}" if changed else ""))
                screen = render(snap, cfg, width=width, changed=changed if frame < 20 or frame % 2 == 0 else set(),
                                show_all=show_all, status_line=status)
                out.write("\x1b[H\x1b[2J" + screen)
                out.flush()
                if once:
                    return 0
                key = _key_ready(0.5)
                frame += 1
                if key in ("q", "Q", "\x1b"):
                    return 0
                if key in ("r", "R") or left <= 0:
                    break
                if key in ("a", "A"):
                    show_all = not show_all
    finally:
        out.write("\x1b[?25h\x1b[?1049l")
        out.flush()
        if old is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ------------------------------------------------------------------------------------------- stats
def _panel(title: str, lines: list[str], width: int, colour: int = 238) -> list[str]:
    inner = width - 6
    out = [f"  {fg(colour)}╭─{RESET} {BOLD}{title}{RESET} {fg(colour)}{'─' * max(0, inner - dwidth(title) - 1)}╮{RESET}"]
    for l in lines:
        if dwidth(l) > inner:
            l = clip(ANSI.sub("", l), inner)
        out.append(f"  {fg(colour)}│{RESET} {pad(l, inner)} {fg(colour)}│{RESET}")
    out.append(f"  {fg(colour)}╰{'─' * (inner + 2)}╯{RESET}")
    return out


def render_stats(snap, cfg, *, width=None, weeks=8, start=None, end=None, rank_data=None, per_repo=None,
                 quality=None) -> str:
    from . import stats as st
    width = min(width or shutil.get_terminal_size((120, 40)).columns, 140)
    rows = st.weekly(snap.observations, cfg, snap.now, weeks, start, end)
    n = st.week_numbers(snap.observations, cfg, snap.now)
    out = [f"  📊 {BOLD}{fg(PINK)}workboard stats{RESET}  {ITALIC}{fg(GREY)}how your work is flowing{RESET}", ""]

    # headline cards
    delta = n["this_week"] - n["same_point_last_week"]
    arrow = f"{fg(GREEN)}▲ {delta}{RESET}" if delta > 0 else f"{fg(RED)}▼ {-delta}{RESET}" if delta < 0 else f"{fg(GREY)}= 0{RESET}"
    flow = st.cycle_and_wait(snap.observations, snap.now, start, end)
    cards = [f"🏁 {BOLD}{fg(GREEN)}{n['this_week']}{RESET} accepted this week ({arrow} vs last week)",
             f"📅 4-week median {BOLD}{n['median_4wk']:g}{RESET}",
             f"🏆 all-time {BOLD}{n['total']}{RESET}"]
    out += _panel("this week", ["   ".join(cards)], width, PINK)

    # weekly bars, MT green + ST teal
    top = max([r["accepted"] for r in rows] + [1])
    bar_w = max(10, width - 52)
    lines = []
    this_mon = rows[-1]["week"] if rows else None
    for r in rows:
        mt = round(bar_w * r["accepted_mt"] / top)
        stw = round(bar_w * r["accepted_st"] / top)
        now_mark = f" {fg(PINK)}◀ now{RESET}" if r["week"] == this_mon and not start else ""
        lines.append(f"{fg(GREY)}{r['week']:%b %d}{RESET}  {fg(GREEN)}{'█' * mt}{RESET}{fg(TEAL)}{'█' * stw}{RESET}"
                     f"{' ' * (bar_w - mt - stw)} {BOLD}{r['accepted']:>3}{RESET} {fg(GREY)}({r['accepted_mt']}/{r['accepted_st']})"
                     f"  ↗ {r['submitted']:>2} sub  ✎ {r['worked_on']:>2} new{RESET}{now_mark}")
    lines.append(f"{fg(GREEN)}█{RESET} multi-turn  {fg(TEAL)}█{RESET} single-turn   trend {fg(PINK)}"
                 f"{st.spark([r['accepted'] for r in rows], True)}{RESET}")
    out += _panel("📈 accepted per week", lines, width, GREEN)

    # flow cards
    fmtd = lambda h: "—" if h is None else (f"{h / 24:.1f}d" if h >= 48 else f"{h:.0f}h")
    out += _panel("⏰ flow", [
        f"🔄 submit → accepted  {BOLD}{fmtd(flow['latest_round_cycle_p50_h'])}{RESET} typical"
        f" {fg(GREY)}(p75 {fmtd(flow['latest_round_cycle_p75_h'])}, {flow['latest_round_cycle_coverage']} tasks){RESET}",
        f"👀 waiting on reviewer  {BOLD}{fmtd(flow['wait_p50_h'])}{RESET} typical"
        f" {fg(GREY)}(p75 {fmtd(flow['wait_p75_h'])}, {flow['wait_coverage']} decisions){RESET}",
        f"{fg(GREY)}first-submission cycle: unavailable (codimango keeps only the latest submission){RESET}"], width, BLUE)

    # funnel
    f = st.funnel(snap.observations)
    steps = [("🧱 built", f["built"]), ("📥 imported", f["imported"]), ("📤 submitted", f["submitted"]),
             ("✅ accepted", f["accepted"])]
    topf = max(1, max(v for _, v in steps))
    fw = max(10, width - 44)
    lines, prev = [], None
    for label, v in steps:
        conv = f" {fg(GREY)}{round(100 * v / prev)}% of previous{RESET}" if prev else ""
        lines.append(f"{pad(label, 13)} {fg(VIOLET)}{'▇' * max(1, round(fw * v / topf))}{RESET} {BOLD}{v}{RESET}{conv}")
        prev = v or None
    lines.append(f"{fg(GREY)}📦 archived {f['archived']} ({f['archived_after_accept']} after acceptance) · 🔧 open {f['open']}{RESET}")
    if per_repo and per_repo.get("available"):
        top_repos = list(per_repo["by_repo"].items())[:6]
        lines.append(f"{fg(GREY)}🧩 most-used repos: " + ", ".join(f"{k.split('/')[-1]} {v}" for k, v in top_repos) + RESET)
    out += _panel("🧭 funnel", lines, width, VIOLET)

    # pipeline age
    ages = st.pipeline_age(snap.views, snap.now)
    if ages:
        topc = max(v["count"] for v in ages.values())
        aw = max(8, width - 60)
        lines = []
        for k, v in ages.items():
            b, ff = PILL.get(k, (240, 255))
            label = k.replace("_", " ").title().replace("Needs Rev", "Sent Back")
            lines.append(f"{bg(b)}{fg(ff)} {pad(label, 10)} {RESET} {fg(b)}{'●' * max(1, round(aw * v['count'] / topc))}{RESET}"
                         f" {BOLD}{v['count']}{RESET} {fg(GREY)}typical {fmtd(v['median_h'])}, oldest {fmtd(v['max_h'])}{RESET}")
        out += _panel("🕓 open work by state", lines, width, AMBER)

    if quality:
        r = quality["rounds"]
        out += _panel("🔁 quality", [f"sent back at least once {BOLD}{sum(1 for x in r.values() if x)}{RESET} · "
                                    f"revision rounds {BOLD}{sum(r.values())}{RESET} {fg(GREY)}(coverage "
                                    f"{quality['covered']}/{quality['eligible']}){RESET}"], width, RED)

    if rank_data:
        from .rank import pivot
        lines = []
        for row in pivot(rank_data["rows"]):
            medal = ""
            acc = row.get("accepted", "")
            m = re.search(r"#(\d+)/", acc)
            if m:
                medal = {"1": "🥇 ", "2": "🥈 ", "3": "🥉 "}.get(m.group(1), "🏅 ")
            lines.append(f"{medal}{BOLD}{clip(row['scope'], 28)}{RESET} {fg(GREY)}{clip(row['window'], 26)}{RESET}  "
                         f"✅ {acc}  📤 {row.get('submitted', '')}")
        out += _panel(f"🏆 rank {fg(GREY)}(from {rank_data['source']}, {rank_data['fetched_at'][:10]}){RESET}", lines, width, AMBER)

    out.append(f"  {fg(GREY)}{ITALIC}definitions: board stats --classic shows them in full{RESET}")
    return "\n".join(out)
