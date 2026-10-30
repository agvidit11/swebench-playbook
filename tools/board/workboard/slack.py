"""Slack face of the board: posts as the Metamate app into ONE private channel, only when a human is needed.

Design: /tmp/wb-slack/PLAN.md (local). Rules enforced here, not by convention:
- Posts go only through `meta agents.notification send-slack` (the Metamate app) and only to the configured channel;
  nothing in this module can post as the owner or to any other conversation.
- One thread per subject: everything about a task (or a session) is a reply under that subject's first post.
- Only necessary posts: blocked-needs-you, decisions, strict SUBMIT-READY, an hourly digest when something changed,
  and a morning brief. Nothing during quiet hours; each item is deduplicated.
- Inbound: only the owner's own replies/reactions count. CLI-posted text ("Sent via …") is ignored, and any answer
  within ±5 min of an agent writing to Slack (`slack_write` tripwire event) is refused. Slack answers settle
  task-level decisions only; they never submit, change settings, delete, or change policy.

Config (never in the repo): ~/.config/workboard/slack.local.toml
    channel_id = "C…"            owner_slack_user_id = "U…"
    host = "6971"                quiet_hours = "02:00-08:00"
State: ~/.cache/workboard/slack-state.json (this host only).
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import tempfile
import time
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

CONFIG = Path(os.environ.get("WORKBOARD_SLACK_CONFIG", "~/.config/workboard/slack.local.toml")).expanduser()
SUFFIX = re.compile(r"_?(Sent|Edited) (via .+|from Meta CLI)_?", re.I)
REPING_S = 4 * 3600
TRIPWIRE_S = 300
OPTION_EMOJI = {"one": "1", "two": "2", "three": "3", "four": "4", "white_check_mark": "yes", "x": "no"}
EMOJI_FOR = {"1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣"}
DECISION_RE = re.compile(r"^\s*(?:(undo)\s+)?(D-[0-9a-f]{4})\b\s*(.*)$", re.I | re.S)


# ---------------------------------------------------------------------------------------------------- config / state
def load_config() -> dict | None:
    try:
        cfg = tomllib.loads(CONFIG.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return None
    if not (str(cfg.get("channel_id", "")).startswith("C") and str(cfg.get("owner_slack_user_id", "")).startswith("U")):
        return None
    cfg.setdefault("quiet_hours", "02:00-08:00")
    return cfg


def state_path() -> Path:
    from .app import cache_dir
    return cache_dir() / "slack-state.json"


def load_state() -> dict:
    try:
        st = json.loads(state_path().read_text())
    except (OSError, ValueError):
        st = {}
    for k in ("threads", "posted", "decisions", "cursors", "days", "applied"):
        st.setdefault(k, {})
    return st


def save_state(st: dict) -> None:
    p = state_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1, sort_keys=True))
    tmp.replace(p)


# ---------------------------------------------------------------------------------------------------- transport
class Transport:
    """The only door to Slack. `dry` writes posts to a local file instead of sending."""

    def __init__(self, channel: str, dry: bool = False, runner=subprocess.run, outbox: Path | None = None):
        self.channel, self.dry, self.run = channel, dry, runner
        self.outbox = outbox or state_path().with_name("slack-outbox.md")
        self.n = 0

    def _meta(self, argv: list[str]) -> dict:
        p = self.run(["meta", *argv, "-o", "json"], capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            raise RuntimeError((p.stderr or p.stdout or "meta failed").strip()[:300])
        return json.loads(p.stdout or "{}")

    def post(self, markdown: str, thread_ts: str | None = None, context: str | None = None,
             buttons: list[tuple[str, str]] = ()) -> str:
        if self.dry:
            self.n += 1
            ts = f"dry.{int(time.time())}.{self.n}"
            with open(self.outbox, "a") as fh:
                fh.write(f"\n---- {ts}{' (reply to ' + thread_ts + ')' if thread_ts else ''}\n{markdown}\n"
                         + (f"_{context}_\n" if context else "") + "".join(f"[{l}]({u})\n" for l, u in buttons))
            return ts
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write(markdown)
        try:
            argv = ["agents.notification", "send-slack", f"--channel-id={self.channel}", f"--markdown=file://{fh.name}"]
            if thread_ts:
                argv.append(f"--thread-ts={thread_ts}")
            if context:
                argv.append(f"--context={context[:150]}")
            for label, url in list(buttons)[:3]:
                argv.append(f"--button={label}|{url}")
            out = self._meta(argv)
        finally:
            os.unlink(fh.name)
        return str(out.get("message_ts") or out.get("ts") or (out.get("data") or {}).get("message_ts") or "")

    def replies(self, root: str, oldest: str | None) -> list[dict]:
        if self.dry or root.startswith("dry."):
            return []
        argv = ["slack.message", "list", f"--channel-id={self.channel}", f"--thread-ts={root}", "--limit=20",
                "--columns=message_ts,author_user_id,is_author_bot,app_id,content,text"]
        if oldest:
            argv.append(f"--oldest={oldest}")
        try:
            return self._meta(argv).get("data") or []
        except (RuntimeError, ValueError):
            return []

    def reactions(self, ts: str) -> list[dict]:
        if self.dry or ts.startswith("dry."):
            return []
        try:
            return self._meta(["slack.reaction", "list", f"--channel-id={self.channel}", f"--message-ts={ts}"]).get("data") or []
        except (RuntimeError, ValueError):
            return []


# ---------------------------------------------------------------------------------------------------- formatting
def _link(view) -> str | None:
    return (view.fields.get("links") or {}).get("codimango") if view else None


def fmt_blocked(subject: str, item: dict) -> str:
    return (f"🚧 **Needs you** · {subject}\n\n"
            f"- **What:** {item['why']}\n"
            f"- **Where:** {item.get('where', '—')}\n"
            f"- **Why you:** {item.get('need', 'the supervisor cannot answer this one')}")


def fmt_decision(d: dict) -> str:
    opts = d.get("options") or []
    lines = [f"❓ **{d['id']}** · {d['task'] or 'general'}", "", f"**{d['question']}**", ""]
    for i, o in enumerate(opts, 1):
        star = "  ← _recommended_" if str(i) == str(d.get("recommend")) else ""
        lines.append(f"- {EMOJI_FOR.get(str(i), str(i))} {o}{star}")
    if not opts:
        lines.append("- ✅ yes   ·   ❌ no")
    lines += ["", f"React, or reply `{d['id']} 1` / `{d['id']} no <reason>`."]
    return "\n".join(lines)


def fmt_ready(view, commit: str) -> str:
    f = view.fields
    return (f"🚀 **SUBMIT-READY** · {view.entity_id} @ `{commit[:8]}`\n\n"
            "- validation **PASS** on this commit\n"
            "- presubmit: owner ✓ · independent ✓\n"
            "- agent review: owner ✓ · independent ✓\n"
            f"- no failing checks or findings · {f.get('kind') or ''}".rstrip(" ·") + "\n\n"
            "_You submit; the board never does._")


def fmt_digest(title: str, d: dict) -> str:
    out = [f"{title}", "", f"📈 **Week {d['week']}:** {d['this_week']} accepted (target 10–12) · "
                           f"last week at this point {d['same_point']}"]
    for icon, label, key in (("🚀", "Ready to submit", "ready"), ("⏳", "Validating", "validating"),
                             ("🚧", "Needs you", "needs"), ("⛔", "Don't submit", "dont"), ("↩️", "Since last", "since")):
        items = d.get(key) or []
        if items:
            out.append(f"{icon} **{label}:** " + " · ".join(items[:5]) + (f" · _+{len(items) - 5} more_" if len(items) > 5 else ""))
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------------- what to say
def strict_ready(view) -> str | None:
    """Commit when the task meets the strict SUBMIT-READY rule, else None."""
    f = view.fields
    if not str(f.get("next") or "").startswith(("SUBMIT", "RESUBMIT")) or f.get("valid") != "PASS":
        return None
    g = f.get("gates") or {}
    if not all((g.get(r) or {}).get(k, {}).get("state") == "ok" for r in ("author", "independent") for k in ("check", "review")):
        return None
    from .insights import validation_summary
    vs = validation_summary(f.get("validation") or [], f.get("tbr_status"))
    if any(i["severity"] in ("fail", "warn") for i in vs["issues"]) or f.get("dissent"):
        return None
    return ((f.get("equiv_commits") or [None])[0]) or f.get("server_sha") or "current"


def needs_you(servers: list[dict], evs: list[dict], now: float) -> dict[str, dict]:
    """{dedupe key: item} — only things a human must handle; machine flags stay with the supervisor."""
    out = {}
    for sv in servers:
        for a in sv.get("attention") or []:
            if a["why"].startswith("waiting for input") and _minutes(a["why"]) >= 15:
                out[f"session:{a['session_key']}|input"] = {
                    "subject": f"session · {a['name']}", "why": a["why"].split(" (")[0],
                    "where": f"server {sv['id']}, terminal tab “{a['name']}”",
                    "need": "only you can answer a prompt in a main session"}
    for e in evs:
        if e.get("type") == "escalate":
            pl = e.get("payload") or {}
            try:
                age = now - datetime.fromisoformat(e["occurred_at"]).timestamp()
            except ValueError:
                continue
            if age < 24 * 3600 and not pl.get("resolved"):
                subj = (e.get("entity") or {}).get("id") or pl.get("session") or "general"
                out[f"task:{subj}|esc:{e['event_id'][:8]}"] = {
                    "subject": subj, "why": pl.get("reason", "escalated"), "where": (e.get("actor") or {}).get("alias", ""),
                    "need": "the supervisor escalated it to you"}
    return out


def _minutes(why: str) -> int:
    m = re.search(r"(\d+)([mhd])", why)
    return 0 if not m else int(m.group(1)) * {"m": 1, "h": 60, "d": 1440}[m.group(2)]


def decisions(evs: list[dict]) -> dict[str, dict]:
    """Open/answered decisions reduced from `decision` events."""
    out = {}
    for e in sorted((e for e in evs if e.get("type") == "decision"), key=lambda e: e.get("occurred_at") or ""):
        pl = e.get("payload") or {}
        did = pl.get("id")
        if not did:
            continue
        if pl.get("action") == "ask":
            out[did] = {"id": did, "task": (e.get("entity") or {}).get("id"), "question": pl.get("question", ""),
                        "options": pl.get("options") or [], "recommend": pl.get("recommend"),
                        "asker": (e.get("actor") or {}).get("session_id"), "asker_alias": (e.get("actor") or {}).get("alias"),
                        "asker_host": e.get("host_id"), "at": e.get("occurred_at"), "answer": None}
        elif did in out and pl.get("action") == "answer":
            out[did]["answer"] = {"choice": pl.get("choice"), "reason": pl.get("reason", ""), "source": pl.get("source"),
                                  "at": e.get("occurred_at")}
        elif did in out and pl.get("action") == "undo":
            out[did]["answer"] = None
    return out


def tripwire_hit(evs: list[dict], at: float) -> dict | None:
    for e in evs:
        if e.get("type") == "slack_write":
            try:
                t = datetime.fromisoformat(e["occurred_at"]).timestamp()
            except ValueError:
                continue
            if abs(t - at) <= TRIPWIRE_S:
                return e
    return None


def parse_answer(text: str, pending_in_thread: list[dict]) -> tuple[str, str, str] | None:
    """(decision id, choice, reason) from an owner's reply; None when it isn't an answer."""
    text = (text or "").strip()
    m = DECISION_RE.match(text)
    if m:
        undo, did, rest = m.group(1), "D-" + m.group(2)[2:].lower(), m.group(3).strip()
        if undo:
            return did, "undo", ""
        choice, _, reason = rest.partition(" ")
        return did, _choice(choice), reason.strip()
    if len(pending_in_thread) == 1:
        word, _, reason = text.partition(" ")
        c = _choice(word)
        if c:
            return pending_in_thread[0]["id"], c, reason.strip()
    return None


def _choice(word: str) -> str:
    w = word.strip().lower().rstrip(".!")
    if w in ("1", "2", "3", "4"):
        return w
    if w in ("a", "b", "c", "d"):
        return str("abcd".index(w) + 1)
    if w in ("yes", "y", "ok", "approve", "approved", "go"):
        return "yes"
    if w in ("no", "n", "reject", "rejected", "stop"):
        return "no"
    return ""


# ---------------------------------------------------------------------------------------------------- the tick
def in_quiet(cfg: dict, tz: ZoneInfo, now: datetime) -> bool:
    a, b = cfg["quiet_hours"].split("-")
    loc = now.astimezone(tz).strftime("%H:%M")
    return a <= loc < b if a < b else (loc >= a or loc < b)


def tick(board_cfg, *, dry: bool = False, transport: Transport | None = None, snap=None, now: datetime | None = None,
         ignore_quiet: bool = False) -> dict:
    """One pass: read the board, post what is necessary, apply the owner's answers. Returns a summary."""
    from . import app, comms, events as ev_mod, stats, sync as sync_mod
    cfg = load_config()
    if not cfg:
        return {"skipped": f"no Slack config at {CONFIG}"}
    host = sync_mod.safe_host(sync_mod.host_id_for(board_cfg))
    if str(cfg.get("host")) != host:
        return {"skipped": f"daemon host is {cfg.get('host')}, this is {host}"}
    now = now or datetime.now(timezone.utc)
    tz = ZoneInfo(getattr(board_cfg.user, "timezone", "") or "America/Los_Angeles")
    tr = transport or Transport(cfg["channel_id"], dry=dry)
    st = load_state()
    snap = snap or app.gather(board_cfg, do_sync=False, light=True)
    views = {v.entity_id: v for v in snap.views}
    servers = comms.servers(snap.events, snap.views, board_cfg, getattr(snap, "sessions", []),
                            getattr(snap, "session_diagnostics", []), local_host=host)
    quiet = in_quiet(cfg, tz, now) and not ignore_quiet
    posted, applied = [], []

    def thread_for(subject: str, first: str, context: str | None = None, buttons=()) -> str:
        """Post `first` as the subject's root if the subject has no thread yet; else reply in it."""
        root = st["threads"].get(subject)
        ts = tr.post(first, thread_ts=root, context=context, buttons=buttons)
        if not root:
            st["threads"][subject] = ts
            st["cursors"][ts] = ts
        posted.append(subject)
        save_state(st)                                   # a later failure in this tick must not repost this
        return ts

    # 1) inbound first, so a fresh answer is never re-asked
    decs = decisions(snap.events)
    pending = {d: x for d, x in decs.items() if not x["answer"] and d in st["decisions"]}
    for subject, root in list(st["threads"].items()):
        cur = st["cursors"].get(root)
        for msg in tr.replies(root, cur):
            mts = str(msg.get("message_ts") or "")
            if not mts or mts == root or (cur and mts <= cur):
                continue
            st["cursors"][root] = mts
            if msg.get("author_user_id") != cfg["owner_slack_user_id"] or msg.get("app_id") or msg.get("is_author_bot"):
                continue
            text = msg.get("content") or msg.get("text") or ""
            if SUFFIX.search(text):
                tr.post("Ignored: a reply posted through the Meta CLI or by an agent doesn't count.", thread_ts=root)
                continue
            hit = tripwire_hit(snap.events, float(mts))
            here = [x for x in pending.values() if st["decisions"].get(x["id"], {}).get("thread") == root]
            ans = parse_answer(text, here)
            if ans and hit:
                tr.post(f"⚠️ Not applied: an agent ({(hit.get('actor') or {}).get('alias', '?')}) wrote to Slack within "
                        "5 minutes of this answer. Answer again in a minute, or in the terminal.", thread_ts=root)
                continue
            if ans:
                applied.append(_apply(board_cfg, decs, st, tr, root, *ans, source="slack-reply"))
            elif not quiet:
                _relay(board_cfg, snap, subject, text, tr, root)
    for did, x in pending.items():                       # reactions on decision posts
        meta = st["decisions"][did]
        owner = [r for r in tr.reactions(meta["ts"]) if cfg["owner_slack_user_id"] in (r.get("users") or r.get("user_ids") or [])]
        picks = {OPTION_EMOJI.get(str(r.get("name") or r.get("emoji") or "").strip(":")) for r in owner} - {None}
        if len(picks) == 1:
            if tripwire_hit(snap.events, time.time()):
                continue
            applied.append(_apply(board_cfg, decs, st, tr, meta["thread"], did, picks.pop(), "", source="slack-reaction"))
        elif len(picks) > 1 and not meta.get("asked_which"):
            tr.post(f"Which one for {did}? I see more than one reaction.", thread_ts=meta["thread"])
            meta["asked_which"] = True

    if quiet:
        save_state(st)
        return {"quiet": True, "applied": applied}

    # 2) morning brief = the day's root; hourly digests reply under it
    day = now.astimezone(tz).strftime("%Y-%m-%d")
    digest = _digest(board_cfg, snap, views, servers, decs, now)
    sig = json.dumps({k: digest[k] for k in ("ready", "validating", "needs", "dont", "this_week")}, sort_keys=True)
    if day not in st["days"]:
        digest = _digest(board_cfg, snap, views, servers, decs, now, since_h=18)        # the brief covers the night
        ts = tr.post(fmt_digest(f"🌅 **Good morning · {now.astimezone(tz):%a %b %-d}**", digest),
                     context="Hourly updates for today reply in this thread, only when something changed.")
        st["days"][day] = {"root": ts, "sig": sig, "at": now.isoformat()}
        posted.append("brief")
        save_state(st)
    else:
        d = st["days"][day]
        last = datetime.fromisoformat(d["at"])
        if sig != d["sig"] and now - last >= timedelta(minutes=55):
            tr.post(fmt_digest(f"🕐 **{now.astimezone(tz):%-I:%M %p} update**", digest), thread_ts=d["root"])
            d.update(sig=sig, at=now.isoformat())
            posted.append("hourly")
            save_state(st)

    # 3) blocked → needs you (deduped per key; re-ping after 4h or when the reason changes)
    for key, item in needs_you(servers, snap.events, now.timestamp()).items():
        prev = st["posted"].get(key)
        reason = re.sub(r"\d+[mhd]", "", item["why"].split(" (")[0]).strip()     # "waiting for input 22m" -> class
        if prev and prev["why"] == reason and now.timestamp() - prev["at"] < REPING_S:
            continue
        st["posted"][key] = {"why": reason, "at": now.timestamp()}
        thread_for(key.split("|")[0], fmt_blocked(item["subject"], item),
                   context="I'll only ping again if this is still blocked in 4 hours.")

    # 4) new decisions
    for did, d in decs.items():
        if d["answer"] or did in st["decisions"]:
            continue
        v = views.get(d["task"]) if d["task"] else None
        ts = thread_for(f"task:{d['task']}" if d["task"] else f"decision:{did}", fmt_decision(d),
                        context=f"asked by {d['asker_alias']} · settles a task choice only; never submits",
                        buttons=[("Open in codimango", _link(v))] if _link(v) else ())
        st["decisions"][did] = {"ts": ts, "thread": st["threads"].get(f"task:{d['task']}") or ts}
        save_state(st)

    # 5) strict SUBMIT-READY, once per (task, commit)
    for name, v in views.items():
        commit = strict_ready(v)
        if not commit or st["posted"].get(f"ready:{name}") == commit:
            continue
        st["posted"][f"ready:{name}"] = commit
        thread_for(f"task:{name}", fmt_ready(v, commit), buttons=[("Open in codimango", _link(v))] if _link(v) else ())

    save_state(st)
    return {"posted": posted, "applied": applied}


def _digest(board_cfg, snap, views, servers, decs, now, since_h: float = 1) -> dict:
    from . import stats
    wk = stats.week_numbers(snap.observations, board_cfg, now)
    ready = [n for n, v in views.items() if strict_ready(v)]
    validating = [n for n, v in views.items() if (v.fields.get("valid") == "RUN" or v.fields.get("next") == "WAIT validation")
                  and not v.fields.get("parked") and v.fields.get("group") != "DONE"]
    needs = [f"{d['id']} {d['task'] or ''}".strip() for d in decs.values() if not d["answer"]]
    needs += [a["name"] + ": " + a["why"].split(" (")[0] for sv in servers for a in sv.get("attention") or []
              if a["why"].startswith("waiting for input")]
    dont = [n for n, v in views.items() if v.fields.get("parked") and v.fields.get("state") not in ("ACCEPTED",)][:6]
    since = []
    cutoff = (now - timedelta(hours=since_h)).isoformat()
    for n, v in views.items():
        for dd in v.fields.get("decisions") or []:
            if str(dd.get("at") or "") >= cutoff:
                since.append(f"{n} {'accepted ✅' if dd.get('kind') == 'accept' else 'sent back ↩️'}")
    return {"week": wk.get("week", "?"), "this_week": wk.get("this_week", "?"), "same_point": wk.get("same_point_last_week", "?"),
            "ready": ready, "validating": validating, "needs": needs, "dont": dont, "since": since}


def _apply(board_cfg, decs, st, tr, root, did, choice, reason, *, source) -> str:
    """Record the owner's answer on the ledger, tell the asker through the courier, echo it in the thread."""
    from . import comms, coord, events as ev_mod, sync as sync_mod
    d = decs.get(did)
    if not d:
        tr.post(f"I don't know {did}. Check the id in the post above.", thread_ts=root)
        return f"{did}:unknown"
    state = sync_mod.default_state_dir()
    actor = {"session_id": "slack:owner", "alias": "Vidit (Slack)", "kind": "human"}
    if choice == "undo":
        coord.record(state, "decision", d["task"], actor, {"id": did, "action": "undo", "source": source})
        tr.post(f"↩️ {did} undone. It is open again.", thread_ts=root)
        return f"{did}:undo"
    opts = d.get("options") or []
    if opts and choice not in [str(i) for i in range(1, len(opts) + 1)]:
        tr.post(f"Which one for {did}? Reply with a number from 1 to {len(opts)}.", thread_ts=root)
        return f"{did}:ambiguous"
    label = opts[int(choice) - 1] if opts else choice
    coord.record(state, "decision", d["task"], actor, {"id": did, "action": "answer", "choice": choice,
                                                       "label": label, "reason": reason, "source": source})
    if d.get("asker"):
        target = {"to": f"session:{d['asker']}", "to_label": d.get("asker_alias") or "asker",
                  "resolved_recipients": [{"session_key": d["asker"], "native_id": d["asker"], "host": d.get("asker_host"),
                                           "name": d.get("asker_alias")}]}
        ev_mod.spool_append(state, comms.new_message(
            f"✅ decision {did} ({d['task'] or 'general'}): {label}" + (f" — {reason}" if reason else "") +
            " (Vidit via Slack; task-level only)", target, actor, task=d["task"]))
    sync_mod.sync(board_cfg, state_dir=state, timeout_seconds=15)
    tr.post(f"✔️ **{did} → {label}**" + (f" · _{reason}_" if reason else "") +
            f"\nRecorded and sent to {d.get('asker_alias') or 'the asker'}. Undo: `undo {did}`", thread_ts=root)
    return f"{did}:{choice}"


def _relay(board_cfg, snap, subject, text, tr, root) -> None:
    """A free-form owner reply in a task/session thread becomes a board message to whoever owns that subject."""
    from . import comms, coord, events as ev_mod, sync as sync_mod
    kind, _, key = subject.partition(":")
    try:
        if kind == "task":
            target = comms.target_for_task(key, snap.views, getattr(snap, "sessions", []))
        elif kind == "session":
            target = {"to": f"session:{key}", "to_label": key.rsplit(":", 1)[-1][:12]}
        else:
            target = comms.supervisor_target(snap.events, "supervisor", [s.id for s in board_cfg.servers] or [],
                                             sync_mod.safe_host(sync_mod.host_id_for(board_cfg)))
    except ValueError as exc:
        tr.post(f"Couldn't route this: {exc}. Try `board msg` from the terminal.", thread_ts=root)
        return
    state = sync_mod.default_state_dir()
    actor = {"session_id": "slack:owner", "alias": "Vidit (Slack)", "kind": "human"}
    ev_mod.spool_append(state, comms.new_message(f"(from Vidit on Slack — a request, not an approval) {text[:1500]}",
                                                 target, actor, task=key if kind == "task" else None))
    sync_mod.sync(board_cfg, state_dir=state, timeout_seconds=15)
    tr.post(f"↪️ Sent to {target.get('to_label')}. Their reply will land here.", thread_ts=root)


# ---------------------------------------------------------------------------------------------------- daemon
def run(board_cfg, *, dry: bool = False, interval: int = 60, once: bool = False) -> int:
    lock = open(state_path().with_name("slack.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0                                          # another tick/daemon holds it: exit quietly (cron-safe)
    beat = state_path().with_name("slack-heartbeat")
    while True:
        try:
            res = tick(board_cfg, dry=dry)
            beat.write_text(json.dumps({"at": datetime.now(timezone.utc).isoformat(), **res}, default=str))
        except Exception as exc:                          # never die on one bad tick
            beat.write_text(json.dumps({"at": datetime.now(timezone.utc).isoformat(), "error": f"{exc.__class__.__name__}: {exc}"[:300]}))
        if once:
            return 0
        time.sleep(interval)
