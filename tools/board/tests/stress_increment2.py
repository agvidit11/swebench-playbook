"""Increment-2 stress: real region builder plus the real inline page patcher."""
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tests.stress_increment1 import _task
from tests.test_visual import realistic, snap
from workboard import html, regions
from workboard.config import load_config
from workboard.html_page import PAGE


NOW = datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc)


def _session(i):
    return {"session_key": f"claude:h1:1:local:s{i}", "native_id": f"s{i}",
            "name": f"Synthetic session {i}", "alias": f"h1·Synthetic session {i}",
            "kind": "claude", "kind_icon": "🟣", "host": "h1",
            "started_at": NOW.isoformat(), "status": "idle", "status_since": NOW.isoformat(),
            "live": True, "classification": "local-live", "tasks": [f"synthetic-task-{i:03d}"],
            "focus": {"confidence": "high"}, "child_runs": [],
            "transport": {"available": True, "reason": "synthetic courier"},
            "restart": {"state": "loaded", "needed": False},
            "tokens": {"total": None, "reason": "unavailable"},
            "advice": {"state": "keep", "reason": "synthetic"}}


def synthetic_full():
    tasks = []
    for i in range(300):
        task = _task(i)
        task.update(
            validation=[{"name": f"synthetic check {n}", "status": "passed",
                         "detail": "synthetic validation detail kept behind the lazy task endpoint " * 3}
                        for n in range(8)],
            decisions=[{"kind": "revision", "at": NOW.isoformat(),
                        "reason": "synthetic reviewer decision detail " * 8}],
            versions=[{"label": f"round {n}", "commits": n + 1, "ended": "revision",
                       "at": NOW.isoformat(), "reason": "synthetic round reason " * 5} for n in range(3)],
            changed=[f"synthetic-task-{i:03d}/file-{n}.py" for n in range(8)],
            gates={"author": {"check": {"state": "ok", "summary": "synthetic gate detail " * 5},
                               "review": {"state": "ok", "note": "synthetic review detail " * 5}}},
            agent_reviews=[{"who": "synthetic", "verdict": "ready", "note": "synthetic note " * 10}],
            legacy={"legacy_owner": "synthetic", "status": "ACTIVE", "updated": "2026-10-25"},
            findings=[{"code": "SYNTHETIC", "severity": "info", "summary": "synthetic finding " * 8,
                       "next": "synthetic next action " * 5}],
            steps=[{"do": "synthetic detailed step " * 6, "eta": "~10m", "routine": False} for _ in range(4)],
            checks={}, last_check=None)
        tasks.append(task)
    sessions = [_session(i) for i in range(40)]
    activity = [{"id": f"event-{i:04d}", "at": NOW.isoformat(), "ts": NOW.timestamp() - i,
                 "host": "h1", "who": f"synthetic-{i % 40}", "type": "check",
                 "task": f"synthetic-task-{i % 300:03d}", "what": "synthetic activity"}
                for i in range(1000)]
    return {"generated_at": NOW.isoformat(), "codimango_at": NOW.isoformat(),
            "health": {"codimango": {"ok": True, "detail": "synthetic"}},
            "ledger_ok": True, "ledger_at": NOW.isoformat(), "refresh_error": None,
            "codimango_detail": "", "week": {"week": 43, "this_week": 1,
            "same_point_last_week": 1, "median_4wk": 1, "total": 1},
            "weekly": [], "funnel": {"built": 300, "imported": 300, "submitted": 0,
            "accepted": 0, "archived": 0, "open": 300},
            "flow": {"latest_round_cycle_p50_h": None, "latest_round_cycle_p75_h": None,
            "wait_p50_h": None, "wait_p75_h": None}, "ages": {}, "load": {"h1": 0},
            "tasks": tasks, "servers": [{"id": "h1", "last_sync_at": NOW.isoformat(),
            "last_activity_at": NOW.isoformat(), "sessions": sessions, "session_count": 40,
            "status_counts": {"busy": 0, "waiting": 0, "idle": 40, "unknown": 0},
            "queue": 0, "sync_error": "", "owned": [], "session_diagnostics": []}],
            "session_targets": sessions, "task_targets": {t["task"]: {"state": "resolved",
            "label": sessions[i % 40]["name"], "host": "h1"} for i, t in enumerate(tasks)},
            "messages": [], "sessions": [], "feed": activity}


def build_cycles():
    rng = random.Random(731)
    full = synthetic_full()
    gens = {key: "0" for key in ("codimango", "git", "ledger", "registry_runs", "presence")}
    cache = regions.RegionCache(full, now=NOW, generations=gens)
    initial = {"summary": cache.region("summary").data, "board": cache.region("board").data,
               "team": cache.region("team").data, "activity": cache.region("activity").data,
               "stats": cache.region("stats").data}
    legacy_bytes = len(regions.canonical_bytes({"tasks": full["tasks"]}))
    compact_bytes = len(cache.region("board").body)
    cycles = []
    builder_start = time.perf_counter()
    for cycle in range(200):
        changed = sorted(rng.sample(range(1, 300), rng.randint(1, 3)))  # task 0 holds the open drawer
        tasks = list(full["tasks"])
        for idx in changed:
            row = dict(tasks[idx])
            failed = row.get("valid") != "FAIL"
            row["valid"] = "FAIL" if failed else "PASS"
            row["vsum"] = ({"issues": [{"check": "synthetic", "why": "changed", "fix": "fix it",
                                          "severity": "fail"}], "total": 1, "info": [], "passed": 0}
                           if failed else {"issues": [], "total": 1, "info": [], "passed": 1})
            tasks[idx] = row
        full = dict(full, tasks=tasks)
        servers = copy.deepcopy(full["servers"])
        sidx = cycle % 40
        servers[0]["sessions"][sidx]["status"] = "busy" if cycle % 2 else "idle"
        full["servers"] = servers
        activity = None
        if cycle % 10 == 0:
            event = {"id": f"new-{cycle:03d}", "at": NOW.isoformat(), "ts": NOW.timestamp() + cycle,
                     "host": "h1", "who": "synthetic-new", "type": "check",
                     "task": f"synthetic-task-{changed[0]:03d}", "what": "new synthetic activity"}
            full["feed"] = [event, *full["feed"]][:1000]
            activity = True
        gens = dict(gens, git=str(cycle + 1), registry_runs=str(cycle + 1),
                    ledger=str(cycle + 1) if activity else gens["ledger"])
        cache.replace(full, now=NOW, generations=gens)
        cycles.append({"board": cache.region("board").data, "team": cache.region("team").data,
                       "activity": cache.region("activity").data if activity else None,
                       "changed": [f"synthetic-task-{i:03d}" for i in changed],
                       "session": f"claude:h1:1:local:s{sidx}"})
    elapsed = time.perf_counter() - builder_start
    return initial, cycles, {"legacy_board_bytes": legacy_bytes, "compact_board_bytes": compact_bytes,
                             "reduction_percent": round(100 * (legacy_bytes - compact_bytes) / legacy_bytes, 1),
                             "cycles": 200, "builder_seconds": round(elapsed, 4),
                             "no_change_body_bytes": 0, "region_builds": cache.build_counts}


HARNESS = r'''
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),els={},saved={};let serial=0;
class Classes{constructor(owner){this.owner=owner;this.s=new Set()}add(...x){x.forEach(y=>this.s.add(y))}remove(...x){x.forEach(y=>this.s.delete(y))}toggle(x,v){if(v===undefined)v=!this.s.has(x);v?this.s.add(x):this.s.delete(x);return v}contains(x){return this.s.has(x)}}
class El{constructor(id='',tag='div'){this.id=id;this.tagName=tag.toUpperCase();this.dataset={};this.style={};this.hidden=id==='team'||id==='stats';this.children=[];this.parent=null;this.classList=new Classes(this);this.identity=++serial;this.value='';this.textContent=id==='data'?JSON.stringify({...input.initial.summary,...input.initial.board,...input.initial.team,feed:input.initial.activity.items,...input.initial.stats}):'';this.offsetWidth=0}
 set className(v){this._className=v;String(v).split(/\s+/).filter(Boolean).forEach(x=>this.classList.add(x))}get className(){return this._className||''}
 set innerHTML(v){this._html=String(v);this.children=[];if(this.id==='rows'||this.id==='sessionrows'||this.tagName==='TBODY'){for(const hit of this._html.matchAll(/<tr\b([^>]*)>([\s\S]*?)<\/tr>/g)){const e=new El('', 'tr'),a=hit[1],cl=(a.match(/class="([^"]*)"/)||[])[1]||'';e.className=cl;const t=(a.match(/data-t="([^"]*)"/)||[])[1],s=(a.match(/data-session="([^"]*)"/)||[])[1],g=(a.match(/data-session-group="([^"]*)"/)||[])[1],bg=(a.match(/data-group="([^"]*)"/)||[])[1];if(t)e.dataset.t=t;if(s)e.dataset.session=s;if(g)e.dataset.sessionGroup=g;if(bg)e.dataset.group=bg;e.textContent=hit[2].replace(/<[^>]*>/g,'');e.parent=this;this.children.push(e)}}}
 get innerHTML(){return this._html||''}get firstElementChild(){return this.children[0]||null}get lastElementChild(){return this.children[this.children.length-1]||null}
 replaceWith(n){const i=this.parent.children.indexOf(this);if(i>=0){this.parent.children[i]=n;n.parent=this.parent}}
 appendChild(n){if(n.parent)n.parent.children=n.parent.children.filter(x=>x!==n);n.parent=this;this.children.push(n);return n}
 remove(){if(this.parent)this.parent.children=this.parent.children.filter(x=>x!==this)}
 insertAdjacentHTML(where,h){const tmp=new El('',this.tagName);tmp.innerHTML=h;const n=tmp.firstElementChild||new El();n.parent=this;if(where==='afterbegin')this.children.unshift(n);this._html=h+(this._html||'')}
 addEventListener(){}querySelectorAll(){return[]}querySelector(){return null}getBoundingClientRect(){return{width:10,height:10}}contains(){return false}}
function make(id){return els[id]||(els[id]=new El(id))}
global.document={getElementById:make,createElement:t=>new El('',t),querySelectorAll:()=>[],querySelector:()=>null,addEventListener:()=>{},activeElement:{id:'',tagName:'BODY'}};
global.window={addEventListener:()=>{}};global.localStorage={getItem:k=>saved[k]||null,setItem:(k,v)=>saved[k]=v,removeItem:k=>delete saved[k]};
global.innerWidth=1600;global.setInterval=()=>0;global.setTimeout=()=>0;global.clearTimeout=()=>{};global.requestAnimationFrame=()=>0;global.fetch=async()=>{throw Error('unexpected network')};
'''


def patch_stress(initial, cycles):
    js = PAGE.split("<script>")[1].split("</script>")[0].replace("__LIVE__", "false")
    tail = r'''
D={...D,...input.initial.summary,...input.initial.board,...input.initial.team,feed:input.initial.activity.items,...input.initial.stats};render();
document.getElementById('team').hidden=false;renderTeam();S.owner='free';S.kind='multi-turn';S.q='synthetic';S.open='synthetic-task-000';document.getElementById('drawer').classList.add('open');
let boardChecks=0,teamChecks=0,activityChecks=0;
for(const [ci,cycle] of input.cycles.entries()){const br=document.getElementById('rows'),before=Object.fromEntries(br.children.filter(x=>x.dataset.t).map(x=>[x.dataset.t,x]));applyRegion('board',cycle.board);const after=Object.fromEntries(br.children.filter(x=>x.dataset.t).map(x=>[x.dataset.t,x]));for(const [task,node] of Object.entries(before)){if(!cycle.changed.includes(task)&&after[task]!==node)throw Error('board identity lost '+task+' cycle '+ci);boardChecks++}
 const sr=document.getElementById('sessionrows'),sb=Object.fromEntries(sr.children.filter(x=>x.dataset.session).map(x=>[x.dataset.session,x]));applyRegion('team',cycle.team);const sa=Object.fromEntries(sr.children.filter(x=>x.dataset.session).map(x=>[x.dataset.session,x]));for(const [key,node] of Object.entries(sb)){if(key!==cycle.session&&sa[key]!==node)throw Error('session identity lost '+key+' cycle '+ci+' expected '+cycle.session+' htmlsame '+(S.teamh[key]===sessionRow(sessionByKey(key))));teamChecks++}
 if(cycle.activity){const beforeIds=new Set(S.activityIds);applyRegion('activity',cycle.activity);for(const id of beforeIds)if(!S.activityIds.has(id))throw Error('activity id lost');activityChecks++}
 if(S.owner!=='free'||S.kind!=='multi-turn'||S.q!=='synthetic')throw Error('filter state reset');if(S.open!=='synthetic-task-000'||!document.getElementById('drawer').classList.contains('open'))throw Error('drawer state reset')}
process.stdout.write(JSON.stringify({board_identity_checks:boardChecks,team_identity_checks:teamChecks,activity_cycles:activityChecks,filters:'preserved',drawer:'preserved'}));
'''
    with tempfile.TemporaryDirectory(prefix="wb-node-stress-") as temp:
        script = Path(temp) / "stress.js"
        script.write_text(HARNESS + js + tail)
        start = time.perf_counter()
        result = subprocess.run(["node", str(script)], input=json.dumps({"initial": initial, "cycles": cycles}),
                                capture_output=True, text=True, timeout=120)
        elapsed = time.perf_counter() - start
    if result.returncode:
        raise AssertionError(result.stderr)
    return dict(json.loads(result.stdout), node_seconds=round(elapsed, 4))


def idle_cpu(seconds: float):
    with tempfile.TemporaryDirectory(prefix="wb-idle-") as temp, mock.patch.dict(os.environ, {
            "WORKBOARD_CACHE": str(Path(temp) / "cache"), "WORKBOARD_STATE": str(Path(temp) / "state")}):
        cfg = load_config(Path("/nonexistent")); snapshot = snap(realistic())
        server = html.serve(lambda: snapshot, cfg, port=0, interval=3600, team_interval=3600)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        cpu0, wall0 = time.process_time(), time.perf_counter()
        time.sleep(seconds)
        cpu, wall = time.process_time() - cpu0, time.perf_counter() - wall0
        server.shutdown(); server.server_close(); thread.join(2)
    return {"sample_wall_seconds": round(wall, 3), "sample_cpu_seconds": round(cpu, 6),
            "cpu_seconds_per_idle_minute": round(cpu * 60 / wall, 6),
            "one_core_percent": round(cpu / wall * 100, 4)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--idle-seconds", type=float, default=5)
    args = parser.parse_args(argv)
    initial, cycles, builder = build_cycles()
    print(json.dumps({"builder": builder, "page": patch_stress(initial, cycles),
                      "idle": idle_cpu(args.idle_seconds)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
