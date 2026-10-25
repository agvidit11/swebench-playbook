"""Synthetic, private-data-free stress run for phase-3a increment 1."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from workboard import comms, events
from workboard.html_page import PAGE
from workboard.ownership import reduce_ownership
from workboard.sources import claude_sessions

NOW = datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc)
A = {"session_id": "sender", "alias": "h1·synthetic sender", "kind": "claude"}
C = {"session_id": "courier", "alias": "h1·synthetic courier", "kind": "claude"}


def _proc(root: Path, pid: int, start: str):
    path = root / str(pid); path.mkdir()
    (path / "stat").write_text(f"{pid} (claude) " + " ".join(["S"] + ["0"] * 18 + [start, "0"]))


def registry_stress() -> dict:
    with tempfile.TemporaryDirectory() as d:
        root, procs = Path(d) / "registry", Path(d) / "proc"
        root.mkdir(); procs.mkdir()
        uid = os.getuid()
        def add(i, *, domain="local", socket_uid=uid, start=None):
            start = start or str(1000 + i)
            data = {"sessionId": f"synthetic-{i}", "pid": 2000 + i, "pidDomain": domain,
                    "procStart": start, "startedAt": int((NOW.timestamp() - i * 60) * 1000),
                    "messagingSocketPath": f"/run/user/{socket_uid}/cc-socks/{i}.sock",
                    "name": f"Synthetic session {i}", "cwd": "/synthetic/tasks/task"}
            (root / f"{i}.json").write_text(json.dumps(data))
            return data
        for i in range(35):
            row = add(i); _proc(procs, row["pid"], row["procStart"])
        for i in range(35, 40): add(i, socket_uid=uid + 1)
        for i in range(40, 45): add(i, domain="foreign")
        for i in range(45, 48): add(i)  # missing PID
        reused = add(48); _proc(procs, reused["pid"], "different")
        (root / "49.json").write_text("{")
        start = time.perf_counter()
        rows, diag = claude_sessions.discover("h1", root=root, proc_root=procs,
                                               pid_domain="local", now=NOW.timestamp())
        elapsed = time.perf_counter() - start
    classes = {}
    for row in diag:
        classes[row["classification"]] = classes.get(row["classification"], 0) + 1
    assert len(rows) == 35 and classes == {"foreign-uid": 5, "foreign-domain": 5,
                                           "local-stale": 3, "pid-reused": 1, "invalid": 1}, (len(rows), classes)
    return {"records": 50, "included": len(rows), "excluded_or_diagnostic": len(diag),
            "classifications": classes, "seconds": elapsed}


def courier_stress() -> dict:
    session = {"session_key": "claude:h1:1:local:target", "native_id": "target", "host": "h1",
               "kind": "claude", "name": "Synthetic target"}
    recipient = {k: session[k] for k in ("session_key", "native_id", "host", "name")}
    target = {"to": f"session:{session['session_key']}", "to_label": session["name"],
              "resolved_recipients": [recipient]}
    msgs = []
    for i in range(1000):
        ev = comms.new_message(f"synthetic message {i}", target, A)
        msgs.append(events.stamp(ev, "h1", i + 1))
    receipts = []
    for i, msg in enumerate(msgs[:500]):
        rec = events.stamp(comms.receipt_event(msg["event_id"], session["session_key"], "delivered", C),
                           "h1", 2000 + i)
        receipts.extend([rec, dict(rec)])  # crash after append, then replay the same durable event
    start = time.perf_counter()
    pending_after_half = comms.courier_jobs(msgs + receipts, [session], "h1")
    assert len(pending_after_half) == 500
    for i, msg in enumerate(msgs[500:]):
        rec = events.stamp(comms.receipt_event(msg["event_id"], session["session_key"], "delivered", C),
                           "h1", 4000 + i)
        receipts.extend([rec, dict(rec)])
    final_events = msgs + receipts
    assert comms.courier_jobs(final_events, [session], "h1") == []
    reduced = comms.messages(final_events)
    assert len(reduced) == 1000 and all(m["delivery"]["state"] == "delivered" for m in reduced)
    elapsed = time.perf_counter() - start
    return {"messages": 1000, "duplicate_receipts": 1000, "pending_after_simulated_crash": 500,
            "pending_final": 0, "visible_messages": len(reduced), "seconds": elapsed}


def ownership_stress() -> dict:
    checked, states = 0, set()
    for claim in (False, True):
        for active in (False, True):
            for pipeline in (False, True):
                for push_age in (None, 1, 71, 73, 240):
                    checked += 1
                    result = reduce_ownership(
                        {"state": "claimed" if claim else "unassigned"},
                        {"state": "active" if active else "inactive", "last_at": NOW.timestamp() if active else None},
                        {"state": "validating" if pipeline else "none"},
                        {"at": None if push_age is None else (NOW - timedelta(hours=push_age)).isoformat()},
                        done=False, actionable=True, sources_fresh=True, now=NOW.timestamp())
                    state = result["availability"]["state"]; states.add(state)
                    if state == "available":
                        assert not claim and not active and not pipeline and (push_age is None or push_age > 72)
    return {"combinations": checked, "states": sorted(states), "free_invariant": "passed"}


def _task(i):
    return {"task": f"synthetic-task-{i:03d}", "group": "READY", "next": "RUN check", "kind": "multi-turn",
            "tag": "Draft", "state_age_s": i * 60, "age_level": "ok", "vp": "0.1", "status_raw": "draft",
            "owner": "", "claim_health": "FREE", "ownership_state": "available", "ownership_reason": "clear",
            "assignment": {"state": "unassigned"}, "activity": {"state": "inactive"},
            "pipeline": {"state": "none"}, "last_push": {"at": None}, "active": [], "valid": "PASS",
            "vsum": {"issues": [], "total": 1, "info": [], "passed": 1}, "rsum": {"agent": [], "gates": {
                "author": {"check": {"state": "none"}, "review": {"state": "none"}},
                "independent": {"check": {"state": "none"}, "review": {"state": "none"}}}},
            "sync": "OK", "findings": [], "tags": [], "category": {}, "track": "swe-bench-multi-turn",
            "steps": [], "assignee": "h1", "decisions": [], "versions": [], "links": {}, "availability": {"free": True}}


def render_stress() -> dict:
    sessions = [{"session_key": f"claude:h1:1:local:s{i}", "native_id": f"s{i}", "name": f"Synthetic session {i}",
                 "alias": f"h1·Synthetic session {i}", "kind": "claude", "kind_icon": "🟣", "host": "h1",
                 "age_s": i * 60, "status": "idle", "status_ago_s": 60, "live": True, "classification": "local-live",
                 "tasks": [f"synthetic-task-{i:03d}"], "focus": {"confidence": "high"}, "child_runs": [],
                 "transport": {"available": True, "reason": "synthetic courier"},
                 "tokens": {"total": None, "reason": "unavailable"}, "advice": {"state": "keep", "reason": "synthetic"}}
                for i in range(40)]
    data = {"week": {"week": 43, "this_week": 1, "same_point_last_week": 1, "median_4wk": 1, "total": 1},
            "weekly": [], "funnel": {"built": 300, "imported": 300, "submitted": 0, "accepted": 0, "archived": 0, "open": 300},
            "flow": {"latest_round_cycle_p50_h": None, "latest_round_cycle_p75_h": None, "wait_p50_h": None, "wait_p75_h": None},
            "tasks": [_task(i) for i in range(300)], "health": {"codimango": {"ok": True, "detail": "synthetic"}},
            "ledger_ok": True, "ledger_at": NOW.isoformat(), "codimango_at": NOW.isoformat(), "generated_at": NOW.isoformat(),
            "codimango_detail": "", "refresh_error": None, "servers": [{"id": "h1", "last_sync_ago_s": 1,
            "last_activity_ago_s": 1, "sessions": sessions, "owned": [], "session_diagnostics": []}],
            "session_targets": sessions, "task_targets": {f"synthetic-task-{i:03d}": {"state": "resolved",
            "label": sessions[i % 40]["name"], "host": "h1"} for i in range(300)}, "messages": [], "feed": []}
    js = PAGE.split("<script>")[1].split("</script>")[0].replace("__LIVE__", "false")
    harness = r'''
const payload=JSON.parse(require('fs').readFileSync(0,'utf8'));
const els={};
function make(id){const set=new Set();return els[id]={id,textContent:id==='data'?JSON.stringify(payload):'',hidden:id==='team'||id==='stats',style:{},dataset:{},children:[],offsetWidth:0,
 className:'',classList:{add(...x){x.forEach(y=>set.add(y))},remove(...x){x.forEach(y=>set.delete(y))},toggle(x,v){if(v===undefined)v=!set.has(x);v?set.add(x):set.delete(x);return v},contains(x){return set.has(x)}},
 addEventListener(){},querySelectorAll(){return[]},querySelector(){return null},set innerHTML(v){this._html=v;this.children=[]},get innerHTML(){return this._html||''}}}
global.document={getElementById:id=>els[id]||make(id),querySelectorAll:()=>[],querySelector:()=>null,addEventListener:()=>{}};
global.window={addEventListener:()=>{}};global.localStorage={getItem:()=>null,setItem:()=>{},removeItem:()=>{}};
global.innerWidth=1600;global.setInterval=()=>0;global.setTimeout=()=>0;global.requestAnimationFrame=()=>0;
'''
    tail = "\ndocument.getElementById('team').hidden=false;renderTeam();if(!document.getElementById('team').innerHTML.includes('Synthetic session 39'))throw Error('team render incomplete');if(!document.getElementById('rows').innerHTML.includes('synthetic-task-299'))throw Error('board render incomplete');\n"
    with tempfile.TemporaryDirectory() as d:
        script = Path(d) / "render.js"
        script.write_text(harness + js + tail)
        start = time.perf_counter()
        result = subprocess.run(["node", str(script)], input=json.dumps(data), capture_output=True, text=True, timeout=30)
        elapsed = time.perf_counter() - start
    assert result.returncode == 0, result.stderr
    return {"tasks": 300, "sessions": 40, "node_render_seconds": elapsed, "js_errors": 0}


def main():
    results = {"registry": registry_stress(), "courier": courier_stress(),
               "ownership": ownership_stress(), "page": render_stress()}
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
