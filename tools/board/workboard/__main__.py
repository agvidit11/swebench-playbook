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


def status_checks(cfg) -> list[dict]:
    """Dependency / installation checks shared by human and JSON status."""
    from . import hooks as hk
    out = [{"name": "codimango CLI", "ok": shutil.which(cfg.codimango.command) is not None},
           {"name": "git", "ok": shutil.which("git") is not None}]
    for repo in cfg.repositories:
        out.append({"name": f"repo {repo.id} at {repo.path}", "ok": Path(repo.path).expanduser().is_dir()})
    settings = Path("~/.claude/settings.json").expanduser()
    try:
        data = json.loads(settings.read_text())
        hooks_cfg = data.get("hooks", {}) if isinstance(data, dict) else {}
        installed = {ev for ev, entries in hooks_cfg.items()
                     if isinstance(entries, list) and any(hk._ours(e) for e in entries)}
        detail = ""
    except (OSError, ValueError) as exc:
        installed, detail = set(), f"settings unreadable: {exc.__class__.__name__}"
    need = {"SessionStart", "PreToolUse", "PostToolUse"}
    out.append({"name": "Claude hooks installed", "ok": need <= installed,
                "detail": detail or ("missing: " + ", ".join(sorted(need - installed)) if need - installed else "all three")})
    cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout if shutil.which("crontab") else ""
    good = [l for l in cron.splitlines() if not l.lstrip().startswith("#")
            and re.match(r"^\*/2\s+\*\s+\*\s+\*\s+\*\s+\S*board sync\b", l.strip())]
    out.append({"name": "background sync (cron */2 board sync)", "ok": bool(good),
                "detail": "" if good else ("found a board sync line with another schedule" if "board sync" in cron else "not installed")})
    return out


def cmd_status(args, cfg):
    from . import sync as s
    from .app import gather
    snap = gather(cfg, refresh=args.refresh, do_sync=not args.no_sync)
    style = _style(args, cfg)
    reg = load_plugins(cfg)
    checks = status_checks(cfg)
    failed = [c for c in checks if not c["ok"]]
    code = 1 if args.strict and (_unhealthy(snap) or failed) else 0
    if args.json:
        print(json.dumps(_envelope(snap, {"version": __version__, "config": cfg.path, "config_warnings": cfg.warnings,
                                          "plugin_warnings": reg.warnings, "host": s.safe_host(s.host_id_for(cfg)),
                                          "checks": checks}), default=str, indent=1))
        return code
    print(render.banner(snap.health, style, snap.sync_state, snap.now, _width(args)))
    print(f"workboard {__version__} · config {cfg.path} · host {s.safe_host(s.host_id_for(cfg))}")
    for w in cfg.warnings:
        print(style.paint(f"  config: {w}", "amber"))
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
    for c in checks:
        print(f"  {'ok ' if c['ok'] else 'NO '} {c['name']}{(' — ' + c['detail']) if c.get('detail') and not c['ok'] else ''}")
    return code


def _resolve_session(snap, fragment):
    """Session whose latest alias contains fragment; keeps the actor's recorded kind/host/person."""
    latest = {}
    for e in snap.events:
        sid = e["actor"].get("session_id")
        if sid:
            alias = e["payload"].get("alias") if e["type"] == "alias" and isinstance(e["payload"].get("alias"), str) else None
            prev = latest.get(sid, dict(e["actor"]))
            latest[sid] = dict(e["actor"], alias=alias or prev.get("alias") or e["actor"].get("alias", ""))
    hits = {sid: a for sid, a in latest.items() if fragment.lower() in a.get("alias", "").lower()}
    if len(hits) == 1:
        sid, actor = next(iter(hits.items()))
        return {"session_id": sid, "alias": actor.get("alias", ""), "kind": actor.get("kind", "claude"),
                "host": actor.get("host") or actor.get("alias", "").split("·", 1)[0], "person": actor.get("person", "")}
    if not hits:
        raise SystemExit(f"no known session matches {fragment!r} (sessions appear once they have run with the hooks)")
    raise SystemExit(f"ambiguous session {fragment!r}: " + ", ".join(sorted(a.get("alias", "") for a in hits.values())[:6]))


def cmd_claim(args, cfg):
    from . import coord, sync as s
    state = s.default_state_dir()
    ok, err = coord.ledger_fresh(cfg, state)
    if not ok:
        print(f"refusing to claim: ledger did not sync ({err})", file=sys.stderr)
        return 2
    snap = _gather(args, cfg)
    task = _find(snap, args.task).entity_id
    to_actor = _resolve_session(snap, args.to) if args.to else None
    source_ok = bool(snap.health.get("claims") and snap.health["claims"].ok)
    view = _find(snap, task)
    clock_ok = not any(f.code == "CLOCK_SKEW" for f in view.findings + list(snap.findings))
    res = coord.claim(cfg, task, state_dir=state, to_actor=to_actor, steal=args.steal,
                      source_healthy=source_ok if args.steal else None, clock_healthy=clock_ok if args.steal else None)
    s.sync(cfg, state_dir=state)
    if args.json:
        print(json.dumps(asdict(res)))
    elif res.status == "ACQUIRED":
        print(f"claimed {task} for {(to_actor or res.owner).get('alias')}")
    elif res.status == "LOST":
        print(f"{task} is already owned by {res.owner.get('alias')} (since {res.owner.get('acquired_at')})")
    else:
        print(f"{res.status}: {res.detail}")
    return 0 if res.status == "ACQUIRED" else 1


def cmd_release(args, cfg):
    from . import coord, sync as s
    state = s.default_state_dir()
    ok, err = coord.ledger_fresh(cfg, state)
    if not ok:
        print(f"refusing to release: ledger did not sync ({err})", file=sys.stderr)
        return 2
    res = coord.release(cfg, args.task, args.reason, state_dir=state)
    s.sync(cfg, state_dir=state)
    if args.json:
        print(json.dumps(asdict(res)))
    else:
        print(f"{res.status}: {args.task} {res.detail}")
    return 0 if res.status == "RELEASED" else 1


def cmd_hook(args, cfg):
    """Entry point for Claude Code hooks: reads hook JSON on stdin; prints nothing on stdout."""
    try:
        from . import hooks, sync as s
        raw = sys.stdin.read(1_000_000)
        try:
            data = json.loads(raw)
        except ValueError:
            data = None
        res = hooks.handle(args.kind, data, cfg=cfg, state_dir=s.default_state_dir(), host_id=s.safe_host(s.host_id_for(cfg)))
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        return res.code
    except Exception:
        return 0


def cmd_sync(args, cfg):
    from . import app, sync as s
    st = s.sync(cfg, state_dir=s.default_state_dir())
    app.refresh_claims_cache(cfg, s.default_state_dir())
    if not args.quiet:
        print(json.dumps(asdict(st)) if args.json else
              f"ledger: pull {'ok' if st.last_pull_ok else 'FAILED'}, push {'ok' if st.last_push_ok else 'not ok'}, "
              f"{st.pending} pending {('— ' + st.error) if st.error else ''}")
    return 0 if (st.last_pull_ok and (st.last_push_ok or not st.pending)) else 1


def cmd_install_hooks(args, cfg):
    from . import hooks
    settings = Path(args.settings).expanduser()
    board = str(Path(__file__).resolve().parent.parent / "board")
    if args.uninstall:
        hooks.uninstall(settings)
        print(f"removed workboard hooks from {settings} (backup kept next to it)")
        return 0
    text = hooks.install(settings, board, dry_run=args.dry_run)
    if args.dry_run:
        print(text)
        return 0
    print(f"installed workboard hooks into {settings} (backup kept next to it; only hook entries changed)")
    line = f"*/2 * * * * {board} sync --quiet >/dev/null 2>&1"
    print("To keep claim data fresh (needed for edit-blocking), add this cron line (crontab -e):")
    print(f"  {line}")
    return 0


def cmd_check(args, cfg):
    from . import checks, sync as s
    state = s.default_state_dir()
    code = checks.run_check(cfg, args.task, state_dir=state)
    s.sync(cfg, state_dir=state, timeout_seconds=10)
    return code


def cmd_review(args, cfg):
    from . import checks, sync as s
    state = s.default_state_dir()
    if args.action == "list":
        snap = _gather(args, cfg)
        task = _find(snap, args.task).entity_id
        revs = sorted((e for e in snap.events if e["type"] == "review" and (e.get("entity") or {}).get("id") == task),
                      key=lambda e: (e["occurred_at"], e["host_id"], e["seq"]))
        if args.json:
            return _emit(args, snap, revs)
        lines = [f"{len(revs)} agent-session review(s) of {task}:"]
        for e in revs:
            p = e["payload"]
            lines.append(f"  {e['occurred_at'][:16]}  {p.get('verdict'):<8} C{p.get('confidence', '-')}  "
                         f"@{(e.get('commit') or '?')[:8]}  {e['actor'].get('alias', '')}  {p.get('note', '')}")
        return _emit(args, snap, human="\n".join(lines))
    if not args.verdict:
        print("review add needs --verdict ready|changes|comment", file=sys.stderr)
        return 2
    from . import coord
    fresh, why = coord.ledger_fresh(cfg, state)
    if not fresh:
        print(f"refusing to add review: ledger did not sync ({why})", file=sys.stderr)
        return 2
    ok, detail = checks.add_review(cfg, args.task, args.verdict, args.confidence, args.note or "", state_dir=state)
    if not ok:
        print(f"review refused: {detail}", file=sys.stderr)
        return 2
    st = s.sync(cfg, state_dir=state, timeout_seconds=10)
    if not (st.last_pull_ok and st.last_push_ok and not st.pending):
        print(f"review on {detail[:8]} is queued locally but NOT yet in the ledger ({st.error or 'push pending'}); "
              "run `workboard sync`", file=sys.stderr)
        return 1
    print(f"review recorded on {detail[:8]}")
    return 0


def _rank_table(rows, width) -> list[str]:
    """Rank as scope · window · accepted · submitted · worked on (value and #rank/of); fits `width`."""
    from . import rank
    piv = rank.pivot(rows)
    cols = ["scope", "window", "accepted", "submitted", "worked_on"]
    heads = {"scope": "SCOPE", "window": "WINDOW", "accepted": "ACCEPTED", "submitted": "SUBMITTED",
             "worked_on": "WORKED ON"}
    widths = {c: min(30, max(len(heads[c]), *(len(str(r.get(c, ""))) for r in piv))) for c in cols}
    shown, used = [], 2
    for c in cols:
        need = widths[c] + (2 if shown else 0)
        if used + need > width:
            room = width - used - (2 if shown else 0)
            if not shown and room >= 6:          # first column always present, truncated to fit
                widths[c] = room
                shown.append(c)
            break
        shown.append(c)
        used += need
    out = ["  " + "  ".join(render.middle(heads[c], widths[c]).ljust(widths[c]) for c in shown)]
    out += ["  " + "  ".join(render.middle(str(r.get(c, "")), widths[c]).ljust(widths[c]) for c in shown) for r in piv]
    hidden = [heads[c] for c in cols if c not in shown]
    if hidden:
        note = f"({len(hidden)} column(s) hidden: {', '.join(hidden)} — widen the terminal or use --json)"
        out += ["  " + l for l in render.wrap(note, max(10, width - 2), "")]
    return [l if len(l) <= width else l[:width] for l in out]


def stats_data(snap, cfg, *, weeks, start=None, end=None, shown_to=None, quality=None, rank_data=None,
               per_repo=None) -> dict:
    from . import stats as st
    cohorts = None
    if quality:
        cohorts = [dict(c, week=c["week"].isoformat())
                   for c in st.first_pass_by_cohort(snap.observations, quality["rounds"], cfg, start, end)]
    return {"window": {"from": start.date().isoformat() if start else None,
                       "to": shown_to.isoformat() if shown_to else None,
                       "end_exclusive": end.isoformat() if end else None},
            "weekly": [dict(r, week=r["week"].isoformat())
                       for r in st.weekly(snap.observations, cfg, snap.now, weeks, start, end)],
            "week": st.week_numbers(snap.observations, cfg, snap.now),
            "range_totals": st.range_totals(snap.observations, snap.now, start, end) if (start or end) else None,
            "funnel": dict(st.funnel(snap.observations), scope="all-time snapshot"),
            "flow": st.cycle_and_wait(snap.observations, snap.now, start, end),
            "tasks_per_repo": per_repo, "pipeline_age": dict(st.pipeline_age(snap.views, snap.now), scope="now"),
            "quality": dict(quality, cohorts=cohorts) if quality else None,
            "rank": rank_data,
            "definitions": st.DEFINITIONS.format(tz=cfg.user.timezone),
            "sources": {k: {"ok": h.ok, "observed_at": h.observed_at.isoformat() if h.observed_at else None}
                        for k, h in snap.health.items()}}


def render_stats(snap, cfg, *, weeks, width, uni, quality=None, rank_data=None, start=None, end=None,
                 shown_to=None, per_repo=None) -> str:
    from . import stats as st
    rows = st.weekly(snap.observations, cfg, snap.now, weeks, start, end)
    n = st.week_numbers(snap.observations, cfg, snap.now)
    top = max([r["accepted"] for r in rows] + [1])
    barw = max(6, min(30, width - 62))
    ranged = bool(start or end)
    if ranged:
        span = (f"{start:%Y-%m-%d}" if start else "the beginning") + (f" to {shown_to:%Y-%m-%d}" if shown_to else " to now")
    else:
        span = f"last {len(rows)} weeks"
    out = [f"Weekly output — completions (accepted) vs arrivals (submitted), {span}",
           f"  {'week of':<11} {'accepted':<10} {'':<{barw}}  {'submitted':>9}  {'worked on':>9}"]
    for r in rows:
        acc = f"{r['accepted']} ({r['accepted_mt']}/{r['accepted_st']})"
        out.append(f"  {r['week']:%Y-%m-%d}  {acc:<10} {st.bar(r['accepted'], top, barw, uni):<{barw}}  "
                   f"{r['submitted']:>9}  {r['worked_on']:>9}")
    out.append(f"  accepted shown as total (multi-turn/single-turn) · trend {st.spark([r['accepted'] for r in rows], uni)}")
    if ranged:
        t = st.range_totals(snap.observations, snap.now, start, end)
        out.append(f"  in range: accepted {t['accepted']} · submitted {t['submitted']} · worked on {t['worked_on']}")
    else:
        out.append(f"  W{n['week']} so far {n['this_week']} · same point last week {n['same_point_last_week']} · "
                   f"4-week median {n['median_4wk']:g} · all-time accepted {n['total']}")
    flow = st.cycle_and_wait(snap.observations, snap.now, start, end)
    fmt = lambda v: "unavailable" if v is None else f"{v}h"
    out += ["", "Flow" + (" (decisions in range)" if ranged else ""),
            f"  cycle time (latest submit -> accepted) p50 {fmt(flow['cycle_p50_h'])} · p75 {fmt(flow['cycle_p75_h'])} "
            f"(coverage {flow['cycle_coverage']})",
            f"  reviewer wait (latest submit -> latest decision) p50 {fmt(flow['wait_p50_h'])} · "
            f"p75 {fmt(flow['wait_p75_h'])} (coverage {flow['wait_coverage']})"]
    f = st.funnel(snap.observations)
    out += ["", "Funnel (exact sources, all-time snapshot)",
            f"  built {f['built']} (task dirs in git) -> imported {f['imported']} -> submitted {f['submitted']} -> "
            f"accepted {f['accepted']}",
            f"  archived {f['archived']} ({f['archived_after_accept']} after acceptance) · open {f['open']}"]
    if per_repo is not None:
        if per_repo["available"]:
            top_repos = list(per_repo["by_repo"].items())[:8]
            out.append(f"  tasks per upstream repo (coverage {per_repo['coverage']}): " +
                       ", ".join(f"{k.split('/')[-1]} {v}" for k, v in top_repos))
        else:
            out.append(f"  tasks per upstream repo: unavailable ({per_repo['reason']}; coverage {per_repo['coverage']})")
    ages = st.pipeline_age(snap.views, snap.now)
    if ages:
        out += ["", "Pipeline age now (open tasks: count · median · max time in state)"]
        out += [f"  {k:<10} {v['count']:>3} · {v['median_h']:>6}h · {v['max_h']:>6}h" for k, v in ages.items()]
    if quality is not None:
        r = quality["rounds"]
        out += ["", f"Quality (human review history, coverage {quality['covered']}/{quality['eligible']} submitted tasks)",
                f"  tasks sent back at least once {sum(1 for x in r.values() if x)} · total revision rounds {sum(r.values())}"]
        for c in st.first_pass_by_cohort(snap.observations, r, cfg, start, end)[-len(rows):]:
            rate = "-" if c["rate"] is None else f"{c['rate']}%"
            out.append(f"  submitted week {c['week']:%Y-%m-%d}: {c['first_pass']}/{c['decided']} accepted first time ({rate})")
    if rank_data:
        out += ["", f"Rank (from {rank_data['source']}, fetched {rank_data['fetched_at'][:16]} UTC)"]
        out += _rank_table(rank_data["rows"], width)
    out.append("")
    out += render.wrap("Definitions: " + st.DEFINITIONS.format(tz=cfg.user.timezone), width, "  ")
    final = []
    for line in out:
        final += [line] if len(line) <= width else render.wrap(line, width, "    ")
    return "\n".join(final)


def _parse_day(text, tz, name):
    from datetime import date
    try:
        d = date.fromisoformat(text)
    except ValueError:
        raise SystemExit(f"--{name} takes a date like 2026-10-01")
    return datetime(d.year, d.month, d.day, tzinfo=tz)


def cmd_stats(args, cfg):
    from zoneinfo import ZoneInfo
    from . import app, rank, stats as st
    tz = ZoneInfo(cfg.user.timezone)
    start = _parse_day(args.from_, tz, "from") if args.from_ else None
    shown_to = _parse_day(args.to, tz, "to").date() if args.to else None
    end = _parse_day(args.to, tz, "to") + timedelta(days=1) if args.to else None   # --to inclusive; end exclusive
    if start and end and end <= start:
        raise SystemExit("--to must be on or after --from")
    if not 1 <= args.weeks <= 104:
        raise SystemExit("--weeks must be between 1 and 104")
    snap = _gather(args, cfg)
    quality = st.revision_rounds(cfg, snap.observations, app.cache_dir(), fetch=True) if args.quality else None
    per_repo = st.tasks_per_repo(cfg, [o.entity_id for o in snap.observations if o.source == "codimango"])
    rank_data = rank.load(app.cache_dir())
    if args.json:
        return _emit(args, snap, stats_data(snap, cfg, weeks=args.weeks, start=start, end=end, shown_to=shown_to,
                                            quality=quality, rank_data=rank_data, per_repo=per_repo))
    style = _style(args, cfg)
    return _emit(args, snap, human=render_stats(snap, cfg, weeks=args.weeks, width=_width(args), uni=style.unicode,
                                                quality=quality, rank_data=rank_data, start=start, end=end,
                                                shown_to=shown_to, per_repo=per_repo))


def cmd_rank(args, cfg):
    from . import app, rank
    cache = app.cache_dir()
    if args.action == "import":
        if not args.file:
            print("rank import needs a file", file=sys.stderr)
            return 2
        try:
            data = rank.import_file(Path(args.file), cache)
        except (OSError, ValueError) as exc:
            print(f"rank import failed: {exc}", file=sys.stderr)
            return 2
        print(f"imported {len(data['rows'])} rank rows")
        return 0
    data, why = (rank.refresh(cfg, cache) if args.refresh else (rank.load(cache), "cached"))
    if data is None and not args.refresh:
        data, why = rank.refresh(cfg, cache)
    if data is None:
        print(why, file=sys.stderr)
        cached = rank.load(cache)
        if not cached:
            return 1
        data = cached
        print("(showing the last cached result)", file=sys.stderr)
    if args.json:
        print(json.dumps(data))
        return 0
    print(render.middle(f"Rank from {data['source']} (fetched {data['fetched_at'][:16]} UTC)", _width(args)))
    print("\n".join(_rank_table(data["rows"], _width(args))))
    return 0


def cmd_import_claims(args, cfg):
    from . import coord, legacy, sync as s
    from .app import gather
    path = Path(args.path).expanduser()
    rows = legacy.parse_claims_md(path.read_text())
    snap = gather(cfg, do_sync=False)
    known = {v.entity_id for v in snap.views if v.fields.get("group") != "DONE"}
    live = legacy.live_rows(rows, known, snap.now, args.days)
    for r in live:
        print(f"  {r['task']:<50} {r['machine']:<12} {r['status']:<10} {r['updated']}")
    if args.dry_run:
        print(f"{len(live)} live row(s) would be imported (dry run)")
        return 0
    state = s.default_state_dir()
    actor = coord.actor_for(cfg)
    n = sum(coord.record(state, "note", r["task"], actor, {"legacy_owner": r["machine"], "status": r["status"],
                                                           "updated": r["updated"], "text": r["note"]}) for r in live)
    s.sync(cfg, state_dir=state)
    print(f"imported {n} legacy owner(s); they show as LEGACY until a real claim exists or 7 days pass")
    return 0


def cmd_setup(args, cfg):
    """Set up this server: config from the private ledger repo, hooks, cron sync, claim probe, first sync."""
    import shutil as sh
    from . import claims, config as cfgmod, gitutil, hooks, sync as s
    target = cfgmod.default_path()
    if not target.exists():
        if not args.ledger:
            print("no config yet: pass --ledger <private ledger git url> (it holds config/workboard.toml)", file=sys.stderr)
            return 2
        tmp = Path(tempfile.mkdtemp(prefix="wb-setup-"))
        p = gitutil.run(tmp, "clone", "-q", "--depth", "1", args.ledger, "ledger", timeout=120)
        src = tmp / "ledger" / "config" / "workboard.toml"
        if p.returncode != 0 or not src.exists():
            print(f"could not get config/workboard.toml from the ledger: {gitutil.err(p)}", file=sys.stderr)
            return 2
        target.parent.mkdir(parents=True, exist_ok=True)
        sh.copy(src, target)
        os.chmod(target, 0o600)
        sh.rmtree(tmp, ignore_errors=True)
        print(f"config installed at {target}")
    cfg = cfgmod.load_config()
    board = str(Path(__file__).resolve().parent.parent / "board")
    hooks.install(Path("~/.claude/settings.json").expanduser(), board)
    print("hooks installed (backup kept next to ~/.claude/settings.json)")
    if sh.which("crontab"):
        cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        lines = [l for l in cur.splitlines() if "tools/board/board sync" not in l]
        lines.append(f"*/2 * * * * {board} sync --quiet >/dev/null 2>&1")
        subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=False)
        print("cron: board sync every 2 minutes")
    state = s.default_state_dir()
    pr = claims.probe(cfg, state_dir=state)
    print(f"claim refs: {'ok (' + pr.prefix + ')' if pr.ok else 'DISABLED: ' + pr.detail}")
    st = s.sync(cfg, state_dir=state)
    print(f"ledger: pull {'ok' if st.last_pull_ok else 'FAILED'}, push {'ok' if st.last_push_ok else 'not ok'}"
          f"{(' — ' + st.error) if st.error else ''}")
    print(f"done. Try: {board}")
    return 0 if pr.ok and st.last_pull_ok else 1


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
    cl = sub.add_parser("claim", parents=[common], help="claim a task (atomic), or assign it with --to")
    cl.add_argument("task")
    cl.add_argument("--to", help="assign to the session whose tab title contains this text")
    cl.add_argument("--steal", action="store_true", help="take over an expired claim")
    stp = sub.add_parser("stats", parents=[common], help="weekly progress, funnel, pipeline age, quality, rank")
    stp.add_argument("--weeks", type=int, default=8)
    stp.add_argument("--from", dest="from_", help="first day, e.g. 2026-10-01 (your timezone)")
    stp.add_argument("--to", help="last day, inclusive")
    stp.add_argument("--quality", action="store_true", help="fetch human review history (cached) for revision stats")
    rk = sub.add_parser("rank", parents=[common], help="your rank on track/team/org (saved DaiQuery query)")
    rk.add_argument("action", choices=["show", "import"], nargs="?", default="show")
    rk.add_argument("file", nargs="?")
    ck = sub.add_parser("check", help="run the pre-submit gate and record its result")
    ck.add_argument("action", choices=["run"])
    ck.add_argument("task")
    rv = sub.add_parser("review", parents=[common], help="add or list agent-session reviews")
    rv.add_argument("action", choices=["add", "list"])
    rv.add_argument("task")
    rv.add_argument("--verdict", choices=["ready", "changes", "comment"])
    rv.add_argument("--confidence", type=int, choices=range(1, 6), metavar="1-5")
    rv.add_argument("--note", default="")
    ic = sub.add_parser("import-claims", help="one-time: import live CLAIMS.md rows as advisory legacy owners")
    ic.add_argument("--path", default="~/swebench-playbook/ledger/CLAIMS.md")
    ic.add_argument("--days", type=int, default=7)
    ic.add_argument("--dry-run", action="store_true")
    su = sub.add_parser("setup", help="set up this server (config from ledger, hooks, cron, probe, first sync)")
    su.add_argument("--ledger", help="private ledger git url holding config/workboard.toml")
    hk = sub.add_parser("hook", help="(internal) Claude Code hook entry point")
    hk.add_argument("kind", choices=["session-start", "pre-tool", "post-tool"])
    sy = sub.add_parser("sync", parents=[common], help="push queued events and refresh claim data")
    sy.add_argument("--quiet", action="store_true")
    ih = sub.add_parser("install-hooks", help="add workboard hooks to Claude Code settings (hooks only)")
    ih.add_argument("--settings", default="~/.claude/settings.json")
    ih.add_argument("--dry-run", action="store_true")
    ih.add_argument("--uninstall", action="store_true")
    rl = sub.add_parser("release", parents=[common], help="give a task up")
    rl.add_argument("task")
    rl.add_argument("--reason", required=True)
    cf = sub.add_parser("config", parents=[common], help="show or validate config")
    cf.add_argument("action", choices=["show", "validate"], nargs="?", default="show")
    pl = sub.add_parser("plugins", parents=[common], help="list loaded plugins")
    pl.add_argument("action", choices=["list", "doctor"], nargs="?", default="list")
    return p


COMMANDS = {"list": cmd_list, "show": cmd_show, "explain": cmd_explain, "available": cmd_available,
            "changes": cmd_changes, "status": cmd_status, "legend": cmd_legend, "config": cmd_config,
            "plugins": cmd_plugins, "claim": cmd_claim, "release": cmd_release, "hook": cmd_hook,
            "sync": cmd_sync, "install-hooks": cmd_install_hooks, "check": cmd_check, "review": cmd_review,
            "stats": cmd_stats, "rank": cmd_rank, "import-claims": cmd_import_claims, "setup": cmd_setup}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-") and argv[0] not in ("-h", "--help", "--version"):
        argv = ["list", *argv]
    if argv[:1] == ["hook"]:
        try:
            args = build_parser().parse_args(argv)
            cfg = load_config()
        except BaseException:
            return 0                                   # hooks fail open, even on bad args/config
        _CFG[0] = cfg
        return cmd_hook(args, cfg)
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
