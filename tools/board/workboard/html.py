"""HTML dashboard: `board html` writes one self-contained page; `board serve` serves it live on localhost.

Same data as the terminal views (TaskViews + stats). No external assets, no CDN: CSS, JS and data are inline.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _task_extra(v, obs_by_task, ev_by_task, decisions) -> dict:
    """Detail for hover cards and the task card: validation checks, timestamps, commits, reviews, rounds."""
    from .reviews import versions
    o = obs_by_task.get(v.entity_id, {})
    tev = ev_by_task.get(v.entity_id, [])
    head = o.get("git.task_head")
    agent_reviews = [{"who": e["actor"].get("alias", ""), "verdict": e["payload"].get("verdict"),
                      "confidence": e["payload"].get("confidence"), "note": (e["payload"].get("note") or "")[:120],
                      "current": bool(head and e.get("commit") == head), "at": e["occurred_at"]}
                     for e in tev if e["type"] == "review"]
    checks = [e for e in tev if e["type"] == "check"]
    last_check = None
    if checks:
        c = checks[-1]
        last_check = dict(c["payload"], at=c["occurred_at"], current=bool(head and c.get("commit") == head))
    legacy = [e["payload"] for e in tev if e["type"] == "note" and e["payload"].get("legacy_owner")]
    dec = decisions.get(v.entity_id, {}).get("decisions", [])
    return {
        "validation": [{"name": x.get("name", ""), "status": x.get("status", ""), "detail": x.get("detail", "")}
                       for x in (o.get("codimango.validation") or [])],
        "oracle": [o.get("codimango.oracle_pass"), o.get("codimango.oracle_total")],
        "avocado": [o.get("codimango.avocado_pass"), o.get("codimango.avocado_total")],
        "created_at": o.get("codimango.created_at"), "entered_pool_at": o.get("codimango.entered_pool_at"),
        "reviewed_at": o.get("codimango.reviewed_at"), "status_raw": o.get("codimango.status"),
        "server_commit": (o.get("codimango.commit_sha") or "")[:8], "server_head": (o.get("codimango.head_commit_sha") or "")[:8],
        "validated_commit": (o.get("codimango.validation_commit_sha") or "")[:8], "task_head": (head or "")[:8],
        "changed": (o.get("git.changed_since_validated") or [])[:8],
        "agent_reviews": agent_reviews, "last_check": last_check,
        "legacy": legacy[-1] if legacy else None,
        "decisions": dec,
        "versions": versions(o.get("git.commit_times") or [], dec) if (dec or o.get("git.commit_times")) else [],
    }


def payload(snap, cfg) -> dict:
    from . import reviews, stats as st
    from .app import cache_dir
    obs_by_task = {}
    for ob in snap.observations:
        obs_by_task.setdefault(ob.entity_id, {}).update(ob.fields)
    ev_by_task = {}
    for e in snap.events:
        ent = e.get("entity")
        if ent:
            ev_by_task.setdefault(ent.get("id"), []).append(e)
    decisions = reviews.load(cache_dir())
    views = []
    for v in snap.views:
        f = dict(v.fields)
        views.append({"task": v.entity_id, **{k: f.get(k) for k in (
            "group", "next", "state", "state_age_s", "age_level", "owner", "claim_health", "valid", "review",
            "confidence", "confidence_stale", "sync", "check", "check_stale", "check_fail", "pushes_before_submit",
            "pushes_after_submit", "track", "active", "dissent", "links")},
            "findings": [{"code": x.code, "severity": x.severity, "summary": x.summary, "next": x.next_action}
                         for x in v.findings],
            **_task_extra(v, obs_by_task, ev_by_task, decisions)})
    weekly = st.weekly(snap.observations, cfg, snap.now, 10)
    return {
        "generated_at": snap.now.isoformat(),
        "health": {k: {"ok": h.ok, "detail": h.detail} for k, h in snap.health.items()},
        "ledger_ok": bool(snap.sync_state and snap.sync_state.last_pull_ok
                          and (snap.sync_state.last_push_ok or not snap.sync_state.pending)) if snap.sync_state else None,
        "week": st.week_numbers(snap.observations, cfg, snap.now),
        "weekly": [dict(r, week=r["week"].strftime("%b %d")) for r in weekly],
        "funnel": st.funnel(snap.observations),
        "flow": st.cycle_and_wait(snap.observations, snap.now),
        "ages": st.pipeline_age(snap.views, snap.now),
        "tasks": views,
    }


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧭 workboard</title>
<style>
:root{--bg:#14161c;--panel:#1b1e26;--line:#2a2e39;--text:#e6e8ee;--dim:#8b90a0;--pink:#f78fb3;--green:#7bd88f;
--amber:#f5c26b;--red:#ff6b6b;--blue:#7ab8ff;--violet:#b39dff;--teal:#5fd7d7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}
header{padding:22px 28px 10px;display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
h1{margin:0;font-size:20px;color:var(--pink)}.sub{color:var(--dim);font-style:italic}
.live{display:inline-flex;align-items:center;gap:6px;color:var(--dim);margin-left:auto}
.dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}
.dot.bad{background:var(--red)}@keyframes pulse{0%{box-shadow:0 0 0 0 #7bd88f88}70%{box-shadow:0 0 0 8px #7bd88f00}100%{box-shadow:0 0 0 0 #7bd88f00}}
.wrap{padding:0 28px 40px}.week{color:var(--dim);margin:2px 0 12px}.week b{color:var(--green);font-size:16px}
.bar{display:flex;height:4px;border-radius:3px;overflow:hidden;margin:8px 0 14px}.bar span{transition:flex .6s}
.tabs{display:flex;gap:8px;margin-bottom:12px}.tab{padding:6px 14px;border-radius:999px;border:1px solid var(--line);cursor:pointer;color:var(--dim);background:none;font:inherit}
.tab.on{background:var(--pink);color:#14161c;border-color:var(--pink);font-weight:700}
.controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
.chip{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:999px;border:1px solid var(--line);cursor:pointer;user-select:none;transition:all .15s;background:none;color:var(--text);font:inherit}
.chip .c{width:8px;height:8px;border-radius:50%}.chip.off{opacity:.35}.chip:hover{transform:translateY(-1px)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}.seg button{background:none;border:0;color:var(--dim);padding:5px 12px;cursor:pointer;font:inherit}
.seg button.on{background:var(--violet);color:#14161c;font-weight:700}
input[type=search]{background:var(--panel);border:1px solid var(--line);color:var(--text);padding:6px 12px;border-radius:999px;min-width:220px;font:inherit}
.health{color:var(--dim);margin-left:auto}.health .ok{color:var(--green)}.health .bad{color:var(--red)}
.tbl{overflow-x:auto;border-radius:12px}body{overflow-x:hidden}table{width:100%;border-collapse:separate;border-spacing:0;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
th{text-align:left;color:var(--dim);font-weight:600;padding:10px 12px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--panel);cursor:pointer;white-space:nowrap}
td{padding:8px 12px;border-bottom:1px solid #22252f;white-space:nowrap}tr.row{cursor:pointer;animation:fade .35s ease both}
tr.row:hover td{background:#222633}tr.row td:first-child{border-left:4px solid var(--s)}@keyframes fade{from{opacity:0;transform:translateY(3px)}to{opacity:1}}
tr.group td{background:#171a21;color:var(--dim);font-weight:700;padding:6px 12px;border-bottom:1px solid var(--line)}
.task{font-weight:700}.spark{color:var(--pink);animation:twinkle 1.2s ease-in-out infinite}@keyframes twinkle{50%{opacity:.25}}
.pill{display:inline-block;padding:1px 9px;border-radius:6px;color:#14161c;font-weight:700;font-size:12px}
.age{color:var(--dim);margin-left:6px}.age.warn{color:var(--amber)}.age.block{color:var(--red)}
.ok{color:var(--green)}.run{color:var(--amber)}.bad{color:var(--red)}.dim{color:var(--dim)}
.ticks{font-weight:800;letter-spacing:-1px}.conf{letter-spacing:1px;margin-left:6px}
.legend{color:var(--dim);margin-top:12px;display:flex;gap:16px;flex-wrap:wrap}
aside{position:fixed;top:0;right:-460px;width:440px;height:100%;background:var(--panel);border-left:1px solid var(--line);padding:22px;transition:right .25s ease;overflow:auto;box-shadow:-10px 0 30px #0008}
aside.open{right:0}aside h2{margin:0 0 8px;font-size:16px;word-break:break-all;padding-right:70px}aside .x{float:right;cursor:pointer;color:var(--dim)}
aside .kv{display:grid;grid-template-columns:120px 1fr;gap:6px 10px;margin:14px 0}aside .kv div:nth-child(odd){color:var(--dim)}
.links{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.lnk{padding:5px 12px;border-radius:999px;border:1px solid var(--line);color:var(--text);text-decoration:none;transition:all .15s}
.lnk:hover{border-color:var(--pink);color:var(--pink);transform:translateY(-1px)}aside h2 a{color:var(--text);text-decoration:none}aside h2 a:hover{color:var(--pink)}
#tip{position:fixed;z-index:50;max-width:440px;background:#0f1117;border:1px solid var(--line);border-radius:10px;padding:10px 12px;
box-shadow:0 10px 30px #000a;pointer-events:none;opacity:0;transform:translateY(4px);transition:opacity .12s,transform .12s;font-size:12.5px;white-space:normal}
#tip.on{opacity:1;transform:none}#tip h4{margin:0 0 6px;font-size:12.5px;color:var(--dim);font-weight:600}
#tip ul,.card-list{margin:0;padding:0;list-style:none}#tip li,.card-list li{margin:3px 0;display:flex;gap:7px}
.b-ok{color:var(--green)}.b-pend{color:var(--amber)}.b-bad{color:var(--red)}.b-info{color:var(--blue)}.b-dim{color:var(--dim)}
td.own{max-width:240px;overflow:hidden;text-overflow:ellipsis}td.task{max-width:380px;overflow:hidden;text-overflow:ellipsis}
td,th{padding-left:10px;padding-right:10px}td[data-tip]{cursor:help}td[data-tip]:hover{background:#262a37!important}
.summary{background:#191c24;border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:10px 0;line-height:1.55}
.timeline{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0}.ver{border:1px solid var(--line);border-radius:8px;padding:4px 9px}
.ver b{color:var(--pink)}.arrow{color:var(--dim)}aside h3{font-size:13px;color:var(--dim);margin:16px 0 6px}
.finding{background:#2a2216;border:1px solid #4a3a1c;border-radius:8px;padding:8px 10px;margin:6px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}.card .big{font-size:26px;font-weight:800}
.card .lbl{color:var(--dim)}.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.panel h3{margin:0 0 10px;font-size:14px}.hbar{display:flex;align-items:center;gap:10px;margin:5px 0}.hbar .l{width:110px;color:var(--dim)}
.hbar .b{height:14px;border-radius:4px;transition:width .6s ease}.empty{color:var(--dim);padding:30px;text-align:center}
</style></head><body>
<header><h1>🧭 workboard</h1><span class="sub">your tasks across every server and session</span>
<span class="live"><span class="dot" id="dot"></span><span id="when"></span></span></header>
<div class="wrap">
<div class="week" id="week"></div><div class="bar" id="bar"></div>
<div class="tabs"><button class="tab on" data-tab="board">📋 Board</button><button class="tab" data-tab="stats">📊 Stats</button></div>
<section id="board">
<div class="controls" id="chips"></div>
<div class="controls"><div class="seg" id="owner"></div><input type="search" id="q" placeholder="🔍 search tasks  ( / )">
<span class="health" id="health"></span></div>
<div class="tbl"><table><thead><tr><th data-k="task">Task</th><th data-k="next">Next</th><th data-k="state">State</th><th data-k="owner">Owner</th>
<th data-k="valid">Validation</th><th data-k="check">Presubmit</th><th data-k="review">Review</th><th data-k="sync">Sync</th></tr></thead>
<tbody id="rows"></tbody></table></div>
<div class="legend"><span><span class="spark">✦</span> changed</span><span><span class="ok ticks">✓✓</span> two sessions approved</span>
<span><span class="run">✓</span> one</span><span><span class="dim">↻✓</span> older commit</span><span>▰▰▰▰▱ confidence</span>
<span>👤 owner</span><span>👀 active</span><span>📜 CLAIMS.md</span><span>💤 expired</span><span>🔓 free</span></div>
</section>
<section id="stats" hidden></section>
</div>
<div id="tip"></div><aside id="drawer"><span class="x" id="close">✕ close</span><div id="dbody"></div></aside>
<script id="data" type="application/json">__DATA__</script>
<script>
const LIVE = __LIVE__;
let D = JSON.parse(document.getElementById('data').textContent);
const G = {ATTENTION:['#ff6b6b','🔥','needs you'],READY:['#7bd88f','✨','ready'],WAITING:['#7ab8ff','⏳','waiting'],DONE:['#8b90a0','🎉','done']};
const PILL = {DRAFT:'#e0b860',QUEUE:'#8fb8e0',REVIEW:'#5fafff',NEEDS_REV:'#ff875f',ACCEPTED:'#7bd88f',ARCHIVED:'#808080',NOT_IMPORTED:'#585858'};
const NEXT = {FIX:'🔧',RESOLVE:'🤺',RERUN:'🔁',SUBMIT:'🚀',GET:'👀',RUN:'🧪',WAIT:'⏳',ADDRESS:'📝',IMPORT:'📥',CHECK:'🕐','—':'🎉'};
const S = {groups:new Set(['ATTENTION','READY','WAITING']), owner:'all', q:'', sort:null, dir:1, prev:JSON.parse(localStorage.getItem('wb-prev')||'{}')};
const esc = s => String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const age = s => s==null?'?':s<60?'<1m':s<3600?Math.floor(s/60)+'m':s<86400?Math.floor(s/3600)+'h':Math.floor(s/86400)+'d';
function owner(t){const h=t.claim_health,o=esc(t.owner);
 if(h==='DONE')return'';if(h==='FREE'||!t.owner)return'<span style="color:var(--blue)">🔓 free</span>';
 if(h==='ACTIVE')return`<span class="run">👀 ${o}</span> <span class="dim">${age((t.active||[{}])[0].ago_s)}</span>`;
 if(h==='CONFLICT')return`<span class="bad">🤺 ${o}</span>`;if(h==='EXPIRED')return`<span class="dim">💤 ${o}</span>`;
 if(h==='LEGACY')return`<span class="dim">📜 ${o}</span>`;return`<span style="color:var(--violet)">👤 ${o}</span>`}
function valid(v){return v==='PASS'?'<span class="ok">✔ pass</span>':v==='RUN'?'<span class="run">○ running</span>':v==='FAIL'?'<span class="bad">✘ failed</span>':`<span class="dim">· ${esc(v)}</span>`}
function check(t){if(!t.check||t.check==='NONE')return'<span class="dim">· not run</span>';if(t.check_fail)return`<span class="bad">✘ ${esc(t.check.split(' ').pop())}</span>`;
 return t.check_stale?'<span class="dim">↻ ✔ old</span>':`<span class="ok">✔ ${esc(t.check.split(' ')[0])}</span>`}
function review(t){const c=t.confidence||0,bars=c?'▰'.repeat(c)+'▱'.repeat(5-c):'';const col=c<=2?'var(--red)':c===3?'var(--amber)':'var(--green)';
 const tick=t.review==='R2'?'<span class="ok ticks">✓✓</span>':t.review==='R1'?'<span class="run ticks">✓</span>':t.review==='R~'?'<span class="dim">↻✓</span>':'<span class="dim">·</span>';
 return tick+(bars?`<span class="conf" style="color:${t.confidence_stale?'var(--dim)':col}">${bars}</span>`:'')}
function sync(s){s=String(s||'');return s.startsWith('OK')?'<span class="ok">✔</span>'+(s.includes('doc')?' <span class="dim">doc</span>':''):
 s==='HEAD≠SERVER'?'<span class="run">⚠ push</span>':s==='STALE_VALID'?'<span class="run">⚠ stale</span>':'<span class="dim">·</span>'}
function next(t){const n=t.next||'',e=NEXT[n.split(' ')[0]]||'•';const col=n.startsWith('FIX')||n.startsWith('RESOLVE')?'var(--red)':n.startsWith('SUBMIT')?'var(--green)':n.startsWith('WAIT')?'var(--dim)':'var(--amber)';
 return `${e} <span style="color:${col}">${esc(n)}</span>`}
function state(t){const l=(t.state||'?').replace('_',' ').toLowerCase().replace('needs rev','sent back');
 return `<span class="pill" style="background:${PILL[t.state]||'#666'}">${esc(l)}</span><span class="age ${t.age_level||''}">${age(t.state_age_s)}</span>`}
const B=(cls,ch,txt)=>`<li><span class="${cls}">${ch}</span><span>${txt}</span></li>`;
const vb=st=>st==='passed'?['b-ok','●']:st==='failed'||st==='error'?['b-bad','✘']:st==='warn'?['b-pend','▲']:['b-pend','○'];
const fdate=x=>x?new Date(x).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'—';
function tipValid(t){if(!t.validation.length)return'<h4>validation</h4><ul>'+B('b-dim','·','no validation results yet')+'</ul>';
 return '<h4>validation checks</h4><ul>'+t.validation.map(v=>{const[c,ch]=vb(v.status);return B(c,ch,`<b>${esc(v.name)}</b> ${v.detail?'<span class="dim">— '+esc(v.detail)+'</span>':''}`)}).join('')+'</ul>'}
function tipNext(t){const n=t.next||'';let h='<h4>why: '+esc(n)+'</h4><ul>';
 const bad=t.validation.filter(v=>v.status==='failed'||v.status==='error');
 if(n.startsWith('FIX'))h+=bad.map(v=>B('b-bad','✘',`<b>${esc(v.name||'a validation check')}</b> <span class="dim">${esc(v.detail||'')}</span>`)).join('')||B('b-bad','✘','validation failing');
 else if(n.startsWith('RUN check'))h+=B('b-pend','○','presubmit not run on the current commit')+B('b-info','→','<code>board check run '+esc(t.task)+'</code>');
 else if(n.startsWith('GET'))h+=B('b-pend','○',`${t.review==='R1'?'one more':'two'} agent-session reviews needed (ready, same commit)`);
 else if(n.startsWith('RERUN'))h+=t.findings.map(f=>B('b-pend','⚠',esc(f.summary))).join('')+B('b-info','→','codimango task rerun '+esc(t.task));
 else if(n.startsWith('ADDRESS')){const d=t.decisions[t.decisions.length-1];h+=B('b-bad','↩',`sent back ${d?fdate(d.at):''}`)+(d&&d.reason?B('b-dim','“',esc(d.reason)):'')}
 else if(n.startsWith('WAIT'))h+=B('b-info','⏳',n==='WAIT reviewer'?'in the review queue':'validation is running');
 else if(n.startsWith('SUBMIT'))h+=B('b-ok','●','presubmit passed')+B('b-ok','●','two sessions approved');
 return h+'</ul>'}
function tipState(t){let h='<h4>state</h4><ul>'+B('b-info','●',`<b>${esc((t.state||'').replace('_',' ').toLowerCase())}</b> for ${age(t.state_age_s)}`+(t.age_level&&t.age_level!=='ok'?` <span class="b-${t.age_level==='block'?'bad':'pend'}">(${t.age_level==='block'?'overdue':'getting old'})</span>`:''));
 h+=B('b-dim','✎','created '+fdate(t.created_at));if(t.entered_pool_at)h+=B('b-dim','↗','submitted '+fdate(t.entered_pool_at));
 t.decisions.forEach(d=>h+=B(d.kind==='accept'?'b-ok':'b-bad',d.kind==='accept'?'✔':'↩',`${d.kind==='accept'?'accepted':'sent back'} ${fdate(d.at)}`));return h+'</ul>'}
function tipOwner(t){let h='<h4>who is on it</h4><ul>';const hl=t.claim_health;
 if(hl==='OWNED')h+=B('b-ok','👤','claimed by '+esc(t.owner));if(hl==='CONFLICT')h+=B('b-bad','🤺','two live claims: '+esc(t.owner));
 if(hl==='EXPIRED')h+=B('b-dim','💤','claim expired ('+esc(t.owner)+')');if(hl==='FREE')h+=B('b-info','🔓','nobody — claim it with board claim');
 (t.active||[]).forEach(a=>h+=B('b-pend','👀',`${esc(a.alias)} touched it ${age(a.ago_s)} ago`));
 if(t.legacy)h+=B(t.legacy.live===false?'b-dim':'b-info','📜',`CLAIMS.md: ${esc(t.legacy.legacy_owner)} · ${esc(t.legacy.status)} · ${esc(t.legacy.updated)}`);return h+'</ul>'}
function tipReview(t){let h='<h4>reviews</h4><ul>';const cur=t.agent_reviews.filter(r=>r.current),ready=new Set(cur.filter(r=>r.verdict==='ready').map(r=>r.who));
 h+=B(ready.size>=2?'b-ok':'b-pend',ready.size>=2?'●':'○',`agent sessions ready on this commit: <b>${ready.size}/2</b>`);
 t.agent_reviews.slice(-4).forEach(r=>h+=B(r.verdict==='ready'?(r.current?'b-ok':'b-dim'):'b-bad',r.verdict==='ready'?'✓':'✘',`${esc(r.who)} · ${esc(r.verdict)}${r.confidence?' · C'+r.confidence:''}${r.current?'':' · older commit'}`));
 const c=t.last_check;h+=B(c?(c.fail?'b-bad':c.current?'b-ok':'b-pend'):'b-pend',c?(c.fail?'✘':c.current?'●':'↻'):'○',c?`presubmit P${c.pass||0} W${c.warn||0} F${c.fail||0}${c.current?'':' (older commit)'}`:'presubmit not run');
 const rounds=t.decisions.filter(d=>d.kind==='revision').length;if(t.decisions.length)h+=B(rounds?'b-pend':'b-ok','👥',`human: ${rounds} revision round${rounds===1?'':'s'}${t.decisions.some(d=>d.kind==='accept')?' · accepted':''}`);return h+'</ul>'}
function tipCheck(t){const c=t.last_check;if(!c)return'<h4>presubmit</h4><ul>'+B('b-pend','○','not run yet')+B('b-info','→','board check run '+esc(t.task))+'</ul>';
 return '<h4>presubmit</h4><ul>'+B('b-ok','●',`${c.pass||0} passed`)+B(c.warn?'b-pend':'b-dim','▲',`${c.warn||0} warnings`)+B(c.fail?'b-bad':'b-dim','✘',`${c.fail||0} failures`)+
  B(c.current?'b-ok':'b-pend',c.current?'●':'↻',c.current?'on the current commit':'ran on an older commit')+B('b-dim','🕐',fdate(c.at))+'</ul>'}
function tipSync(t){let h='<h4>server vs your latest push</h4><ul>';const s=String(t.sync||'');
 h+=B('b-dim','#',`your latest commit <code>${esc(t.task_head||'—')}</code> · server validated <code>${esc(t.validated_commit||t.server_commit||'—')}</code>`);
 if(s==='OK')h+=B('b-ok','●','server has your latest commit and validated it');
 if(s==='OK·doc')h+=B('b-ok','●','only docs changed since validation (no rerun needed)')+t.changed.map(c=>B('b-dim','·',esc(c))).join('');
 if(s==='STALE_VALID')h+=B('b-pend','⚠','server saw your commit but validated an older one')+t.changed.map(c=>B('b-pend','·',esc(c))).join('')+B('b-info','→','codimango task rerun '+esc(t.task));
 if(s==='HEAD≠SERVER')h+=B('b-pend','⚠','your newest push is not on the server yet')+B('b-info','→','codimango task rerun '+esc(t.task));
 if(s==='UNCHECKED'||s==='—')h+=B('b-dim','·','could not compare (no git data)');return h+'</ul>'}
const TIPS={next:tipNext,state:tipState,owner:tipOwner,valid:tipValid,check:tipCheck,review:tipReview,sync:tipSync};
function changed(t){const p=S.prev[t.task];return p&&(p.state!==t.state||p.valid!==t.valid||p.next!==t.next||p.review!==t.review||p.owner!==t.owner)}
function visible(){return D.tasks.filter(t=>S.groups.has(t.group)&&(S.owner==='all'||(S.owner==='free'?['FREE','EXPIRED'].includes(t.claim_health):
 S.owner==='active'?['ACTIVE','OWNED'].includes(t.claim_health):S.owner==='claimed'?t.claim_health==='OWNED':true))&&(!S.q||t.task.includes(S.q.toLowerCase())))}
function renderBoard(){
 const counts={};D.tasks.forEach(t=>counts[t.group]=(counts[t.group]||0)+1);
 document.getElementById('chips').innerHTML=Object.entries(G).map(([g,[c,e,l]])=>`<button class="chip ${S.groups.has(g)?'':'off'}" data-g="${g}"><span class="c" style="background:${c}"></span>${e} ${l} <b>${counts[g]||0}</b></button>`).join('');
 document.getElementById('owner').innerHTML=['all','free','active','claimed'].map(o=>`<button class="${S.owner===o?'on':''}" data-o="${o}">${{all:'👥 all',free:'🔓 free',active:'👀 active',claimed:'👤 claimed'}[o]}</button>`).join('');
 const total=D.tasks.length||1;document.getElementById('bar').innerHTML=Object.entries(G).map(([g,[c]])=>`<span style="flex:${counts[g]||0};background:${c}"></span>`).join('');
 let rows=visible();
 if(S.sort){const key=S.sort,dir=S.dir;const val=t=>key==='state'?(t.state_age_s??0):key==='review'?((t.review==='R2'?2:t.review==='R1'?1:0)*10+(t.confidence||0)):String(t[key]??'');
  const order=['ATTENTION','READY','WAITING','DONE'];rows=[...rows].sort((a,b)=>order.indexOf(a.group)-order.indexOf(b.group)||((val(a)>val(b)?1:val(a)<val(b)?-1:0)*dir))}
 let html='',last=null;rows.forEach((t,i)=>{if(t.group!==last){last=t.group;const[c,e,l]=G[t.group];html+=`<tr class="group"><td colspan="8" style="border-left:4px solid ${c}">${e} ${l} · ${rows.filter(r=>r.group===t.group).length}</td></tr>`}
  html+=`<tr class="row" data-t="${esc(t.task)}" style="--s:${G[t.group][0]};animation-delay:${Math.min(i*12,400)}ms"><td class="task">${changed(t)?'<span class="spark">✦</span> ':''}${esc(t.task)}</td><td data-tip="next">${next(t)}</td><td data-tip="state">${state(t)}</td><td data-tip="owner" class="own">${owner(t)}</td><td data-tip="valid">${valid(t.valid)}</td><td data-tip="check">${check(t)}</td><td data-tip="review">${review(t)}</td><td data-tip="sync">${sync(t.sync)}</td></tr>`});
 document.querySelectorAll('th[data-k]').forEach(th=>th.textContent=th.textContent.replace(/ [▲▼]$/,'')+(S.sort===th.dataset.k?(S.dir>0?' ▲':' ▼'):''));
 document.getElementById('rows').innerHTML=html||'<tr><td colspan="8" class="empty">🌈 nothing matches — try another filter</td></tr>';
 const h=D.health;document.getElementById('health').innerHTML=Object.entries(h).map(([k,v])=>`<span class="${v.ok?'ok':'bad'}">${v.ok?'✔':'✘'} ${k}</span>`).join(' · ')+(D.ledger_ok===null?'':` · <span class="${D.ledger_ok?'ok':'bad'}">${D.ledger_ok?'✔':'✘'} ledger</span>`);
 document.getElementById('dot').className='dot'+(Object.values(h).every(v=>v.ok)?'':' bad');
}
function renderStats(){const w=D.week,f=D.funnel,fl=D.flow,hr=x=>x==null?'—':x>=48?(x/24).toFixed(1)+'d':Math.round(x)+'h';
 const top=Math.max(1,...D.weekly.map(r=>r.accepted));const ftop=Math.max(1,f.built,f.imported);
 const delta=w.this_week-w.same_point_last_week;
 document.getElementById('stats').innerHTML=`<div class="cards">
 <div class="card"><div class="lbl">🏁 accepted this week</div><div class="big ok">${w.this_week}</div><div class="${delta>=0?'ok':'bad'}">${delta>=0?'▲':'▼'} ${Math.abs(delta)} vs last week at this point</div></div>
 <div class="card"><div class="lbl">📅 4-week median</div><div class="big">${w.median_4wk}</div></div>
 <div class="card"><div class="lbl">🔄 submit → accepted</div><div class="big">${hr(fl.latest_round_cycle_p50_h)}</div><div class="dim">p75 ${hr(fl.latest_round_cycle_p75_h)}</div></div>
 <div class="card"><div class="lbl">👀 waiting on reviewer</div><div class="big">${hr(fl.wait_p50_h)}</div><div class="dim">p75 ${hr(fl.wait_p75_h)}</div></div>
 <div class="card"><div class="lbl">🏆 all-time accepted</div><div class="big">${w.total}</div></div></div>
 <div class="panel"><h3>📈 accepted per week <span class="dim">(<span style="color:var(--green)">■</span> multi-turn <span style="color:var(--teal)">■</span> single-turn)</span></h3>
 ${D.weekly.map(r=>`<div class="hbar"><span class="l">${r.week}</span><span class="b" style="width:${r.accepted_mt/top*60}%;background:var(--green)"></span><span class="b" style="width:${r.accepted_st/top*60}%;background:var(--teal);margin-left:-10px"></span><b>${r.accepted}</b><span class="dim">↗ ${r.submitted} submitted · ✎ ${r.worked_on} new</span></div>`).join('')}</div>
 <div class="panel"><h3>🧭 funnel</h3>${[['🧱 built',f.built],['📥 imported',f.imported],['📤 submitted',f.submitted],['✅ accepted',f.accepted]].map(([l,v],i,a)=>`<div class="hbar"><span class="l">${l}</span><span class="b" style="width:${v/ftop*70}%;background:var(--violet)"></span><b>${v}</b>${i?`<span class="dim">${Math.round(100*v/(a[i-1][1]||1))}% of previous</span>`:''}</div>`).join('')}
 <div class="dim">📦 archived ${f.archived} · 🔧 open ${f.open}</div></div>
 <div class="panel"><h3>🕓 open work by state</h3>${Object.entries(D.ages).map(([k,v])=>`<div class="hbar"><span class="l"><span class="pill" style="background:${PILL[k]||'#666'}">${k.replace('_',' ').toLowerCase().replace('needs rev','sent back')}</span></span><span class="b" style="width:${v.count/Math.max(1,...Object.values(D.ages).map(a=>a.count))*55}%;background:${PILL[k]||'#666'}"></span><b>${v.count}</b><span class="dim">typical ${hr(v.median_h)} · oldest ${hr(v.max_h)}</span></div>`).join('')}</div>`}
function summary(t){const parts=[];const st=(t.state||'').replace('_',' ').toLowerCase().replace('needs rev','sent back');
 const rounds=t.decisions.filter(d=>d.kind==='revision').length;
 parts.push(`<b>${esc(st)}</b> for ${age(t.state_age_s)}${rounds?` · round ${rounds+1} (sent back ${rounds}×)`:''}.`);
 const bad=t.validation.filter(v=>v.status==='failed'||v.status==='error');
 if(bad.length)parts.push(`Validation failing on <b>${bad.map(v=>esc(v.name)).join(', ')}</b>${bad[0].detail?': <span class="dim">'+esc(bad[0].detail)+'</span>':''}.`);
 else if(t.valid==='PASS')parts.push('Validation <span class="b-ok">passing</span>.');else if(t.valid==='RUN')parts.push('Validation <span class="b-pend">running</span>.');
 if(t.owner)parts.push(`${t.claim_health==='ACTIVE'?'Being worked on by':t.claim_health==='LEGACY'?'Listed in CLAIMS.md for':'Owned by'} <b>${esc(t.owner)}</b>.`);else parts.push('Nobody owns it.');
 const d=t.decisions[t.decisions.length-1];if(d&&d.kind==='revision'&&d.reason)parts.push(`Last review: <span class="dim">“${esc(d.reason)}”</span>`);
 parts.push(`Next: ${next(t)}.`);return parts.join(' ')}
function openDrawer(name){const t=D.tasks.find(x=>x.task===name);if(!t)return;
 const L=t.links||{};const btn=(k,l)=>L[k]?`<a class="lnk" href="${esc(L[k])}" target="_blank" rel="noopener">${l}</a>`:'';
 document.getElementById('dbody').innerHTML=`<h2>${L.codimango?`<a href="${esc(L.codimango)}" target="_blank" rel="noopener">${esc(t.task)}</a>`:esc(t.task)}</h2><div>${next(t)}</div>
 <div class="links">${btn('codimango','🥭 codimango')}${btn('github','🐙 github (server commit)')}${btn('latest','📂 latest on main')}</div><div class="kv">
 <div>state</div><div>${state(t)}</div><div>owner</div><div>${owner(t)||'—'}</div><div>validation</div><div>${valid(t.valid)}</div>
 <div>presubmit</div><div>${check(t)}</div><div>review</div><div>${review(t)}</div><div>sync</div><div>${sync(t.sync)}</div>
 <div>pushes</div><div>${t.pushes_before_submit||0} before submit · ${t.pushes_after_submit||0} after</div></div>
 <div class="summary">${summary(t)}</div>
 ${t.versions.length?`<h3>🗂 rounds</h3><div class="timeline">${t.versions.map((v,i)=>`${i?'<span class="arrow">→</span>':''}<span class="ver"><b>${v.label}</b> ${v.commits} commit${v.commits===1?'':'s'}${v.ended?` <span class="${v.ended==='accept'?'b-ok':'b-bad'}">${v.ended==='accept'?'✔ accepted':'↩ sent back'}</span> <span class="dim">${fdate(v.at)}</span>`:' <span class="dim">so far</span>'}</span>`).join('')}</div>`:''}
 <h3>✅ validation</h3><ul class="card-list">${t.validation.length?t.validation.map(v=>{const[c,ch]=vb(v.status);return B(c,ch,`<b>${esc(v.name)}</b> <span class="dim">${esc(v.detail)}</span>`)}).join(''):B('b-dim','·','no results yet')}</ul>
 <h3>👥 reviews</h3><ul class="card-list">${tipReview(t).replace(/^<h4>.*?<\/h4><ul>/,'').replace(/<\/ul>$/,'')}</ul>
 <h3>👤 who</h3><ul class="card-list">${tipOwner(t).replace(/^<h4>.*?<\/h4><ul>/,'').replace(/<\/ul>$/,'')}</ul>
 ${(t.active||[]).map(a=>`<div>👀 ${esc(a.alias)} <span class="dim">${age(a.ago_s)} ago</span></div>`).join('')}
 ${t.findings.map(x=>`<div class="finding">⚠ <b>${esc(x.code)}</b> ${esc(x.summary)}<div class="dim">→ ${esc(x.next)}</div></div>`).join('')}
 <p class="dim">terminal: <code>board show ${esc(t.task)}</code></p>`;document.getElementById('drawer').classList.add('open')}
function render(){document.getElementById('week').innerHTML=`📈 W${D.week.week}: <b>${D.week.this_week}</b> accepted · last week at this point ${D.week.same_point_last_week} · 4-week median ${D.week.median_4wk}`;
 document.getElementById('when').textContent=(LIVE?'live · ':'')+'updated '+new Date(D.generated_at).toLocaleTimeString();renderBoard();renderStats()}
document.addEventListener('click',e=>{const g=e.target.closest('[data-g]'),o=e.target.closest('[data-o]'),r=e.target.closest('tr.row'),tb=e.target.closest('[data-tab]'),th=e.target.closest('th[data-k]');
 if(g){S.groups.has(g.dataset.g)?S.groups.delete(g.dataset.g):S.groups.add(g.dataset.g);renderBoard()}
 if(o){S.owner=o.dataset.o;renderBoard()}if(r)openDrawer(r.dataset.t);if(th){const k=th.dataset.k;if(S.sort!==k){S.sort=k;S.dir=1}else if(S.dir>0)S.dir=-1;else S.sort=null;renderBoard()}
 if(tb){document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x===tb));document.getElementById('board').hidden=tb.dataset.tab!=='board';document.getElementById('stats').hidden=tb.dataset.tab!=='stats'}
 if(e.target.id==='close')document.getElementById('drawer').classList.remove('open')});
const tip=document.getElementById('tip');
document.addEventListener('mouseover',e=>{const td=e.target.closest('td[data-tip]');if(!td){tip.classList.remove('on');return}
 const t=D.tasks.find(x=>x.task===td.parentElement.dataset.t);if(!t)return;tip.innerHTML=TIPS[td.dataset.tip](t);tip.classList.add('on')});
document.addEventListener('mousemove',e=>{if(!tip.classList.contains('on'))return;const r=tip.getBoundingClientRect();
 let x=e.clientX+16,y=e.clientY+16;if(x+r.width>innerWidth-8)x=e.clientX-r.width-16;if(y+r.height>innerHeight-8)y=e.clientY-r.height-16;tip.style.left=x+'px';tip.style.top=y+'px'});
document.getElementById('q').addEventListener('input',e=>{S.q=e.target.value;renderBoard()});
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement.id!=='q'){e.preventDefault();document.getElementById('q').focus()}
 if(e.key==='Escape'){document.getElementById('drawer').classList.remove('open');document.getElementById('q').value='';S.q='';renderBoard()}});
window.addEventListener('beforeunload',()=>localStorage.setItem('wb-prev',JSON.stringify(Object.fromEntries(D.tasks.map(t=>[t.task,{state:t.state,valid:t.valid,next:t.next,review:t.review,owner:t.owner}])))));
render();
if(LIVE)setInterval(async()=>{try{const r=await fetch('data.json',{cache:'no-store'});if(r.ok){D=await r.json();render()}}catch(_){document.getElementById('dot').className='dot bad'}},30000);
</script></body></html>
"""


def page(data: dict, live: bool = False) -> str:
    blob = json.dumps(data, default=str).replace("</", "<\\/")
    return PAGE.replace("__DATA__", blob).replace("__LIVE__", "true" if live else "false")


def write(snap, cfg, path: Path) -> Path:
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page(payload(snap, cfg)))
    return path


def serve(gather_fn, cfg, *, port: int = 8765, interval: int = 120, host: str = "127.0.0.1"):
    """Serve the dashboard; data refreshes in the background every `interval` seconds."""
    state = {"data": payload(gather_fn(), cfg), "at": time.time()}
    lock = threading.Lock()

    def refresher():
        while True:
            time.sleep(interval)
            try:
                d = payload(gather_fn(), cfg)
                with lock:
                    state["data"], state["at"] = d, time.time()
            except Exception:
                pass

    threading.Thread(target=refresher, daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            with lock:
                data = state["data"]
            if self.path.startswith("/data.json"):
                body, ctype = json.dumps(data, default=str).encode(), "application/json"
            elif self.path in ("/", "/index.html"):
                body, ctype = page(data, live=True).encode(), "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    srv = ThreadingHTTPServer((host, port), Handler)
    return srv
