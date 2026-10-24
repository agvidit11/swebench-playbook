"""workboard CLI. `workboard` (or the `board` shim) with no command shows the list."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import __version__, render
from .config import load_config
from .registry import load_plugins

LAST_LOOK = "last-look.json"


def _style(args, cfg):
    color = args.color or cfg.ui.color
    uni = args.unicode or cfg.ui.unicode
    if args.plain:
        color, uni = "never", "never"
    return render.Style.detect(color, uni)


def _width(args):
    return args.width or shutil.get_terminal_size((120, 40)).columns


def _gather(args, cfg):
    from .app import gather
    return gather(cfg, refresh=args.refresh, do_sync=not args.no_sync)


def _unhealthy(snap) -> bool:
    bad = any(not h.ok for h in snap.health.values())
    st = snap.sync_state
    return bad or bool(st and not (st.last_pull_ok and (st.last_push_ok or not st.pending)))


def _view_json(v):
    return {"task": v.entity_id, **{k: val for k, val in v.fields.items()},
            "findings": [asdict(f) for f in v.findings]}


def _find(snap, name):
    exact = [v for v in snap.views if v.entity_id == name]
    if exact:
        return exact[0]
    near = [v for v in snap.views if name in v.entity_id]
    if len(near) == 1:
        return near[0]
    if near:
        sys.exit(f"ambiguous task {name!r}: " + ", ".join(v.entity_id for v in near[:8]))
    sys.exit(f"no task matching {name!r}")


def _save_look(snap):
    from .app import cache_dir
    data = {v.entity_id: {k: v.fields.get(k) for k in ("state", "valid", "next", "review", "owner", "group")}
            for v in snap.views}
    (cache_dir() / LAST_LOOK).write_text(json.dumps({"at": snap.now.isoformat(), "tasks": data}))


# ---------------------------------------------------------------------------------------------- commands
def cmd_list(args, cfg):
    from .stats import week_header
    snap = _gather(args, cfg)
    views = snap.views
    if args.mine:
        from . import sync as s
        me = s.safe_host(s.host_id_for(cfg))
        views = [v for v in views if v.fields.get("owner", "").startswith(me) or v.fields.get("claim_health") == "FREE"]
    if args.json:
        print(json.dumps({"health": {k: asdict(h) for k, h in snap.health.items()},
                          "tasks": [_view_json(v) for v in views]}, default=str, indent=1))
    else:
        warnings = [f.summary for f in snap.findings if f.code not in ("SYNC_FAILED",)] + cfg.warnings
        print(render.render_list(views, snap.health, now=snap.now, width=_width(args), style=_style(args, cfg),
                                 wide=args.wide, show_all=args.all, header=week_header(snap.observations, cfg, snap.now),
                                 sync_state=snap.sync_state, warnings=warnings))
    _save_look(snap)
    return 1 if args.strict and _unhealthy(snap) else 0


def _reviews_text(cfg, task):
    try:
        p = subprocess.run([cfg.codimango.command, "task", "reviews", task, "--full"], capture_output=True, text=True,
                           timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout if p.returncode == 0 else None


def cmd_show(args, cfg):
    snap = _gather(args, cfg)
    v = _find(snap, args.task)
    style = _style(args, cfg)
    if args.json:
        print(json.dumps(_view_json(v), default=str, indent=1))
        return 0
    f = v.fields
    print(style.paint(v.entity_id, "bold"))
    print(f"  NEXT     {f['next']}   ({f['group']})")
    print(f"  state    {f['state']} for {render.fmt_age(f.get('state_age_s'))}   validation {f['valid']}   sync {f['sync']}")
    print(f"  owner    {f.get('owner') or '-'} [{f.get('claim_health')}]")
    print(f"  review   {f['review']}  confidence {f.get('confidence') or '-'}{' (older commit)' if f.get('confidence_stale') else ''}"
          f"  dissent {f.get('dissent', 0)}")
    print(f"  check    {f['check']}{' (older commit)' if f.get('check_stale') else ''}")
    print(f"  commits  {f.get('pushes_before_submit', 0)} before submit, {f.get('pushes_after_submit', 0)} after")
    text = _reviews_text(cfg, v.entity_id) if not args.no_reviews else None
    if text:
        rounds = len(re.findall(r"^\s*REVISION by", text, re.M))
        accepts = len(re.findall(r"^\s*ACCEPT", text, re.M))
        print(f"  human    {rounds} revision round(s), {accepts} accept(s)  (codimango task reviews {v.entity_id} --full)")
    for x in v.findings:
        print(style.paint(f"  ! {x.code}: {x.summary} -> {x.next_action}", "amber"))
    tev = [e for e in snap.events if (e.get("entity") or {}).get("id") == v.entity_id]
    if tev:
        print("  history")
        for e in tev[-15:]:
            who = e["actor"].get("alias") or e["actor"].get("session_id")
            extra = {k: e["payload"][k] for k in list(e["payload"])[:3]}
            print(f"    {e['occurred_at'][:16]}  {e['type']:<8} {who}  {extra if extra else ''}")
    return 0


def cmd_explain(args, cfg):
    snap = _gather(args, cfg)
    v = _find(snap, args.task)
    obs = [o for o in snap.observations if o.entity_id == v.entity_id]
    print(f"{v.entity_id}: NEXT = {v.fields['next']} (group {v.fields['group']})")
    print("Why: the first matching rule wins — conflict > failing validation > newer push not on server > "
          "validating > waiting on reviewer > address review > draft ladder (check -> R1 -> R2 -> submit).")
    for o in obs:
        age = render.fmt_age(int((snap.now - o.observed_at).total_seconds()))
        print(f"  source {o.source} (observed {age} ago, {snap.health.get(o.source).detail if o.source in snap.health else ''})")
        for k, val in sorted(o.fields.items()):
            if k.endswith("validation") and isinstance(val, list):
                val = ", ".join(f"{d['name']}={d['status']}" for d in val)
            if isinstance(val, list) and len(val) > 6:
                val = f"{len(val)} items, newest {val[0]}"
            print(f"    {k} = {val}")
    print("  derived")
    for k, val in sorted(v.fields.items()):
        print(f"    {k} = {val}")
    for x in v.findings:
        print(f"  finding {x.code} [{x.severity}] {x.summary} -> {x.next_action}")
    return 0


def cmd_available(args, cfg):
    snap = _gather(args, cfg)
    free = [v for v in snap.views if v.fields.get("group") != "DONE" and v.fields.get("claim_health") in ("FREE", "EXPIRED")]
    style = _style(args, cfg)
    if args.json:
        print(json.dumps([_view_json(v) for v in free], default=str, indent=1))
        return 0
    if not free:
        print("Nothing available: every open task has a live owner.")
        return 0
    print(style.paint(f"{len(free)} task(s) nobody is working on (claim one with: workboard claim <task>)", "bold"))
    for v in free:
        why = "owner idle 24h+" if v.fields["claim_health"] == "EXPIRED" else "never claimed / released"
        print(f"  {render.middle(v.entity_id, 46):46}  {v.fields['next']:<16}  {v.fields['state']} "
              f"{render.fmt_age(v.fields.get('state_age_s')):>4}  {why}")
    return 0


def cmd_changes(args, cfg):
    from .app import cache_dir
    snap = _gather(args, cfg)
    try:
        prev = json.loads((cache_dir() / LAST_LOOK).read_text())
    except (OSError, ValueError):
        prev = None
    if args.since:
        m = re.fullmatch(r"(\d+)([mhd])", args.since)
        if not m:
            sys.exit("--since takes e.g. 30m, 2h, 3d")
        cutoff = snap.now - timedelta(**{{"m": "minutes", "h": "hours", "d": "days"}[m.group(2)]: int(m.group(1))})
        print(f"Ledger events since {cutoff.isoformat(timespec='minutes')}:")
        for e in snap.events:
            if datetime.fromisoformat(e["occurred_at"]) >= cutoff and e["type"] not in ("touch", "alias"):
                tid = (e.get("entity") or {}).get("id", "")
                print(f"  {e['occurred_at'][:16]}  {e['type']:<8} {tid}  {e['actor'].get('alias', '')}")
        return 0
    if not prev:
        print("No previous look recorded; showing nothing. Run `workboard` once, then `workboard changes` later.")
        _save_look(snap)
        return 0
    print(f"Changes since your last look ({prev['at'][:16]} UTC):")
    seen = 0
    for v in snap.views:
        before = prev["tasks"].get(v.entity_id)
        now = {k: v.fields.get(k) for k in ("state", "valid", "next", "review", "owner", "group")}
        if before is None:
            print(f"  NEW      {v.entity_id}  {now['state']}  next {now['next']}")
            seen += 1
            continue
        diff = [f"{k} {before[k]} -> {now[k]}" for k in ("state", "valid", "review", "owner", "next") if before.get(k) != now[k]]
        if diff:
            print(f"  CHANGED  {v.entity_id}: " + "; ".join(diff))
            seen += 1
    gone = set(prev["tasks"]) - {v.entity_id for v in snap.views}
    for g in sorted(gone):
        print(f"  GONE     {g}")
    if not seen and not gone:
        print("  nothing changed")
    _save_look(snap)
    return 0


def cmd_status(args, cfg):
    from . import sync as s
    from .app import gather
    snap = gather(cfg, refresh=args.refresh, do_sync=not args.no_sync)
    style = _style(args, cfg)
    print(render.banner(snap.health, style, snap.sync_state, snap.now))
    print(f"workboard {__version__} · config {cfg.path} · host {s.safe_host(s.host_id_for(cfg))}")
    for w in cfg.warnings:
        print(style.paint(f"  config: {w}", "amber"))
    reg = load_plugins(cfg)
    for w in reg.warnings:
        print(style.paint(f"  plugin: {w}", "amber"))
    st = snap.sync_state
    if st:
        print(f"  ledger: pull {'ok' if st.last_pull_ok else 'FAILED'}, push {'ok' if st.last_push_ok else 'not ok'}, "
              f"{st.pending} pending, at {st.at} {('— ' + st.error) if st.error else ''}")
    else:
        print("  ledger: not configured (set [ledger] remote in config)")
    for f in snap.findings:
        print(style.paint(f"  {f.code}: {f.summary} -> {f.next_action}", "amber"))
    checks = [("codimango CLI", shutil.which(cfg.codimango.command) is not None), ("git", shutil.which("git") is not None)]
    for repo in cfg.repositories:
        checks.append((f"repo {repo.id} at {repo.path}", Path(repo.path).expanduser().is_dir()))
    settings = Path("~/.claude/settings.json").expanduser()
    hooks = settings.exists() and "workboard" in settings.read_text(errors="replace")
    checks.append(("Claude hooks installed", hooks))
    for name, ok in checks:
        print(f"  {'ok ' if ok else 'NO '} {name}")
    return 1 if args.strict and _unhealthy(snap) else 0


def cmd_legend(args, cfg):
    print(render.legend(set(), _style(args, cfg), everything=True))
    return 0


def cmd_config(args, cfg):
    if args.action == "validate":
        print("config ok" if not cfg.warnings else "\n".join(cfg.warnings))
        return 0 if not cfg.warnings else 1
    print(f"# {cfg.path}")
    print(json.dumps(asdict(cfg), indent=1, default=str))
    return 0


def cmd_plugins(args, cfg):
    reg = load_plugins(cfg)
    for kind in ("sources", "columns", "checks", "stats"):
        print(f"{kind}: {', '.join(getattr(reg, kind)) or '-'}")
    for w in reg.warnings:
        print(f"warning: {w}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="workboard", description="Action-first board for your codimango work.")
    p.add_argument("--version", action="version", version=f"workboard {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    common.add_argument("--plain", action="store_true", help="no colour, no unicode")
    common.add_argument("--color", choices=["auto", "always", "never"])
    common.add_argument("--unicode", choices=["auto", "always", "never"])
    common.add_argument("--width", type=int, help="override terminal width")
    common.add_argument("--refresh", action="store_true", help="ignore caches, fetch live")
    common.add_argument("--no-sync", action="store_true", help="don't sync the ledger first")
    common.add_argument("--strict", action="store_true", help="exit 1 if any source is unhealthy")
    sub = p.add_subparsers(dest="cmd")
    lp = sub.add_parser("list", parents=[common], help="the board (default)")
    for q in (lp, p):
        pass
    for parser in (lp,):
        parser.add_argument("--wide", action="store_true", help="add ROUND, PUSHES, CHECK, TRACK")
        parser.add_argument("--all", action="store_true", help="include done tasks")
        parser.add_argument("--mine", action="store_true", help="only tasks owned on this host, or free")
    s = sub.add_parser("show", parents=[common], help="one task in full")
    s.add_argument("task")
    s.add_argument("--no-reviews", action="store_true", help="skip fetching human reviews")
    e = sub.add_parser("explain", parents=[common], help="every input and rule behind NEXT")
    e.add_argument("task")
    sub.add_parser("available", parents=[common], help="tasks nobody is working on")
    c = sub.add_parser("changes", parents=[common], help="what changed since your last look")
    c.add_argument("--since", help="ledger events in a window instead, e.g. 2h")
    sub.add_parser("status", parents=[common], help="health of sources, ledger, config, hooks")
    sub.add_parser("legend", parents=[common], help="every symbol explained")
    cf = sub.add_parser("config", parents=[common], help="show or validate config")
    cf.add_argument("action", choices=["show", "validate"], nargs="?", default="show")
    sub.add_parser("plugins", parents=[common], help="list loaded plugins")
    return p


COMMANDS = {"list": cmd_list, "show": cmd_show, "explain": cmd_explain, "available": cmd_available,
            "changes": cmd_changes, "status": cmd_status, "legend": cmd_legend, "config": cmd_config,
            "plugins": cmd_plugins}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-") and argv[0] not in ("-h", "--help", "--version"):
        argv = ["list", *argv]
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config()
    except ValueError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    return COMMANDS[args.cmd](args, cfg) or 0


if __name__ == "__main__":
    sys.exit(main())
