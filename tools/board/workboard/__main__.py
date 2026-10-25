"""workboard CLI. `workboard` (or the `board` shim) with no command shows the list."""
from __future__ import annotations

import argparse
import json
import time
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


def app_cache():
    from .app import cache_dir
    return cache_dir()


def _pretty(args, cfg) -> bool:
    if getattr(args, "classic", False) or args.plain or cfg.ui.style != "pretty":
        return False
    st = _style(args, cfg)
    return st.color and st.unicode and getattr(args, "group", "attention") == "attention" and not getattr(args, "wide", False)


def cmd_watch(args, cfg):
    from . import app_ui, sync as s
    from .app import gather
    if not (sys.stdout.isatty() and sys.stdin.isatty()):
        print("board ui needs an interactive terminal; use `board` for a one-off view", file=sys.stderr)
        return 2
    return app_ui.run(lambda: gather(cfg), cfg, interval=args.interval, host_tag=s.safe_host(s.host_id_for(cfg)))


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
        views = [v for v in views if v.fields.get("owner", "").startswith(me) or
                 (v.fields.get("availability") or {}).get(
                     "state", "available" if v.fields.get("claim_health") in ("FREE", "EXPIRED") else "") == "available"]
    if args.json:
        print(json.dumps(_envelope(snap, [_view_json(v) for v in views]), default=str, indent=1))
    elif _pretty(args, cfg):
        from . import tui
        try:
            prev = json.loads((app_cache() / LAST_LOOK).read_text())["tasks"]
        except (OSError, ValueError, KeyError):
            prev = None
        snap.views = views
        print(tui.render(snap, cfg, width=_width(args), changed=tui._changed_since(prev, snap), show_all=args.all))
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
    from . import tui
    links = f.get("links") or {}
    lines = [style.paint(tui.link(v.entity_id, links.get("codimango") or links.get("github")) if style.color else v.entity_id, "bold"),
             f"  NEXT     {f['next']}   ({f['group']})",
             f"  state    {f['state']} for {render.fmt_age(f.get('state_age_s'))}   validation {f['valid']}   sync {f['sync']}",
             f"  owner    {f.get('owner') or '-'} [{f.get('claim_health')}]",
             f"  agent review {f['review']}  confidence {f.get('confidence') or '-'}"
             f"{' (older commit)' if f.get('confidence_stale') else ''}  dissent {f.get('dissent', 0)}",
             f"  check    {f['check']}{' (older commit)' if f.get('check_stale') else ''}",
             f"  commits  {f.get('pushes_before_submit', 0)} before submit, {f.get('pushes_after_submit', 0)} after"]
    for k, lbl in (("codimango", "codimango"), ("github", "github"), ("latest", "latest")):
        if links.get(k):
            lines.append(f"  {lbl:<8} {links[k]}")
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
            if v.fields.get("group") != "DONE" and
            (v.fields.get("availability") or {}).get(
                "state", "available" if v.fields.get("claim_health") in ("FREE", "EXPIRED") else "") == "available"]
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
    want = {ev: entry["hooks"][0]["command"] for ev, (entry,) in hk._plan(board_path()).items()}
    try:
        data = json.loads(settings.read_text())
        hooks_cfg = data.get("hooks", {}) if isinstance(data, dict) else {}
        installed = {ev for ev, cmd in want.items()
                     if any(isinstance(h, dict) and h.get("command") == cmd
                            for e in (hooks_cfg.get(ev) or []) if isinstance(e, dict) for h in e.get("hooks", []))}
        detail = ""
    except (OSError, ValueError) as exc:
        installed, detail = set(), f"settings unreadable: {exc.__class__.__name__}"
    need = {"SessionStart", "PreToolUse", "PostToolUse"}
    out.append({"name": "Claude hooks installed", "ok": need <= installed,
                "detail": detail or ("missing: " + ", ".join(sorted(need - installed)) if need - installed else "all three")})
    cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout if shutil.which("crontab") else ""
    expected = cron_line(board_path())
    good = [l for l in cron.splitlines() if l.strip() == expected]
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
    st = s.sync(cfg, state_dir=state)
    audit_ok = "audit event could not be queued" not in res.detail and st.last_push_ok and not st.pending
    if args.json:
        print(json.dumps(dict(asdict(res), audit_recorded=audit_ok)))
    elif res.status == "ACQUIRED":
        print(f"claimed {task} for {(to_actor or res.owner).get('alias')}")
        if not audit_ok:
            print("warning: the claim is held, but its audit event is not in the ledger yet "
                  f"({st.error or 'queued locally'}); run `workboard sync`", file=sys.stderr)
            return 3
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
    st = s.sync(cfg, state_dir=state)
    audit_ok = "audit event could not be queued" not in res.detail and st.last_push_ok and not st.pending
    if args.json:
        print(json.dumps(dict(asdict(res), audit_recorded=audit_ok)))
    else:
        print(f"{res.status}: {args.task} {res.detail}")
    if res.status == "RELEASED" and not audit_ok:
        print("warning: released, but the audit event is not in the ledger yet; run `workboard sync`", file=sys.stderr)
        return 3
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
        dbg = s.default_state_dir() / "hook-debug.log"         # opt-in diagnostics: `touch` this file to enable
        if dbg.exists() and dbg.stat().st_size < 2_000_000:
            with open(dbg, "a") as fh:
                sid = data.get("session_id", "?") if isinstance(data, dict) else "?"
                fh.write(f"{time.strftime('%H:%M:%S')} {args.kind} {str(sid)[:8]} "
                         f"{(data or {}).get('tool_name', '') if isinstance(data, dict) else ''} "
                         f"delivered={'additionalContext' in (res.stdout or '')}\n")
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        if res.stdout:
            print(res.stdout)
        return res.code
    except Exception:
        return 0


def cmd_sync(args, cfg):
    from . import app, presence, sync as s
    from .completion import task_names
    host, known = s.safe_host(s.host_id_for(cfg)), set(task_names())
    try:
        presence.emit(cfg, s.default_state_dir(), host, known)
    except Exception as exc:                       # presence is best-effort; never block the sync
        print(f"presence scan skipped: {exc}", file=sys.stderr)
    try:
        from . import claims_md_sync
        claims_md_sync.sync(cfg, s.default_state_dir(), host, known)
    except Exception as exc:
        print(f"CLAIMS.md sync skipped: {exc}", file=sys.stderr)
    try:
        from .sources.codimango import CodimangoSource
        from .sources.gitsrc import GitSource
        CodimangoSource(cfg, cache_dir=app.cache_dir()).fetch(max_age_seconds=cfg.codimango.cache_ttl_seconds)
        stamp = app.cache_dir() / app.GIT_STAMP
        if cfg.repositories and (not stamp.exists() or time.time() - stamp.stat().st_mtime > cfg.codimango.cache_ttl_seconds):
            if GitSource(cfg).fetch().health.ok:
                stamp.touch()
    except Exception as exc:                       # cache warming is best-effort
        print(f"cache refresh skipped: {exc}", file=sys.stderr)
    try:
        from . import reviews
        from .sources.codimango import CodimangoSource as _CS
        rows = (_CS(cfg, cache_dir=app.cache_dir())._read_cache() or {}).get("rows", [])
        reviews.refresh(cfg, app.cache_dir(), [(r["name"], r.get("updated_at") or "") for r in rows
                                               if r.get("entered_pool_at") and r.get("status") != "archived"])
    except Exception as exc:
        print(f"review history refresh skipped: {exc}", file=sys.stderr)
    hb = s.default_state_dir() / "heartbeat-at"
    if not hb.exists() or time.time() - hb.stat().st_mtime > 600:      # prove this host syncs, at most every 10 min
        from . import coord as _c, events as _e
        if _e.spool_append(s.default_state_dir(), _e.new_event("heartbeat", None, {"host": host},
                                                               actor=dict(_c.actor_for(cfg), kind="human"),
                                                               commit=None, source="sync")):
            hb.touch()
    try:
        from . import events as ev_mod, host_snapshots, session_inventory
        current_events, _ = ev_mod.read_events(app.ledger_event_files(cfg))
        native, diagnostic = session_inventory.discover(cfg, current_events, host, now=time.time())
        host_snapshots.cache_local(s.default_state_dir(), host, [row for row in native if not row.get("remote")],
                                   [row for row in diagnostic if row.get("host") == host],
                                   at=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        print(f"session snapshot skipped: {exc}", file=sys.stderr)
    st = s.sync(cfg, state_dir=s.default_state_dir())
    app.refresh_claims_cache(cfg, s.default_state_dir())
    try:
        from . import comms, events as ev_mod
        evs, _ = ev_mod.read_events(app.ledger_event_files(cfg))
        comms.write_inbox_cache(s.default_state_dir(), evs + app.pending_spool_events(s.default_state_dir(), host))
    except Exception as exc:
        print(f"inbox cache skipped: {exc}", file=sys.stderr)
    if not args.quiet:
        print(json.dumps(asdict(st)) if args.json else
              f"ledger: pull {'ok' if st.last_pull_ok else 'FAILED'}, push {'ok' if st.last_push_ok else 'not ok'}, "
              f"{st.pending} pending {('— ' + st.error) if st.error else ''}")
    return 0 if (st.last_pull_ok and (st.last_push_ok or not st.pending)) else 1


def cmd_install_hooks(args, cfg):
    from . import hooks
    settings = Path(args.settings).expanduser()
    board = board_path()
    if args.uninstall:
        hooks.uninstall(settings)
        print(f"removed workboard hooks from {settings} (backup kept next to it)")
        return 0
    text = hooks.install(settings, board, dry_run=args.dry_run)
    if args.dry_run:
        print(text)
        return 0
    print(f"installed workboard hooks into {settings} (backup kept next to it; only hook entries changed)")
    line = cron_line(board)
    print("To keep claim data fresh (needed for edit-blocking), add this cron line (crontab -e):")
    print(f"  {line}")
    return 0


def cmd_check(args, cfg):
    from . import checks, sync as s
    from .completion import task_names
    state = s.default_state_dir()
    if args.action != "record" and (args.commit or args.source != "manual"):
        print("check: --commit only applies to `check record`", file=sys.stderr)
        return 2
    if args.action == "run":
        code = checks.run_check(cfg, args.target, state_dir=state, role=args.role)
    elif args.action == "record":
        ok, detail = checks.record_check(cfg, args.target, passed=args.passed, warn=args.warn, fail=args.fail,
                                         summary=args.summary or "", state_dir=state, role=args.role,
                                         commit=args.commit, source=args.source)
        print(f"recorded on {detail[:8]}" if ok else f"not recorded: {detail}")
        code = 0 if ok else 2
    else:
        known = set(task_names())
        for task, result in checks.import_dir(cfg, Path(args.target), state_dir=state, known=known or None, role=args.role):
            print(f"  {task:<50} {result}")
        code = 0
    st = s.sync(cfg, state_dir=state, timeout_seconds=15)
    if args.action != "run" and not (st.last_push_ok and not st.pending):
        print("results queued locally; run `workboard sync` to publish them", file=sys.stderr)
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
    ok, detail = checks.add_review(cfg, args.task, args.verdict, args.confidence, args.note or "", state_dir=state,
                                   role=args.role)
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
            "current_week": dict(st.week_numbers(snap.observations, cfg, snap.now), scope="current week, not ranged"),
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
            f"  first-submission cycle time: unavailable ({flow['first_submission_cycle']['reason']})",
            f"  latest-round cycle (latest submit -> accepted) p50 {fmt(flow['latest_round_cycle_p50_h'])} · "
            f"p75 {fmt(flow['latest_round_cycle_p75_h'])} (coverage {flow['latest_round_cycle_coverage']})",
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
    if _pretty(args, cfg):
        from . import tui
        print(tui.render_stats(snap, cfg, width=_width(args), weeks=args.weeks, start=start, end=end,
                               rank_data=rank_data, per_repo=per_repo, quality=quality))
        return 1 if args.strict and _unhealthy(snap) else 0
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
    if not 1 <= args.days <= 90:
        raise SystemExit("--days must be between 1 and 90")
    source = args.path or cfg.legacy.claims_md
    if not source:
        raise SystemExit("pass --path <CLAIMS.md> or set [legacy] claims_md in your config")
    path = Path(source).expanduser()
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
    fresh, why = coord.ledger_fresh(cfg, state)
    if not fresh:
        print(f"refusing to import: ledger did not sync ({why})", file=sys.stderr)
        return 2
    actor = coord.actor_for(cfg)
    expires = (snap.now + timedelta(days=args.days)).isoformat(timespec="seconds")
    n = sum(coord.record(state, "note", r["task"], actor, {"legacy_owner": r["machine"], "status": r["status"],
                                                           "updated": r["updated"], "text": r["note"],
                                                           "expires_at": expires}) for r in live)
    st = s.sync(cfg, state_dir=state)
    if n < len(live) or not (st.last_push_ok and not st.pending):
        print(f"imported {n}/{len(live)}, but not all are in the ledger yet ({st.error or 'queued'}); run `workboard sync`",
              file=sys.stderr)
        return 1
    print(f"imported {n} legacy owner(s); they show as LEGACY until a real claim exists or {args.days} days pass")
    return 0


def board_path() -> str:
    return str(Path(__file__).resolve().parent.parent / "board")


def cron_line(board: str) -> str:
    return f"*/2 * * * * {board} sync --quiet >/dev/null 2>&1"


def cmd_setup(args, cfg):
    """Set up this machine: config (from the private ledger if missing), `board` on PATH, the skill, hooks,
    a 2-minute cron sync, a claim-ref probe and a first sync. Fails if any required step fails."""
    import shutil as sh
    from . import claims, config as cfgmod, gitutil, hooks, sync as s
    problems = []
    target = cfgmod.default_path()
    if not target.exists():
        if not args.ledger:
            print("no config yet: pass --ledger <private ledger git url> (it holds config/workboard.toml)", file=sys.stderr)
            return 2
        with tempfile.TemporaryDirectory(prefix="wb-setup-") as tmp:
            p = gitutil.run(tmp, "clone", "-q", "--depth", "1", args.ledger, "ledger", timeout=120)
            src = Path(tmp) / "ledger" / "config" / "workboard.toml"
            if p.returncode != 0 or not src.exists():
                print(f"could not get config/workboard.toml from the ledger: {gitutil.err(p)}", file=sys.stderr)
                return 2
            target.parent.mkdir(parents=True, exist_ok=True)
            sh.copy(src, target)
            os.chmod(target, 0o600)
        print(f"config installed at {target}")
    try:
        cfg = cfgmod.load_config()
    except ValueError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    board = board_path()
    def link(dest: Path, src: Path, what: str):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.is_symlink():
                target = Path(os.readlink(dest))
                if not target.is_absolute():
                    target = dest.parent / target
                if os.path.realpath(target) == os.path.realpath(src):
                    return
                problems.append(f"{what}: {dest} links somewhere else ({os.readlink(dest)}); remove it and re-run setup")
                return
            elif dest.exists():
                problems.append(f"{what}: {dest} exists and is not our link; remove it and re-run setup")
                return
            dest.symlink_to(src)
            print(f"{what} installed at {dest}")
        except OSError as exc:
            problems.append(f"{what}: {exc}")

    link(Path("~/.local/bin/board").expanduser(), Path(board), "`board` command (needs ~/.local/bin on PATH)")
    link(Path("~/.claude/skills/workboard/SKILL.md").expanduser(), Path(board).parent / "skill" / "SKILL.md", "skill")
    link(Path("~/.claude/commands/board.md").expanduser(), Path(board).parent / "skill" / "board-command.md",
         "/board slash command")
    try:
        from . import completion
        comp_dir = Path("~/.local/share/workboard").expanduser()
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "completion.bash").write_text(completion.BASH)
        (comp_dir / "completion.zsh").write_text(completion.ZSH)
        for rc, f in (("~/.bashrc", "completion.bash"), ("~/.zshrc", "completion.zsh")):
            rcp = Path(rc).expanduser()
            if rc.endswith("zshrc") and not rcp.exists():
                continue
            line = f'[ -f "$HOME/.local/share/workboard/{f}" ] && . "$HOME/.local/share/workboard/{f}"  # workboard'
            text = rcp.read_text() if rcp.exists() else ""
            if "# workboard" not in text:
                with open(rcp, "a") as fh:
                    fh.write(("\n" if text and not text.endswith("\n") else "") + line + "\n")
        print("tab completion installed (open a new shell, or: source ~/.bashrc)")
    except OSError as exc:
        problems.append(f"completion: {exc}")
    try:
        hooks.install(Path("~/.claude/settings.json").expanduser(), board)
        print("hooks installed (backup kept next to ~/.claude/settings.json)")
    except (OSError, ValueError) as exc:
        problems.append(f"hooks: {exc}")
    if sh.which("crontab"):
        cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        managed = re.compile(r"^\*/2 \* \* \* \* \S*/tools/board/board sync --quiet >/dev/null 2>&1$")
        lines = [l for l in cur.splitlines() if not managed.match(l.strip())]
        lines.append(cron_line(board))
        r = subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, capture_output=True)
        if r.returncode != 0:
            problems.append(f"cron: {r.stderr.strip() or 'crontab failed'}")
        else:
            print("cron: board sync every 2 minutes")
    else:
        problems.append("cron: crontab not available (claim data for edit-blocking will go stale)")
    state = s.default_state_dir()
    pr = claims.probe(cfg, state_dir=state)
    print(f"claim refs: {'ok (' + pr.prefix + ')' if pr.ok else 'DISABLED: ' + pr.detail}")
    if not pr.ok:
        problems.append("claim refs probe failed")
    st = s.sync(cfg, state_dir=state)
    print(f"ledger: pull {'ok' if st.last_pull_ok else 'FAILED'}, push {'ok' if st.last_push_ok else 'not ok'}"
          f"{(' — ' + st.error) if st.error else ''}")
    if not (st.last_pull_ok and (st.last_push_ok or not st.pending)):
        problems.append("first ledger sync did not complete")
    if problems:
        print("setup incomplete:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print("done. Try: board")
    return 0


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
    lp.add_argument("--classic", action="store_true", help="compact word-based table instead of the pretty view")
    wt = sub.add_parser("ui", aliases=["watch"], parents=[common],
                        help="interactive live board: tabs, filters, search, details (? for keys)")
    wt.add_argument("--interval", type=int, default=120, help="seconds between refreshes")
    hp = sub.add_parser("here", parents=[common], help="check in: claim/renew the tasks this session works on (or --idle)")
    hp.add_argument("tasks", nargs="*")
    hp.add_argument("--idle", action="store_true", help="not working on any task right now")
    hp.add_argument("--note", default="", help="one line about what you are doing")
    rcp = sub.add_parser("rollcall", parents=[common], help="ask every session to check in (`board here`)")
    rcp.add_argument("--server", help="only sessions on this server")
    mp = sub.add_parser("msg", parents=[common], help="message a session, a server, or all (delivered into sessions)")
    mp.add_argument("to", help="'all', a server id, or part of a session's tab title")
    mp.add_argument("text", nargs="+")
    mp.add_argument("--task", help="what the message is about")
    mp.add_argument("--reply-to", help="message id this answers")
    ib = sub.add_parser("inbox", parents=[common], help="messages for this session/server")
    ib.add_argument("--all", action="store_true", help="include acknowledged ones")
    ak = sub.add_parser("ack", parents=[common], help="mark a message (id prefix) or 'all' as handled")
    ak.add_argument("id")
    fd = sub.add_parser("feed", parents=[common], help="servers, sessions and activity across both servers")
    fd.add_argument("--hours", default="12")
    fd.add_argument("--limit", type=int, default=60)
    cr = sub.add_parser("courier", parents=[common], help="wait for messages a courier session should deliver")
    cr.add_argument("--timeout", type=float, default=3600, help="seconds to wait (0 checks once)")
    cr.add_argument("--limit", type=int, default=20)
    cw = sub.add_parser("courier-wait", parents=[common], help="block without model tokens until courier work exists")
    cw.add_argument("--timeout", type=float, default=3600, help="seconds to wait (0 checks once)")
    cw.add_argument("--limit", type=int, default=20)
    rc = sub.add_parser("receipt", parents=[common], help="record courier delivery for one message recipient")
    rc.add_argument("message", help="message id or unique prefix")
    rc.add_argument("recipient", help="stable session target from courier-wait")
    rc.add_argument("state", choices=["delivered", "failed"])
    rc.add_argument("--reason", default="")
    rc.add_argument("--transport", default="courier", choices=["courier", "hook"])
    hp = sub.add_parser("html", parents=[common], help="write a self-contained HTML dashboard")
    hp.add_argument("--out", default="~/.cache/workboard/board.html")
    sv = sub.add_parser("serve", help="serve the live HTML dashboard on localhost")
    sv.add_argument("--port", type=int, default=8765)
    sv.add_argument("--interval", type=int, default=30, help="seconds between refreshes (each one pulls the shared ledger)")
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
    stp.add_argument("--classic", action="store_true", help="plain sections with full definitions")
    rk = sub.add_parser("rank", parents=[common], help="your rank on track/team/org (saved DaiQuery query)")
    rk.add_argument("action", choices=["show", "import"], nargs="?", default="show")
    rk.add_argument("file", nargs="?")
    ck = sub.add_parser("check", help="run the pre-submit gate and record its result")
    ck.add_argument("action", choices=["run", "record", "import"])
    ck.add_argument("target", help="task name (run/record) or a directory of <task>.txt outputs (import)")
    ck.add_argument("--pass", dest="passed", type=int, default=0)
    ck.add_argument("--warn", type=int, default=0)
    ck.add_argument("--fail", type=int, default=0)
    ck.add_argument("--summary", default="")
    ck.add_argument("--role", choices=["author", "independent"],
                    help="author = the session building the task; independent = a fresh agent without that context")
    ck.add_argument("--commit", help="commit the result is for (default: the task's latest commit)")
    ck.add_argument("--source", default="manual", help=argparse.SUPPRESS)
    rv = sub.add_parser("review", parents=[common], help="add or list agent-session reviews")
    rv.add_argument("action", choices=["add", "list"])
    rv.add_argument("task")
    rv.add_argument("--verdict", choices=["ready", "changes", "comment"])
    rv.add_argument("--confidence", type=int, choices=range(1, 6), metavar="1-5")
    rv.add_argument("--note", default="")
    rv.add_argument("--role", choices=["author", "independent"],
                    help="author = the session building the task; independent = a fresh agent without that context")
    ic = sub.add_parser("import-claims", help="one-time: import live CLAIMS.md rows as advisory legacy owners")
    ic.add_argument("--path", help="CLAIMS.md to import (default: [legacy] claims_md in config)")
    ic.add_argument("--days", type=int, default=7)
    ic.add_argument("--dry-run", action="store_true")
    su = sub.add_parser("setup", help="set up this server (config from ledger, hooks, cron, probe, first sync)")
    su.add_argument("--ledger", help="private ledger git url holding config/workboard.toml")
    cp = sub.add_parser("completion", help="print shell completion script (bash or zsh)")
    cp.add_argument("shell", choices=["bash", "zsh"], nargs="?", default="bash")
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


def cmd_completion(args, cfg):
    from . import completion
    print(completion.ZSH if args.shell == "zsh" else completion.BASH, end="")
    return 0


def cmd_html(args, cfg):
    from . import html
    snap = _gather(args, cfg)
    path = html.write(snap, cfg, Path(args.out))
    print(f"wrote {path}  (open it in a browser; for a live page use: board serve)")
    return 0


def cmd_serve(args, cfg):
    from . import html
    from .app import gather
    def fresh():
        from . import sync as s
        try:                                   # pull other servers' claims / checks / reviews / messages now, not at next cron
            s.sync(cfg, state_dir=s.default_state_dir(), timeout_seconds=15)
        except Exception:
            pass
        return gather(cfg, do_sync=False)
    cfg.codimango.cache_ttl_seconds = min(cfg.codimango.cache_ttl_seconds, 60)   # the page should never lag

    def send(to, text, task):
        from . import comms, coord, events as ev_mod, sync as s
        if not text.strip():
            raise ValueError("empty message")
        snap = gather(cfg, do_sync=False)
        target = comms.target_for(to, ev_mod.latest_aliases(snap.events), [sv.id for sv in cfg.servers],
                                  views=snap.views, sessions=getattr(snap, "sessions", []))
        actor = dict(coord.actor_for(cfg), alias=f"{s.safe_host(s.host_id_for(cfg))}·dashboard", kind="human")
        if not ev_mod.spool_append(s.default_state_dir(), comms.new_message(text, target, actor, task=task)):
            raise ValueError("could not queue the message")
        st = s.sync(cfg, state_dir=s.default_state_dir(), timeout_seconds=20)
        return {"to": target["to_label"], "state": "published" if st.last_push_ok and not st.pending else "queued",
                "synced": bool(st.last_push_ok and not st.pending)}
    srv = html.serve(fresh, cfg, port=args.port, interval=args.interval, send_fn=send)
    print(f"🧭 workboard live at http://localhost:{args.port}/  (VS Code forwards the port; Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def _snap_for_comms(args, cfg):
    from .app import gather
    return gather(cfg, do_sync=not getattr(args, "no_sync", False))


def cmd_msg(args, cfg):
    from . import comms, coord, events as ev_mod, sync as s
    state = s.default_state_dir()
    snap = _snap_for_comms(args, cfg)
    try:
        target = comms.target_for(args.to, ev_mod.latest_aliases(snap.events), [sv.id for sv in cfg.servers],
                                  views=snap.views, sessions=getattr(snap, "sessions", []))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    ev = comms.new_message(" ".join(args.text), target, coord.actor_for(cfg), task=args.task, reply_to=args.reply_to)
    if not ev_mod.spool_append(state, ev):
        print("could not queue the message", file=sys.stderr)
        return 2
    st = s.sync(cfg, state_dir=state, timeout_seconds=20)
    ok = st.last_push_ok and not st.pending
    print(f"💬 published for {target['to_label']} — waiting for courier/hook delivery"
          if ok else f"💬 queued for {target['to_label']} (publishes on the next sync)")
    return 0 if ok else 3


ROLLCALL = ("📋 roll call from the workboard: run `board here <task> [<task> ...]` with the tasks you are working on "
            "(or `board here --idle` if none), check that `board here` then lists them, and `board ack` this message.")


def cmd_here(args, cfg):
    """A session checks in: claims (or renews) the tasks it is working on and says working / idle."""
    import re as _re
    from . import claims as cl, coord, events as ev_mod, sync as s
    state = s.default_state_dir()
    me = coord.actor_for(cfg)
    snap = _gather(args, cfg)
    if not args.tasks and not args.idle:
        mine = [v for v in snap.views if v.fields.get("owner_session") == me["session_id"]]
        last = next((e for e in reversed(snap.events) if e["type"] == "checkin"
                     and e["actor"].get("session_id") == me["session_id"]), None)
        print(f"🧭 {me['alias']}")
        print("  owns: " + (", ".join(v.entity_id for v in mine) or "nothing"))
        print("  last check-in: " + (f"{last['occurred_at'][:16]} · {last['payload'].get('status')} · "
                                     f"{', '.join(last['payload'].get('tasks') or []) or '—'}" if last else "never"))
        print("  check in: board here <task> [<task> ...]   ·   nothing to do: board here --idle")
        return 0
    ok, err = coord.ledger_fresh(cfg, state)
    if not ok:
        print(f"refusing to check in: ledger did not sync ({err})", file=sys.stderr)
        return 2
    tasks, lines, others = [], [], {}
    for name in args.tasks:
        exact = [v.entity_id for v in snap.views if v.entity_id == name]
        near = [v.entity_id for v in snap.views if name in v.entity_id]
        task = exact[0] if exact else near[0] if len(near) == 1 else name
        if not exact and len(near) != 1 and not _re.fullmatch(r"[a-z0-9][a-z0-9._-]{5,140}", name):
            lines.append(f"  ✘ {name}: no such task ({len(near)} partial matches)")
            continue
        tasks.append(task)
        res = coord.claim(cfg, task, state_dir=state)
        if res.status == "ACQUIRED":
            lines.append(f"  👤 {task}: claimed")
        elif res.status == "LOST" and (res.owner or {}).get("session_id") == me["session_id"]:
            hb = cl.heartbeat(cfg, task, me, expected_oid=res.oid, state_dir=state)
            lines.append(f"  ✓ {task}: already yours" + ("" if hb.status in ("RENEWED", "ACQUIRED") else f" ({hb.status})"))
        elif res.status == "LOST":
            others[task] = (res.owner or {}).get("alias", "?")
            lines.append(f"  ⚠ {task}: owned by {others[task]} — coordinate with `board msg`")
        else:
            lines.append(f"  … {task}: {res.status} {res.detail}")
    payload = {"tasks": tasks, "status": "idle" if args.idle else "working"}
    if args.note:
        payload["note"] = args.note[:300]
    if others:
        payload["owned_by_others"] = others
    ev_mod.spool_append(state, ev_mod.new_event("checkin", None, payload, actor=me, commit=None, source="checkin"))
    for task in tasks:                                   # counts as activity on each task (owner shows as working)
        ev_mod.spool_append(state, ev_mod.new_event("presence", task, {"last_seen": time.time(), "checkin": True},
                                                    actor=me, commit=None, source="checkin"))
    st = s.sync(cfg, state_dir=state, timeout_seconds=20)
    print(f"🧭 {me['alias']} checked in — {'idle 💤' if args.idle else 'working on ' + str(len(tasks)) + ' task(s)'}"
          + ("" if st.last_push_ok and not st.pending else " (queued; publishes on next sync)"))
    for line in lines:
        print(line)
    return 0


def cmd_rollcall(args, cfg):
    """Ask every session (or one server's) to check in; they see it at their next step."""
    from . import comms, coord, events as ev_mod, sync as s
    state = s.default_state_dir()
    target = {"to": f"host:{args.server}", "to_label": f"server {args.server}"} if args.server else \
        {"to": "all", "to_label": "everyone"}
    if not ev_mod.spool_append(state, comms.new_message(ROLLCALL, target, coord.actor_for(cfg))):
        print("could not queue the roll call", file=sys.stderr)
        return 2
    st = s.sync(cfg, state_dir=state, timeout_seconds=20)
    print(f"📋 roll call sent to {target['to_label']}" + ("" if st.last_push_ok else " (queued)") +
          " — sessions answer at their next step; idle ones when you next use them. Watch the Team tab.")
    return 0


def cmd_inbox(args, cfg):
    from . import comms, coord, render as r, sync as s
    snap = _snap_for_comms(args, cfg)
    me = coord.actor_for(cfg)
    msgs = comms.inbox(snap.events, me["session_id"], s.safe_host(s.host_id_for(cfg)), include_acked=args.all)
    if args.json:
        print(json.dumps(msgs))
        return 0
    if not msgs:
        print("📭 no messages for you")
        return 0
    for m in msgs:
        mark = "✓" if me["session_id"] in m["acked_by"] else "•"
        about = f" [{m['task']}]" if m["task"] else ""
        print(f"{mark} {m['id'][:8]}  {m['at'][:16]}  {m['from']} → {m['to_label']}{about}\n    {m['text']}")
    return 0


def cmd_ack(args, cfg):
    from . import comms, coord, events as ev_mod, sync as s
    state = s.default_state_dir()
    snap = _snap_for_comms(args, cfg)
    me = coord.actor_for(cfg)
    msgs = comms.inbox(snap.events, me["session_id"], s.safe_host(s.host_id_for(cfg)))
    pick = msgs if args.id == "all" else [m for m in msgs if m["id"].startswith(args.id)]
    for m in pick:
        ev_mod.spool_append(state, comms.ack_event(m["id"], me))
    s.sync(cfg, state_dir=state, timeout_seconds=15)
    print(f"acked {len(pick)} message(s)")
    return 0 if pick else 1


def _courier_data(cfg):
    """Read only the private ledger, local spool, and Claude registry; no Codimango/Git scan."""
    from . import app as app_mod, comms, events as ev_mod, sync as s
    from .sources import claude_sessions
    host = s.safe_host(s.host_id_for(cfg))
    evs, _ = ev_mod.read_events(app_mod.ledger_event_files(cfg))
    known = {e["event_id"] for e in evs}
    evs += [e for e in app_mod.pending_spool_events(s.default_state_dir(), host) if e["event_id"] not in known]
    sessions, _ = claude_sessions.discover(host)
    return evs, sessions, host, comms.courier_jobs(evs, sessions, host)


def _courier_fingerprint(cfg):
    from . import app as app_mod, sync as s
    from .sources.claude_sessions import REGISTRY
    paths = app_mod.ledger_event_files(cfg) + [s.default_state_dir() / "spool.jsonl"]
    try:
        paths += list(REGISTRY.glob("*.json"))
    except OSError:
        pass
    out = []
    for path in paths:
        try:
            st = path.stat()
            out.append((str(path), st.st_mtime_ns, st.st_size))
        except OSError:
            continue
    return tuple(out)


def cmd_courier_wait(args, cfg):
    """Block in ordinary Python (zero model turns) until a courier has useful work."""
    if not getattr(args, "no_sync", False):
        from . import sync as s
        try:
            s.sync(cfg, state_dir=s.default_state_dir(), timeout_seconds=15)
        except Exception:
            pass
    end = time.monotonic() + max(0.0, args.timeout)
    fingerprint = None
    jobs = []
    while True:
        current = _courier_fingerprint(cfg)
        if current != fingerprint:
            fingerprint = current
            _, _, _, jobs = _courier_data(cfg)
            if jobs:
                break
        if time.monotonic() >= end:
            break
        time.sleep(min(1.0, max(0.01, end - time.monotonic())))
    jobs = jobs[:args.limit]
    if args.json:
        print(json.dumps(jobs, ensure_ascii=False))
    elif not jobs:
        print("courier wait timed out; no undelivered messages")
    else:
        print("📨 courier work — use the native SendMessage tool, then record exactly one receipt per row:")
        for job in jobs:
            about = f" [{job['task']}]" if job.get("task") else ""
            print(f"  {job['message_id'][:8]} → {job['name']}{about}: {job['body']}")
            print(f"    board receipt {job['message_id']} '{job['recipient']}' delivered")
    return 0


def cmd_receipt(args, cfg):
    from . import comms, coord, events as ev_mod, sync as s
    evs, _, _, _ = _courier_data(cfg)
    matches = [m for m in comms.messages(evs) if m["id"].startswith(args.message)]
    if len(matches) != 1:
        print("message id is unknown or ambiguous", file=sys.stderr)
        return 2
    msg = matches[0]
    current = next((r.get("state") for r in (msg.get("delivery") or {}).get("recipients", [])
                    if args.recipient in (r.get("session_key"), r.get("native_id"))), None)
    if current == args.state or current == "acked" or (current == "delivered" and args.state == "failed"):
        print(f"receipt already {current or args.state}; no duplicate event written")
        return 0
    event = comms.receipt_event(msg["id"], args.recipient, args.state, coord.actor_for(cfg),
                                reason=args.reason, transport=args.transport)
    if not ev_mod.spool_append(s.default_state_dir(), event):
        print("could not queue receipt", file=sys.stderr)
        return 2
    published = False
    if not getattr(args, "no_sync", False):
        state = s.sync(cfg, state_dir=s.default_state_dir(), timeout_seconds=15)
        published = state.last_push_ok and not state.pending
    print(f"receipt {args.state} queued" + (" and published" if published else ""))
    return 0


def cmd_feed(args, cfg):
    from . import comms
    snap = _snap_for_comms(args, cfg)
    hours = float(args.hours)
    items = comms.feed(snap.events, since_s=hours * 3600)
    if args.json:
        print(json.dumps(items))
        return 0
    for sv in comms.servers(snap.events, snap.views, cfg, getattr(snap, "sessions", []),
                            getattr(snap, "session_diagnostics", [])):
        last = render.fmt_age(sv["last_sync_ago_s"]) if sv["last_sync_ago_s"] is not None else "never"
        print(f"🖥  {sv['id']}: last sync {last} ago · {len(sv['sessions'])} active session(s) · owns {len(sv['owned'])}")
        for se in sv["sessions"][:6]:
            print(f"     · {se['alias']} ({render.fmt_age(se['ago_s'])} ago)")
    print(f"\n🕒 last {hours:g}h across servers:")
    for it in items[: args.limit]:
        print(f"  {it['at'][11:16]}  {it['host']:<6} {render.middle(it['who'], 34):<34} {it['task'] or '':<44} {it['what']}")
    return 0


COMMANDS_EXTRA = {"here": cmd_here, "rollcall": cmd_rollcall, "msg": cmd_msg, "inbox": cmd_inbox,
                  "ack": cmd_ack, "feed": cmd_feed, "courier": cmd_courier_wait,
                  "courier-wait": cmd_courier_wait, "receipt": cmd_receipt,
                  "watch": cmd_watch, "ui": cmd_watch, "html": cmd_html, "serve": cmd_serve}
COMMANDS = {"list": cmd_list, "show": cmd_show, "explain": cmd_explain, "available": cmd_available,
            "changes": cmd_changes, "status": cmd_status, "legend": cmd_legend, "config": cmd_config,
            "plugins": cmd_plugins, "claim": cmd_claim, "release": cmd_release, "hook": cmd_hook,
            "sync": cmd_sync, "install-hooks": cmd_install_hooks, "check": cmd_check, "review": cmd_review,
            "stats": cmd_stats, "rank": cmd_rank, "import-claims": cmd_import_claims, "setup": cmd_setup,
            "completion": cmd_completion, **COMMANDS_EXTRA}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["__complete"]:                     # shell completion fast path: no config, no network
        from . import completion
        try:
            cword, words = int(argv[1]), argv[2:]
            print("\n".join(completion.candidates(build_parser(), words, cword)))
        except Exception:
            pass
        return 0
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
