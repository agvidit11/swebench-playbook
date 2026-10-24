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


def payload(snap, cfg) -> dict:
    from . import stats as st
    from .tui import _changed_since
    views = []
    for v in snap.views:
        f = dict(v.fields)
        views.append({"task": v.entity_id, **{k: f.get(k) for k in (
            "group", "next", "state", "state_age_s", "age_level", "owner", "claim_health", "valid", "review",
            "confidence", "confidence_stale", "sync", "check", "check_stale", "check_fail", "pushes_before_submit",
            "pushes_after_submit", "track", "active", "dissent")},
            "findings": [{"code": x.code, "severity": x.severity, "summary": x.summary, "next": x.next_action}
                         for x in v.findings]})
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
table{width:100%;border-collapse:separate;border-spacing:0;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
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
aside.open{right:0}aside h2{margin:0 0 8px;font-size:16px;word-break:break-all}aside .x{float:right;cursor:pointer;color:var(--dim)}
aside .kv{display:grid;grid-template-columns:120px 1fr;gap:6px 10px;margin:14px 0}aside .kv div:nth-child(odd){color:var(--dim)}
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
<table><thead><tr><th data-k="task">Task</th><th data-k="next">Next</th><th data-k="state">State</th><th data-k="owner">Owner</th>
<th data-k="valid">Validation</th><th data-k="check">Presubmit</th><th data-k="review">Review</th><th data-k="sync">Sync</th></tr></thead>
<tbody id="rows"></tbody></table>
<div class="legend"><span><span class="spark">✦</span> changed</span><span><span class="ok ticks">✓✓</span> two sessions approved</span>
<span><span class="run">✓</span> one</span><span><span class="dim">↻✓</span> older commit</span><span>▰▰▰▰▱ confidence</span>
<span>👤 owner</span><span>👀 active</span><span>📜 CLAIMS.md</span><span>💤 expired</span><span>🔓 free</span></div>
</section>
<section id="stats" hidden></section>
</div>
<aside id="drawer"><span class="x" id="close">✕ close</span><div id="dbody"></div></aside>
<script id="data" type="application/json">__DATA__</script>
<script>
const LIVE = __LIVE__;
let D = JSON.parse(document.getElementById('data').textContent);
const G = {ATTENTION:['#ff6b6b','🔥','needs you'],READY:['#7bd88f','✨','ready'],WAITING:['#7ab8ff','⏳','waiting'],DONE:['#8b90a0','🎉','done']};
const PILL = {DRAFT:'#e0b860',QUEUE:'#8fb8e0',REVIEW:'#5fafff',NEEDS_REV:'#ff875f',ACCEPTED:'#7bd88f',ARCHIVED:'#808080',NOT_IMPORTED:'#585858'};
const NEXT = {FIX:'🔧',RESOLVE:'🤺',RERUN:'🔁',SUBMIT:'🚀',GET:'👀',RUN:'🧪',WAIT:'⏳',ADDRESS:'📝',IMPORT:'📥',CHECK:'🕐','—':'🎉'};
const S = {groups:new Set(['ATTENTION','READY','WAITING']), owner:'all', q:'', sort:null, prev:JSON.parse(localStorage.getItem('wb-prev')||'{}')};
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
function changed(t){const p=S.prev[t.task];return p&&(p.state!==t.state||p.valid!==t.valid||p.next!==t.next||p.review!==t.review||p.owner!==t.owner)}
function visible(){return D.tasks.filter(t=>S.groups.has(t.group)&&(S.owner==='all'||(S.owner==='free'?['FREE','EXPIRED'].includes(t.claim_health):
 S.owner==='active'?['ACTIVE','OWNED'].includes(t.claim_health):S.owner==='claimed'?t.claim_health==='OWNED':true))&&(!S.q||t.task.includes(S.q.toLowerCase())))}
function renderBoard(){
 const counts={};D.tasks.forEach(t=>counts[t.group]=(counts[t.group]||0)+1);
 document.getElementById('chips').innerHTML=Object.entries(G).map(([g,[c,e,l]])=>`<button class="chip ${S.groups.has(g)?'':'off'}" data-g="${g}"><span class="c" style="background:${c}"></span>${e} ${l} <b>${counts[g]||0}</b></button>`).join('');
 document.getElementById('owner').innerHTML=['all','free','active','claimed'].map(o=>`<button class="${S.owner===o?'on':''}" data-o="${o}">${{all:'👥 all',free:'🔓 free',active:'👀 active',claimed:'👤 claimed'}[o]}</button>`).join('');
 const total=D.tasks.length||1;document.getElementById('bar').innerHTML=Object.entries(G).map(([g,[c]])=>`<span style="flex:${counts[g]||0};background:${c}"></span>`).join('');
 let rows=visible();if(S.sort)rows=[...rows].sort((a,b)=>String(a[S.sort]??'').localeCompare(String(b[S.sort]??'')));
 let html='',last=null;rows.forEach((t,i)=>{if(!S.sort&&t.group!==last){last=t.group;const[c,e,l]=G[t.group];html+=`<tr class="group"><td colspan="8" style="border-left:4px solid ${c}">${e} ${l} · ${rows.filter(r=>r.group===t.group).length}</td></tr>`}
  html+=`<tr class="row" data-t="${esc(t.task)}" style="--s:${G[t.group][0]};animation-delay:${Math.min(i*12,400)}ms"><td class="task">${changed(t)?'<span class="spark">✦</span> ':''}${esc(t.task)}</td><td>${next(t)}</td><td>${state(t)}</td><td>${owner(t)}</td><td>${valid(t.valid)}</td><td>${check(t)}</td><td>${review(t)}</td><td>${sync(t.sync)}</td></tr>`});
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
function openDrawer(name){const t=D.tasks.find(x=>x.task===name);if(!t)return;
 document.getElementById('dbody').innerHTML=`<h2>${esc(t.task)}</h2><div>${next(t)}</div><div class="kv">
 <div>state</div><div>${state(t)}</div><div>owner</div><div>${owner(t)||'—'}</div><div>validation</div><div>${valid(t.valid)}</div>
 <div>presubmit</div><div>${check(t)}</div><div>review</div><div>${review(t)}</div><div>sync</div><div>${sync(t.sync)}</div>
 <div>pushes</div><div>${t.pushes_before_submit||0} before submit · ${t.pushes_after_submit||0} after</div></div>
 ${(t.active||[]).map(a=>`<div>👀 ${esc(a.alias)} <span class="dim">${age(a.ago_s)} ago</span></div>`).join('')}
 ${t.findings.map(x=>`<div class="finding">⚠ <b>${esc(x.code)}</b> ${esc(x.summary)}<div class="dim">→ ${esc(x.next)}</div></div>`).join('')}
 <p class="dim">terminal: <code>board show ${esc(t.task)}</code></p>`;document.getElementById('drawer').classList.add('open')}
function render(){document.getElementById('week').innerHTML=`📈 W${D.week.week}: <b>${D.week.this_week}</b> accepted · last week at this point ${D.week.same_point_last_week} · 4-week median ${D.week.median_4wk}`;
 document.getElementById('when').textContent=(LIVE?'live · ':'')+'updated '+new Date(D.generated_at).toLocaleTimeString();renderBoard();renderStats()}
document.addEventListener('click',e=>{const g=e.target.closest('[data-g]'),o=e.target.closest('[data-o]'),r=e.target.closest('tr.row'),tb=e.target.closest('[data-tab]'),th=e.target.closest('th[data-k]');
 if(g){S.groups.has(g.dataset.g)?S.groups.delete(g.dataset.g):S.groups.add(g.dataset.g);renderBoard()}
 if(o){S.owner=o.dataset.o;renderBoard()}if(r)openDrawer(r.dataset.t);if(th){S.sort=S.sort===th.dataset.k?null:th.dataset.k;renderBoard()}
 if(tb){document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x===tb));document.getElementById('board').hidden=tb.dataset.tab!=='board';document.getElementById('stats').hidden=tb.dataset.tab!=='stats'}
 if(e.target.id==='close')document.getElementById('drawer').classList.remove('open')});
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
