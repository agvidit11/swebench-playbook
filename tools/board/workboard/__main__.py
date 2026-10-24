"""workboard CLI. `workboard` (or the `board` shim) with no command shows the list."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
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
_CFG = [None]   # set in main(); lets helpers style output without threading cfg everywhere


def _style(args, cfg):
    cfg = cfg or _CFG[0]
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


def _envelope(snap, result) -> dict:
    return {"health": {k: asdict(h) for k, h in snap.health.items()},
            "sync_state": asdict(snap.sync_state) if snap.sync_state else None,
            "findings": [asdict(f) for f in snap.findings], "result": result}


def _emit(args, snap, result=None, human=None) -> int:
    """Finish a source-backed read: banner + human text, or the JSON envelope; strict exit code."""
    if args.json:
        print(json.dumps(_envelope(snap, result), default=str, indent=1))
    else:
        style = _style(args, None)
        print(render.banner(snap.health, style, snap.sync_state, snap.now, _width(args)))
        if human:
            print(human)
    return 1 if args.strict and _unhealthy(snap) else 0


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
    d = cache_dir()
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".look-")
    with os.fdopen(fd, "w") as fh:
        json.dump({"at": snap.now.isoformat(), "tasks": data}, fh)
    os.replace(tmp, d / LAST_LOOK)


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
        print(json.dumps(_envelope(snap, [_view_json(v) for v in views]), default=str, indent=1))
    else:
        warnings = [f.summary for f in snap.findings if f.code not in ("SYNC_FAILED",)] + cfg.warnings
        color = "never" if args.plain else (args.color or cfg.ui.color)
        uni = "never" if args.plain else (args.unicode or cfg.ui.unicode)
        print(render.render_list(views, snap.health, cfg, width=_width(args), color=color, unicode=uni,
                                 wide=args.wide, show_all=args.all, header=week_header(snap.observations, cfg, snap.now),
                                 sync_state=snap.sync_state, warnings=warnings, group=args.group, now=snap.now))
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
    tev = [e for e in snap.events if (e.get("entity") or {}).get("id") == v.entity_id]
    reviews = None if args.no_reviews else _reviews_text(cfg, v.entity_id)
    if not args.no_reviews:
        from .model import Finding, SourceHealth
        ok = reviews is not None
        snap.health["reviews"] = SourceHealth("reviews", ok, snap.now, 0, "ok" if ok else "codimango task reviews failed or timed out")
        if not ok:
            snap.findings.append(Finding("REVIEWS_UNAVAILABLE", "warn", "human reviews could not be fetched",
                                         f"codimango task reviews {v.entity_id} --full"))
    human_reviews = None
    if reviews is not None:
        human_reviews = {"revision_rounds": len(re.findall(r"^\s*REVISION by", reviews, re.M)),
                         "accepts": len(re.findall(r"^\s*ACCEPT", reviews, re.M))}
    if args.json:
        result = _view_json(v)
        result["human_reviews"] = human_reviews if reviews is not None else ("skipped" if args.no_reviews else "unavailable")
        if args.history:
            result["history"] = tev
        if args.sources:
            result["sources"] = [{"source": o.source, "fields": o.fields} for o in snap.observations if o.entity_id == v.entity_id]
        return _emit(args, snap, result)
    style = _style(args, cfg)
    f = v.fields
    lines = [style.paint(v.entity_id, "bold"),
             f"  NEXT     {f['next']}   ({f['group']})",
             f"  state    {f['state']} for {render.fmt_age(f.get('state_age_s'))}   validation {f['valid']}   sync {f['sync']}",
             f"  owner    {f.get('owner') or '-'} [{f.get('claim_health')}]",
             f"  agent review {f['review']}  confidence {f.get('confidence') or '-'}"
             f"{' (older commit)' if f.get('confidence_stale') else ''}  dissent {f.get('dissent', 0)}",
             f"  check    {f['check']}{' (older commit)' if f.get('check_stale') else ''}",
             f"  commits  {f.get('pushes_before_submit', 0)} before submit, {f.get('pushes_after_submit', 0)} after"]
    if human_reviews:
        lines.append(f"  human    {human_reviews['revision_rounds']} revision round(s), {human_reviews['accepts']} accept(s)")
    elif not args.no_reviews:
        lines.append(style.paint("  human    reviews unavailable (codimango task reviews failed or timed out)", "amber"))
    for x in v.findings:
        lines.append(style.paint(f"  ! {x.code}: {x.summary} -> {x.next_action}", "amber"))
    if tev and not args.history:
        lines.append(f"  history  {len(tev)} ledger event(s); see them with --history")
    if tev and args.history:
        lines.append(f"  history ({len(tev)})")
        for e in tev:
            who = e["actor"].get("alias") or e["actor"].get("session_id")
            extra = {k: e["payload"][k] for k in list(e["payload"])[:3]}
            lines.append(f"    {e['occurred_at'][:16]}  {e['type']:<8} {who}  {extra if extra else ''}")
    if args.sources:
        for o in snap.observations:
            if o.entity_id == v.entity_id:
                lines.append(f"  source {o.source}")
                lines += [f"    {k} = {val}" for k, val in sorted(o.fields.items())]
    return _emit(args, snap, human="\n".join(lines))


def cmd_explain(args, cfg):
    snap = _gather(args, cfg)
    v = _find(snap, args.task)
    obs = [o for o in snap.observations if o.entity_id == v.entity_id]
    if args.json:
        return _emit(args, snap, {"task": _view_json(v), "sources": [{"source": o.source, "observed_at": o.observed_at,
                                                                       "fields": o.fields} for o in obs]})
    _emit(args, snap)
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
    return 1 if args.strict and _unhealthy(snap) else 0


REASON = {"FREE": "never-claimed", "EXPIRED": "expired", "RELEASED": "released"}


def _available_reason(v, snap):
    if v.fields["claim_health"] == "EXPIRED":
        return "expired"
    tev = [e for e in snap.events if (e.get("entity") or {}).get("id") == v.entity_id]
    return "released" if any(e["type"] == "release" for e in tev) else "never-claimed"


def cmd_available(args, cfg):
    snap = _gather(args, cfg)
    free = [(v, _available_reason(v, snap)) for v in snap.views
            if v.fields.get("group") != "DONE" and v.fields.get("claim_health") in ("FREE", "EXPIRED")]
    if args.reason:
        free = [(v, r) for v, r in free if r == args.reason]
    if args.json:
        return _emit(args, snap, [dict(_view_json(v), reason=r) for v, r in free])
    style = _style(args, cfg)
    if not free:
        return _emit(args, snap, human="Nothing available: every open task has a live owner.")
    lines = [style.paint(f"{len(free)} task(s) nobody is working on (claim one with: workboard claim <task>)", "bold")]
    for v, r in free:
        lines.append(f"  {render.middle(v.entity_id, 46):46}  {v.fields['next']:<16}  {v.fields['state']} "
                     f"{render.fmt_age(v.fields.get('state_age_s')):>4}  {r}")
    return _emit(args, snap, human="\n".join(lines))


def cmd_changes(args, cfg):
    from .app import cache_dir
    snap = _gather(args, cfg)
    try:
        prev = json.loads((cache_dir() / LAST_LOOK).read_text())
    except (OSError, ValueError):
        prev = None
    if not args.json:
        _emit(args, snap)
    if args.since:
        m = re.fullmatch(r"(\d+)([mhd])", args.since)
        if m:
            cutoff = snap.now - timedelta(**{{"m": "minutes", "h": "hours", "d": "days"}[m.group(2)]: int(m.group(1))})
        else:
            try:
                cutoff = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
            except ValueError:
                sys.exit("--since takes a duration (30m, 2h, 3d) or an ISO timestamp with timezone")
            if cutoff.tzinfo is None:
                sys.exit("--since timestamp needs a timezone, e.g. 2026-10-23T09:00:00-07:00")
        hits = [e for e in snap.events if datetime.fromisoformat(e["occurred_at"]) >= cutoff and e["type"] not in ("touch", "alias")]
        if args.json:
            return _emit(args, snap, hits)
        print(f"Ledger events since {cutoff.isoformat(timespec='minutes')}:")
        for e in hits:
            tid = (e.get("entity") or {}).get("id", "")
            print(f"  {e['occurred_at'][:16]}  {e['type']:<8} {tid}  {e['actor'].get('alias', '')}")
        return 1 if args.strict and _unhealthy(snap) else 0
    if not prev:
        _save_look(snap)
        if args.json:
            return _emit(args, snap, {"since": None, "changes": []})
        print("No previous look recorded. Run `workboard` once, then `workboard changes` later.")
        return 1 if args.strict and _unhealthy(snap) else 0
    changes = []
    for v in snap.views:
        before = prev["tasks"].get(v.entity_id)
        now = {k: v.fields.get(k) for k in ("state", "valid", "next", "review", "owner", "group")}
        if before is None:
            changes.append({"task": v.entity_id, "kind": "NEW", "now": now})
            continue
        diff = {k: [before.get(k), now[k]] for k in ("state", "valid", "review", "owner", "next") if before.get(k) != now[k]}
        if diff:
            changes.append({"task": v.entity_id, "kind": "CHANGED", "diff": diff})
    for g in sorted(set(prev["tasks"]) - {v.entity_id for v in snap.views}):
        changes.append({"task": g, "kind": "GONE"})
    _save_look(snap)
    if args.json:
        return _emit(args, snap, {"since": prev["at"], "changes": changes})
    print(f"Changes since your last look ({prev['at'][:16]} UTC):")
    for c in changes:
        if c["kind"] == "NEW":
            print(f"  NEW      {c['task']}  {c['now']['state']}  next {c['now']['next']}")
        elif c["kind"] == "GONE":
            print(f"  GONE     {c['task']}")
        else:
            print(f"  CHANGED  {c['task']}: " + "; ".join(f"{k} {a} -> {b}" for k, (a, b) in c["diff"].items()))
    if not changes:
        print("  nothing changed")
    return 1 if args.strict and _unhealthy(snap) else 0


def cmd_status(args, cfg):
    from . import sync as s
    from .app import gather
    snap = gather(cfg, refresh=args.refresh, do_sync=not args.no_sync)
    style = _style(args, cfg)
    if args.json:
        reg = load_plugins(cfg)
        return _emit(args, snap, {"version": __version__, "config": cfg.path, "config_warnings": cfg.warnings,
                                  "plugin_warnings": reg.warnings, "host": s.safe_host(s.host_id_for(cfg))})
    print(render.banner(snap.health, style, snap.sync_state, snap.now, _width(args)))
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
    text = render.legend(set(), _style(args, cfg), everything=True, width=_width(args))
    print(json.dumps({"legend": text.splitlines()}) if args.json else text)
    return 0


def cmd_config(args, cfg):
    if args.action == "validate":
        if args.json:
            print(json.dumps({"ok": not cfg.warnings, "path": cfg.path, "warnings": cfg.warnings}))
        else:
            print("config ok" if not cfg.warnings else "\n".join(cfg.warnings))
        return 0 if not cfg.warnings else 1
    if args.json:
        print(json.dumps(asdict(cfg), default=str))
    else:
        print(f"# {cfg.path}")
        print(json.dumps(asdict(cfg), indent=1, default=str))
    return 0


def cmd_plugins(args, cfg):
    reg = load_plugins(cfg)
    if args.action == "doctor":
        if args.json:
            print(json.dumps({"ok": not reg.warnings, "enabled": cfg.plugins.enabled, "problems": reg.warnings}))
        else:
            print(f"{len(cfg.plugins.enabled)} plugin(s) enabled; " + ("all loaded" if not reg.warnings else "problems:"))
            for w in reg.warnings:
                print(f"  {w}")
        return 1 if reg.warnings else 0
    if args.json:
        print(json.dumps({k: sorted(getattr(reg, k)) for k in ("sources", "columns", "checks", "stats")} | {"warnings": reg.warnings}))
        return 0
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
    lp.add_argument("--wide", action="store_true", help="add ROUND, PUSHES, CHECK, TRACK")
    lp.add_argument("--all", action="store_true", help="include done tasks")
    lp.add_argument("--mine", action="store_true", help="only tasks owned on this host, or free")
    lp.add_argument("--group", choices=["attention", "state", "owner"], default="attention")
    s = sub.add_parser("show", parents=[common], help="one task in full")
    s.add_argument("task")
    s.add_argument("--no-reviews", action="store_true", help="skip fetching human reviews")
    s.add_argument("--history", action="store_true", help="every ledger event, not just the last 15")
    s.add_argument("--sources", action="store_true", help="raw source fields")
    e = sub.add_parser("explain", parents=[common], help="every input and rule behind NEXT")
    e.add_argument("task")
    av = sub.add_parser("available", parents=[common], help="tasks nobody is working on")
    av.add_argument("--reason", choices=["never-claimed", "expired", "released"])
    c = sub.add_parser("changes", parents=[common], help="what changed since your last look")
    c.add_argument("--since", help="ledger events in a window instead, e.g. 2h")
    sub.add_parser("status", parents=[common], help="health of sources, ledger, config, hooks")
    sub.add_parser("legend", parents=[common], help="every symbol explained")
    cf = sub.add_parser("config", parents=[common], help="show or validate config")
    cf.add_argument("action", choices=["show", "validate"], nargs="?", default="show")
    pl = sub.add_parser("plugins", parents=[common], help="list loaded plugins")
    pl.add_argument("action", choices=["list", "doctor"], nargs="?", default="list")
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
    _CFG[0] = cfg
    return COMMANDS[args.cmd](args, cfg) or 0


if __name__ == "__main__":
    sys.exit(main())
