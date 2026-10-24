"""The dashboard page template (CSS + JS inline). Data is injected as JSON by html.page()."""

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧭 workboard</title>
<style>
:root{--bg:#13151b;--panel:#1a1d25;--panel2:#20242e;--line:#2a2e39;--text:#e7e9ef;--dim:#8a8fa0;--pink:#f78fb3;--green:#7bd88f;
--amber:#f5c26b;--red:#ff6b6b;--blue:#7ab8ff;--violet:#b39dff;--teal:#5fd7d7}
*{box-sizing:border-box}html,body{overflow-x:hidden}
body{margin:0;background:radial-gradient(1200px 500px at 10% -10%,#1d1830 0,transparent 60%),var(--bg);color:var(--text);
 font:14px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}
header{padding:22px 28px 6px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.logo{font-size:22px;display:inline-block;animation:float 4s ease-in-out infinite}@keyframes float{50%{transform:translateY(-3px) rotate(-6deg)}}
h1{margin:0;font-size:20px;background:linear-gradient(90deg,var(--pink),var(--violet));-webkit-background-clip:text;color:transparent}
.sub{color:var(--dim);font-style:italic}
.live{display:inline-flex;align-items:center;gap:8px;color:var(--dim);margin-left:auto}
.dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 2.2s infinite}.dot.bad{background:var(--red)}
@keyframes pulse{0%{box-shadow:0 0 0 0 #7bd88f99}70%{box-shadow:0 0 0 9px #7bd88f00}100%{box-shadow:0 0 0 0 #7bd88f00}}
.wrap{padding:0 28px 50px}.week{color:var(--dim);margin:4px 0 10px}.week b{color:var(--green);font-size:16px}
.bar{display:flex;height:5px;border-radius:3px;overflow:hidden;margin:6px 0 16px;position:relative}
.bar span{transition:flex .7s cubic-bezier(.2,.9,.3,1.2)}
.bar::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,#ffffff40,transparent);animation:shimmer 3.5s infinite}
@keyframes shimmer{from{transform:translateX(-100%)}to{transform:translateX(100%)}}
.tabs{display:flex;gap:8px;margin-bottom:12px}
.tab{padding:6px 15px;border-radius:999px;border:1px solid var(--line);cursor:pointer;color:var(--dim);background:none;font:inherit;transition:all .2s}
.tab.on{background:var(--pink);color:#14161c;border-color:var(--pink);font-weight:700}.tab:hover{transform:translateY(-1px)}
.controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.chip{display:inline-flex;align-items:center;gap:7px;padding:5px 12px;border-radius:999px;border:1px solid var(--line);cursor:pointer;
 user-select:none;transition:all .18s;background:var(--panel);color:var(--text);font:inherit}
.chip .c{width:8px;height:8px;border-radius:50%}.chip.off{opacity:.35}.chip:hover{transform:translateY(-2px)}.chip:active{transform:scale(.94)}
.chip .e{display:inline-block;transition:transform .3s}.chip:hover .e{transform:rotate(-12deg) scale(1.2)}
.chip.pop{animation:pop .3s}@keyframes pop{50%{transform:scale(1.12)}}
.sub-chips{display:flex;gap:6px;margin-left:6px;padding-left:10px;border-left:1px dashed var(--line);animation:fadein .25s}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:var(--panel)}
.seg button{background:none;border:0;color:var(--dim);padding:5px 12px;cursor:pointer;font:inherit;transition:background .2s}
.seg button.on{background:var(--violet);color:#14161c;font-weight:700}
input[type=search]{background:var(--panel);border:1px solid var(--line);color:var(--text);padding:6px 12px;border-radius:999px;min-width:230px;font:inherit;transition:border-color .2s}
input[type=search]:focus{outline:0;border-color:var(--pink)}
.health{color:var(--dim);margin-left:auto}.health .ok{color:var(--green)}.health .bad{color:var(--red)}
.tbl{overflow-x:auto;border-radius:14px;border:1px solid var(--line);background:var(--panel)}
table{width:100%;border-collapse:separate;border-spacing:0}
th{text-align:left;color:var(--dim);font-weight:600;padding:10px 10px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--panel);cursor:pointer;white-space:nowrap}
th:hover{color:var(--text)}td{padding:8px 10px;border-bottom:1px solid #22252f;white-space:nowrap}
tr.row{cursor:pointer;animation:rowin .35s ease both}@keyframes rowin{from{opacity:0;transform:translateY(4px)}to{opacity:1}}
tr.row:hover td{background:#232735}tr.row td:first-child{border-left:4px solid var(--s)}
tr.group td{background:#171a21;color:var(--dim);font-weight:700;padding:7px 10px;border-bottom:1px solid var(--line)}
td.task{font-weight:700;max-width:330px;overflow:hidden;text-overflow:ellipsis}td.own{max-width:220px;overflow:hidden;text-overflow:ellipsis}
.spark{color:var(--pink);display:inline-block;animation:twinkle 1.4s ease-in-out infinite}@keyframes twinkle{50%{opacity:.25;transform:scale(.8) rotate(20deg)}}
.tag{display:inline-block;padding:1px 9px;border-radius:7px;color:#14161c;font-weight:700;font-size:12px}
.age{color:var(--dim);margin-left:6px}.age.warn{color:var(--amber)}.age.block{color:var(--red)}
.ok{color:var(--green)}.run{color:var(--amber)}.bad{color:var(--red)}.dim{color:var(--dim)}.info{color:var(--blue)}
.tk{font-weight:800;letter-spacing:-2px}.tk.g{color:var(--green)}.tk.d{color:#5b6070}.tk.a{color:var(--amber)}
.legend{color:var(--dim);margin-top:12px;display:flex;gap:16px;flex-wrap:wrap}
#tip{position:fixed;z-index:60;max-width:420px;background:#0e1016f2;backdrop-filter:blur(4px);border:1px solid var(--line);border-radius:12px;padding:10px 12px;
 box-shadow:0 12px 34px #000b;opacity:0;transform:translateY(6px) scale(.98);transition:opacity .14s,transform .14s;font-size:12.5px;white-space:normal;
 pointer-events:none;user-select:text}
#tip.on{opacity:1;transform:none;pointer-events:auto}#tip h4{margin:0 0 6px;font-size:12px;color:var(--dim);font-weight:600;letter-spacing:.3px}
#tip ul,.lst{margin:0;padding:0;list-style:none}#tip li,.lst li{margin:3px 0;display:flex;gap:8px}
#tip .hint{color:#5b6070;margin-top:6px;font-size:11px}
.b-ok{color:var(--green)}.b-pend{color:var(--amber)}.b-bad{color:var(--red)}.b-info{color:var(--blue)}.b-dim{color:var(--dim)}
td[data-tip],th[data-h],td.task{cursor:help}
aside{position:fixed;top:0;right:0;width:470px;max-width:96vw;height:100%;background:var(--panel);border-left:1px solid var(--line);padding:20px 22px;
 overflow:auto;box-shadow:-14px 0 40px #000a;transform:translateX(105%);transition:transform .38s cubic-bezier(.2,1.1,.3,1)}
.grip{position:absolute;left:0;top:0;width:7px;height:100%;cursor:ew-resize;background:linear-gradient(90deg,#f78fb300,#f78fb300)}
.grip:hover,.grip.drag{background:linear-gradient(90deg,#f78fb366,#f78fb300)}.card-title a{color:var(--text);text-decoration:none;border-bottom:1px dashed #f78fb366}
.card-title a:hover{color:var(--pink)}@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
aside.open{transform:none}aside.wide{width:min(1180px,92vw)}aside.wide #dbody{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
aside.wide #dbody>.head{grid-column:1/-1}aside{transition:transform .38s cubic-bezier(.2,1.1,.3,1),width .3s ease}
aside .xx{position:absolute;top:14px;right:46px;cursor:pointer;color:var(--dim);font-size:16px;transition:transform .2s}aside .xx:hover{transform:scale(1.25);color:var(--pink)}
.team{display:grid;grid-template-columns:minmax(300px,1fr) minmax(360px,1.4fr);gap:14px}.srv{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-bottom:10px;background:var(--panel)}
.srv h3{margin:0 0 6px;font-size:14px}.srv .live{margin:0}.badge{display:inline-block;padding:0 7px;border-radius:6px;font-size:11.5px;font-weight:700;color:#14161c}
.feed{max-height:70vh;overflow:auto}.fi{display:grid;grid-template-columns:52px 64px 1fr;gap:8px;padding:6px 4px;border-bottom:1px solid #22252f;animation:rowin .3s ease both}
.fi .t{color:var(--dim)}.fi .w{color:var(--dim);font-size:12px}.msg{border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin:6px 0;background:#181b22;animation:up .3s ease}
.msg .meta{color:var(--dim);font-size:12px}.msg.me{border-color:#f78fb355}.compose{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.compose select,.compose input,.compose textarea{background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:10px;padding:7px 10px;font:inherit}
.compose textarea{flex:1 1 100%;min-height:60px}.sent{color:var(--green);animation:fadein .3s}aside .x{position:absolute;top:14px;right:18px;cursor:pointer;color:var(--dim);font-size:16px;transition:transform .2s}
aside .x:hover{transform:rotate(90deg);color:var(--pink)}
.card-title{font-size:16px;font-weight:800;word-break:break-all;padding-right:34px;margin:0}
.kind{color:var(--dim);margin:4px 0 10px}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 14px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:7px 13px;border-radius:10px;background:var(--panel2);border:1px solid var(--line);color:var(--text);
 text-decoration:none;font-weight:700;transition:all .18s}.btn:hover{border-color:var(--pink);color:var(--pink);transform:translateY(-2px)}
.btn.primary{background:linear-gradient(135deg,#f78fb333,#b39dff33);border-color:#f78fb366}
.sec{background:#181b22;border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0;opacity:0;animation:up .4s ease forwards}
.sec h3{margin:0 0 8px;font-size:12.5px;color:var(--dim);font-weight:700;letter-spacing:.3px}
aside.open .sec:nth-child(1){animation-delay:.05s}aside.open .sec:nth-child(2){animation-delay:.1s}aside.open .sec:nth-child(3){animation-delay:.15s}
aside.open .sec:nth-child(4){animation-delay:.2s}aside.open .sec:nth-child(5){animation-delay:.25s}aside.open .sec:nth-child(6){animation-delay:.3s}
@keyframes up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}@keyframes fadein{from{opacity:0}to{opacity:1}}
.next-sec{border-color:#f78fb355;background:linear-gradient(180deg,#f78fb314,#181b22)}
.step{display:flex;gap:10px;align-items:baseline;margin:5px 0}.step .n{width:20px;height:20px;border-radius:50%;background:var(--pink);color:#14161c;
 font-weight:800;font-size:11px;display:inline-flex;align-items:center;justify-content:center;flex:none}.step .eta{margin-left:auto;color:var(--amber);white-space:nowrap}
.who{margin-top:8px;color:var(--violet)}
.timeline{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.ver{border:1px solid var(--line);border-radius:8px;padding:3px 9px;background:var(--panel2)}
.ver b{color:var(--pink)}.arrow{color:var(--dim)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-bottom:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;transition:transform .2s}.card:hover{transform:translateY(-3px)}
.card .big{font-size:26px;font-weight:800}.card .lbl{color:var(--dim)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:14px}.panel h3{margin:0 0 10px;font-size:14px}
.hbar{display:flex;align-items:center;gap:10px;margin:5px 0}.hbar .l{width:120px;color:var(--dim)}
.hbar .b{height:14px;border-radius:4px;transition:width .8s cubic-bezier(.2,.9,.3,1.1)}.empty{color:var(--dim);padding:30px;text-align:center}
code{background:#0e1016;border:1px solid var(--line);border-radius:5px;padding:0 4px}
</style></head><body>
<header><span class="logo">🧭</span><h1>workboard</h1><span class="sub">your tasks across every server and session</span>
<span class="live"><span class="dot" id="dot"></span><span id="when"></span></span></header>
<div class="wrap">
<div class="week" id="week"></div><div class="bar" id="bar"></div>
<div class="tabs"><button class="tab on" data-tab="board">📋 Board</button><button class="tab" data-tab="team">💬 Team</button><button class="tab" data-tab="stats">📊 Stats</button></div>
<section id="board">
<div class="controls" id="chips"></div>
<div class="controls"><div class="seg" id="owner"></div><input type="search" id="q" placeholder="🔍 search tasks  ( / )"><span class="health" id="health"></span></div>
<div class="tbl"><table><thead><tr>
<th data-k="task" data-h="task">Task</th><th data-k="next" data-h="next">Next</th><th data-k="tag" data-h="tag">Status</th>
<th data-k="owner" data-h="owner">Owner</th><th data-k="valid" data-h="valid">Validation</th><th data-k="review" data-h="review">Review</th>
<th data-k="check" data-h="check">Presubmit</th><th data-k="sync" data-h="sync">Server</th></tr></thead><tbody id="rows"></tbody></table></div>
<div class="legend"><span><span class="spark">✦</span> changed</span><span><span class="tk g">✓✓</span> done</span><span><span class="tk d">✓✓</span> not yet</span>
<span><span class="tk g">✓</span><span class="tk d">✓</span> half-way</span><span>👤 owner · 👀 active · 📜 CLAIMS.md · 🔓 free</span><span class="dim">hover anything for details · click a task for its card</span></div>
</section>
<section id="team" hidden></section>
<section id="stats" hidden></section>
</div>
<div id="tip"></div>
<aside id="drawer"><div class="grip" id="grip" title="drag to resize"></div><span class="x" id="close" title="close (esc)">✕</span><span class="xx" id="expand" title="expand (e)">⤢</span><div id="dbody"></div></aside>
<script id="data" type="application/json">__DATA__</script>
<script>
const LIVE = __LIVE__;
let D = JSON.parse(document.getElementById('data').textContent);
const G = {ATTENTION:['#ff6b6b','🔥','needs you'],READY:['#7bd88f','✨','ready'],VALIDATING:['#7ab8ff','⏳','validating'],
 REVIEWING:['#b39dff','👀','with reviewers'],DONE:['#8b90a0','🎉','done']};
const TAGC = {'Draft':'#e0b860','Sent back':'#ff875f','Needs reviewers':'#8fb8e0','In review':'#5fafff','Accepted':'#7bd88f','In training':'#5fd7d7',
 'Archived':'#808080','Not imported':'#585858'};
const NEXT = {FIX:'🔧',RESOLVE:'🤺',RERUN:'🔁',SUBMIT:'🚀',GET:'👀',RUN:'🧪',WAIT:'⏳',ADDRESS:'📝',IMPORT:'📥','—':'🎉'};
const HEAD = {task:'The task folder. Hover a task name for what it is; click for its card with next steps.',
 next:'What to do next, worked out from validation, reviews, sync and ownership. Hover for why.',
 tag:'Status in codimango: Draft, Sent back, Needs reviewers, In review, Accepted, In training, Archived — plus how long it has been there.',
 owner:'Who is on it: 👤 claimed · 👀 a session touched it recently · 📜 listed in CLAIMS.md · 🔓 nobody.',
 valid:'codimango validation. Hover shows only the problems and how to fix them.',
 review:'Human review in codimango: ✔ accepted · ✘ sent back (n times) · 👀 in review · ⌛ waiting for a reviewer · · not submitted. Hover for the last decision.',
 check:'Pre-submit gate (board check run / record). ✔ clean on this commit · ✘ failures · grey = old or not run. Hover shows what the session suggested fixing.',
 sync:'Server verdict on your latest push: ✔ validated clean · ✘ validation failed or sent back · ⏳ grey = importing / validating · ▲ amber = server validated an older commit.'};
const S = {tags:new Set(), groups:new Set(['ATTENTION','READY','VALIDATING','REVIEWING']), done:new Set(['accepted','in_training','archived']), owner:'all', q:'', sort:null, dir:1,
 prev:JSON.parse(localStorage.getItem('wb-prev')||'{}')};
const esc = s => String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const age = s => s==null?'?':s<60?'<1m':s<3600?Math.floor(s/60)+'m':s<86400?Math.floor(s/3600)+'h':Math.floor(s/86400)+'d';
const fdate = x => x?new Date(x).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'—';
const L = (cls,ch,txt) => `<li><span class="b-${cls}">${ch}</span><span>${txt}</span></li>`;
const CH = {ok:'●',pend:'○',bad:'✘',dim:'·',info:'→'};
const tick = (n,green,amber) => n?`<span class="tk ${green?'g':amber?'a':'d'}">${'✓'.repeat(n)}</span>`:'<span class="tk d">✓✓</span>';
function kindLine(t){const c=t.category||{};const track=(t.track||'').includes('multi')?'multi-turn':(t.track?'single-turn':'');
 return [track&&('SWE-bench '+track), (c.category||'').replace(/_/g,' '), (c.subdomain||'').replace(/_/g,' '), (c.languages||[]).join('/'), c.difficulty].filter(Boolean).join(' · ')}
function owner(t){const h=t.claim_health,o=esc(t.owner);if(h==='DONE')return'';if(h==='FREE'||!t.owner)return'<span class="info">🔓 free</span>';
 if(h==='ACTIVE')return`<span class="run">👀 ${o}</span> <span class="dim">${age((t.active||[{}])[0].ago_s)}</span>`;
 if(h==='CONFLICT')return`<span class="bad">🤺 ${o}</span>`;if(h==='EXPIRED')return`<span class="dim">💤 ${o}</span>`;
 if(h==='LEGACY')return`<span class="dim">📜 ${o}</span>`;return`<span style="color:var(--violet)">👤 ${o}</span>`}
function valid(t){const v=t.vsum;const f=v.issues.filter(i=>i.severity==='fail').length,w=v.issues.filter(i=>i.severity==='warn').length;
 if(t.valid==='RUN')return'<span class="run">○ running</span>';if(!v.total)return'<span class="dim">· none yet</span>';
 if(f)return`<span class="bad">✘ ${f} issue${f>1?'s':''}</span>`;if(w)return`<span class="run">▲ ${w} warning${w>1?'s':''}</span>`;return'<span class="ok">✔ clean</span>'}
function review(t){const raw=t.status_raw,n=t.decisions.filter(d=>d.kind==='revision').length;
 if(raw==='accepted')return'<span class="ok">✔ accepted</span>';if(raw==='used_in_training')return'<span style="color:var(--teal)">✔ in training</span>';
 if(raw==='needs_revision')return`<span class="bad">✘ sent back${n>1?' '+n+'×':''}</span>`;if(raw==='being_reviewed')return'<span style="color:var(--violet)">👀 in review</span>';
 if(raw==='needs_reviewers_assigned')return'<span class="info">⌛ awaiting reviewer</span>';if(raw==='archived')return'<span class="dim">📦 archived</span>';
 return n?`<span class="dim">· draft (↩${n}×)</span>`:'<span class="dim">· not submitted</span>'}
function check(t){const c=t.last_check;if(!c)return'<span class="dim">· not run</span>';
 if(c.fail)return`<span class="bad">✘ ${c.fail}</span>`;return c.current?`<span class="ok">✔</span>${c.warn?' <span class="run">▲'+c.warn+'</span>':''}`:'<span class="dim">↻ old</span>'}
function sync(t){if(t.sync==='IMPORTING'||t.valid==='RUN')return'<span class="dim">⏳</span>';
 if(t.sync==='STALE_VALID'||t.sync==='HEAD≠SERVER')return'<span class="run">▲</span>';
 if(t.valid==='FAIL'||t.status_raw==='needs_revision')return'<span class="bad">✘</span>';
 if(t.valid==='PASS')return'<span class="ok">✔</span>';return'<span class="dim">·</span>'}
function next(t){const n=t.next||'',e=NEXT[n.split(' ')[0]]||'•';const col=n.startsWith('FIX')||n.startsWith('RESOLVE')?'var(--red)':n.startsWith('SUBMIT')?'var(--green)':n.startsWith('WAIT')?'var(--dim)':'var(--amber)';
 return `${e} <span style="color:${col}">${esc(n)}</span>`}
function tag(t){return `<span class="tag" style="background:${TAGC[t.tag]||'#666'}">${esc(t.tag)}</span><span class="age ${t.age_level||''}">${age(t.state_age_s)}</span>`}
// ---- hover cards: short, only what matters
function tipTask(t){return `<h4>${esc(t.task)}</h4><ul>${L('info','◆',esc(kindLine(t)||'no category yet'))}${t.category&&t.category.domain?L('dim','·',esc(t.category.domain)):''}${t.category&&t.category.usecase?L('dim','·',esc(t.category.usecase.replace(/_/g,' '))):''}</ul>`}
function tipNext(t){return `<h4>next · ETA</h4><ul>${t.steps.map(s=>L('pend','→',`${esc(s.do)} <span class="dim">${esc(s.eta)}</span>`)).join('')||L('ok','●','nothing to do')}</ul>`}
function tipTag(t){let h=`<h4>${esc(t.tag)} for ${age(t.state_age_s)}</h4><ul>`;if(t.entered_pool_at)h+=L('dim','↗','submitted '+fdate(t.entered_pool_at));
 t.decisions.slice(-3).forEach(d=>h+=L(d.kind==='accept'?'ok':'bad',d.kind==='accept'?'✔':'↩',(d.kind==='accept'?'accepted ':'sent back ')+fdate(d.at)));
 if(t.age_level&&t.age_level!=='ok')h+=L(t.age_level==='block'?'bad':'pend','!',t.age_level==='block'?'overdue for this state':'getting old');return h+'</ul>'}
function tipOwner(t){let h='<h4>who</h4><ul>';(t.active||[]).slice(0,3).forEach(a=>h+=L('pend','👀',`${esc(a.alias)} · ${age(a.ago_s)} ago`));
 if(t.claim_health==='OWNED')h+=L('ok','👤','claimed by '+esc(t.owner));if(t.legacy&&t.legacy.live!==false)h+=L('info','📜',`${esc(t.legacy.legacy_owner)} · ${esc(t.legacy.status)} · ${esc(t.legacy.updated)}`);
 if(t.claim_health==='FREE')h+=L('info','🔓','nobody');h+=L('dim','→',esc(t.assignee));return h+'</ul>'}
function tipValid(t){const v=t.vsum;if(t.valid==='RUN'&&!v.issues.length)return'<h4>validation</h4><ul>'+L('pend','○','running')+'</ul>';
 if(!v.issues.length)return`<h4>validation</h4><ul>${L('ok','●',`all ${v.total} checks passed`)}</ul>`;
 return `<h4>validation · ${v.passed}/${v.total} passed</h4><ul>${v.issues.map(i=>L(i.severity==='fail'?'bad':'pend',i.severity==='fail'?'✘':'▲',`<b>${esc(i.check)}</b> ${esc(i.why)}<br><span class="dim">→ ${esc(i.fix)}</span>`)).join('')}</ul>`}
function tipReview(t){let h=`<h4>human review · ${esc(t.rsum.human)}</h4><ul>`;
 t.decisions.slice(-3).forEach(d=>h+=L(d.kind==='accept'?'ok':'bad',d.kind==='accept'?'✔':'↩',`${d.kind==='accept'?'accepted':'sent back'} ${fdate(d.at)}`));
 const d=t.decisions[t.decisions.length-1];if(d&&d.reason)h+=L('dim','“',esc(d.reason.slice(0,140)));
 if(t.entered_pool_at&&!t.decisions.length)h+=L('info','⌛','submitted '+fdate(t.entered_pool_at)+', no decision yet');
 if(!t.entered_pool_at)h+=L('dim','·','not submitted yet');
 const ar=t.agent_reviews||[];if(ar.length)h+=L('dim','🤖',`${ar.length} agent-session check${ar.length>1?'s':''} (optional second opinion)`);return h+'</ul>'}
function tipCheck(t){const c=t.last_check;if(!c)return'<h4>presubmit</h4><ul>'+L('pend','○','not run')+L('info','→','board check run '+esc(t.task))+'</ul>';
 return `<h4>presubmit · ${fdate(c.at)}</h4><ul>${c.fail?L('bad','✘',c.fail+' failure(s)'):L('ok','●','clean')}${c.warn?L('pend','▲',c.warn+' warning(s)'):''}${c.current?'':L('pend','↻','ran on an older commit — re-run')}${c.summary?L('info','💡','suggested: '+esc(c.summary)):''}</ul>`}
function tipSync(t){const s=t.sync;let h='<h4>server</h4><ul>';
 if(t.valid==='FAIL'){const i=t.vsum.issues.filter(x=>x.severity==='fail');h+=L('bad','✘','validation failed'+(i.length?': '+esc(i.map(x=>x.check).join(', ')):''))}
 if(t.status_raw==='needs_revision')h+=L('bad','✘','sent back by the reviewer');if(t.valid==='RUN')h+=L('dim','⏳','validating now');
 if(s==='OK'||s==='OK·doc')h+=L('ok','●','server has your latest commit')+L(t.validated?'ok':'pend',t.validated?'●':'○',t.validated?'and validated it':'validation running');
 else if(s==='IMPORTING')h+=L('info','⏳','your push is being imported (a few minutes)');
 else if(s==='STALE_VALID')h+=L('pend','▲','validated an older commit; code changed since')+L('info','→','codimango task rerun');
 else if(s==='HEAD≠SERVER')h+=L('pend','▲',(t.findings.find(f=>f.code==='HEAD≠SERVER')||{}).summary||'latest push not on server')+L('info','→','rerun if it does not catch up');
 else h+=L('dim','·','not compared');return h+'</ul>'}
const TIPS={task:tipTask,next:tipNext,tag:tipTag,owner:tipOwner,valid:tipValid,review:tipReview,check:tipCheck,sync:tipSync};
function changed(t){const p=S.prev[t.task];return p&&(p.tag!==t.tag||p.valid!==t.valid||p.next!==t.next||p.review!==t.review||p.owner!==t.owner)}
function visible(){return D.tasks.filter(t=>S.groups.has(t.group)&&(!S.tags.size||S.tags.has(t.tag))&&(t.group!=='DONE'||S.done.has(t.done_kind)||(t.done_kind==='in_training'&&S.done.has('accepted')))&&
 (S.owner==='all'||(S.owner==='free'?['FREE','EXPIRED'].includes(t.claim_health):S.owner==='active'?['ACTIVE','OWNED'].includes(t.claim_health):S.owner==='claimed'?['OWNED','LEGACY'].includes(t.claim_health):true))&&
 (!S.q||t.task.includes(S.q.toLowerCase())))}
function renderBoard(){const counts={};D.tasks.forEach(t=>counts[t.group]=(counts[t.group]||0)+1);
 const dc={accepted:0,in_training:0,archived:0};D.tasks.forEach(t=>{if(t.done_kind)dc[t.done_kind]++});
 let chips=Object.entries(G).map(([g,[c,e,l]])=>`<button class="chip ${S.groups.has(g)?'':'off'}" data-g="${g}"><span class="c" style="background:${c}"></span><span class="e">${e}</span> ${l} <b>${counts[g]||0}</b></button>`).join('');
 if(S.groups.has('DONE'))chips+=`<span class="sub-chips">${[['accepted','✅','accepted',dc.accepted+dc.in_training],['in_training','🧠','in training',dc.in_training],['archived','📦','archived',dc.archived]].map(([k,e,l,n])=>`<button class="chip ${S.done.has(k)?'':'off'}" data-d="${k}"><span class="e">${e}</span> ${l} <b>${n}</b></button>`).join('')}</span>`;
 const inGroups=D.tasks.filter(t=>S.groups.has(t.group)&&(t.group!=='DONE'||S.done.has(t.done_kind)||(t.done_kind==='in_training'&&S.done.has('accepted'))));
 const tagc={};inGroups.forEach(t=>tagc[t.tag]=(tagc[t.tag]||0)+1);[...S.tags].forEach(x=>{if(!tagc[x])S.tags.delete(x)});
 chips+=`<span class="sub-chips"><span class="dim">status:</span>${Object.entries(tagc).sort((a,b)=>b[1]-a[1]).map(([k,n])=>`<button class="chip ${!S.tags.size||S.tags.has(k)?'':'off'}" data-tagf="${esc(k)}"><span class="c" style="background:${TAGC[k]||'#666'}"></span>${esc(k)} <b>${n}</b></button>`).join('')}${S.tags.size?'<button class="chip" data-tagf="">✕ all</button>':''}</span>`;
 document.getElementById('chips').innerHTML=chips;
 document.getElementById('owner').innerHTML=['all','free','active','claimed'].map(o=>`<button class="${S.owner===o?'on':''}" data-o="${o}">${{all:'👥 all',free:'🔓 free',active:'👀 active',claimed:'👤 claimed'}[o]}</button>`).join('');
 document.getElementById('bar').innerHTML=Object.entries(G).map(([g,[c]])=>`<span style="flex:${counts[g]||0};background:${c}"></span>`).join('');
 let rows=visible();const order=Object.keys(G);
 if(S.sort){const k=S.sort;const val=t=>k==='tag'?(t.state_age_s??0):k==='review'?t.rsum.agent.length:k==='valid'?t.vsum.issues.length:String(t[k]??'');
  rows=[...rows].sort((a,b)=>order.indexOf(a.group)-order.indexOf(b.group)||((val(a)>val(b)?1:val(a)<val(b)?-1:0)*S.dir))}
 let html='',last=null;rows.forEach((t,i)=>{if(t.group!==last){last=t.group;const[c,e,l]=G[t.group];html+=`<tr class="group"><td colspan="8" style="border-left:4px solid ${c}">${e} ${l} · ${rows.filter(r=>r.group===t.group).length}</td></tr>`}
  html+=`<tr class="row" data-t="${esc(t.task)}" style="--s:${G[t.group][0]};animation-delay:${Math.min(i*10,350)}ms"><td class="task" data-tip="task">${changed(t)?'<span class="spark">✦</span> ':''}${esc(t.task)}</td>
  <td data-tip="next">${next(t)}</td><td data-tip="tag">${tag(t)}</td><td data-tip="owner" class="own">${owner(t)}</td><td data-tip="valid">${valid(t)}</td>
  <td data-tip="review">${review(t)}</td><td data-tip="check">${check(t)}</td><td data-tip="sync">${sync(t)}</td></tr>`});
 document.getElementById('rows').innerHTML=html||'<tr><td colspan="8" class="empty">🌈 nothing matches — try another filter</td></tr>';
 document.querySelectorAll('th[data-k]').forEach(th=>{th.textContent=th.textContent.replace(/ [▲▼]$/,'')+(S.sort===th.dataset.k?(S.dir>0?' ▲':' ▼'):'')});
 const h=D.health;document.getElementById('health').innerHTML=Object.entries(h).map(([k,v])=>`<span class="${v.ok?'ok':'bad'}">${v.ok?'✔':'✘'} ${k}</span>`).join(' · ')+(D.ledger_ok===null?'':` · <span class="${D.ledger_ok?'ok':'bad'}">${D.ledger_ok?'✔':'✘'} ledger</span>`);
 const stale=D.codimango_at&&(Date.now()-new Date(D.codimango_at))/1000>600;
 document.getElementById('dot').className='dot'+(Object.values(h).every(v=>v.ok)&&!D.refresh_error&&!stale&&D.ledger_ok!==false?'':' bad');
 if(D.refresh_error)document.getElementById('health').innerHTML+=` · <span class="bad">refresh failing: ${esc(D.refresh_error)}</span>`}
function countUp(el){const end=parseFloat(el.dataset.n);if(isNaN(end))return;let s=null;const step=ts=>{s=s||ts;const p=Math.min(1,(ts-s)/700);el.textContent=(end%1?(end*p).toFixed(1):Math.round(end*p));if(p<1)requestAnimationFrame(step)};requestAnimationFrame(step)}
function renderStats(){const w=D.week,f=D.funnel,fl=D.flow,hr=x=>x==null?'—':x>=48?(x/24).toFixed(1)+'d':Math.round(x)+'h';
 const top=Math.max(1,...D.weekly.map(r=>r.accepted));const ftop=Math.max(1,f.built,f.imported);const delta=w.this_week-w.same_point_last_week;
 document.getElementById('stats').innerHTML=`<div class="cards">
 <div class="card"><div class="lbl">🏁 accepted this week</div><div class="big ok" data-n="${w.this_week}">${w.this_week}</div><div class="${delta>=0?'ok':'bad'}">${delta>=0?'▲':'▼'} ${Math.abs(delta)} vs last week at this point</div></div>
 <div class="card"><div class="lbl">📅 4-week median</div><div class="big" data-n="${w.median_4wk}">${w.median_4wk}</div></div>
 <div class="card"><div class="lbl">🔄 submit → accepted</div><div class="big">${hr(fl.latest_round_cycle_p50_h)}</div><div class="dim">p75 ${hr(fl.latest_round_cycle_p75_h)}</div></div>
 <div class="card"><div class="lbl">👀 waiting on reviewer</div><div class="big">${hr(fl.wait_p50_h)}</div><div class="dim">p75 ${hr(fl.wait_p75_h)}</div></div>
 <div class="card"><div class="lbl">🏆 all-time accepted</div><div class="big" data-n="${w.total}">${w.total}</div></div></div>
 <div class="panel"><h3>📈 accepted per week <span class="dim">(<span class="ok">■</span> multi-turn <span style="color:var(--teal)">■</span> single-turn)</span></h3>
 ${D.weekly.map(r=>`<div class="hbar"><span class="l">${r.week}</span><span class="b" style="width:${r.accepted_mt/top*60}%;background:var(--green)"></span><span class="b" style="width:${r.accepted_st/top*60}%;background:var(--teal);margin-left:-10px"></span><b>${r.accepted}</b><span class="dim">↗ ${r.submitted} submitted · ✎ ${r.worked_on} new</span></div>`).join('')}</div>
 <div class="panel"><h3>🧭 funnel</h3>${[['🧱 built',f.built],['📥 imported',f.imported],['📤 submitted',f.submitted],['✅ accepted',f.accepted]].map(([l,v],i,a)=>`<div class="hbar"><span class="l">${l}</span><span class="b" style="width:${v/ftop*70}%;background:var(--violet)"></span><b>${v}</b>${i?`<span class="dim">${Math.round(100*v/(a[i-1][1]||1))}% of previous</span>`:''}</div>`).join('')}
 <div class="dim">📦 archived ${f.archived} · 🔧 open ${f.open}</div></div>`;document.querySelectorAll('#stats [data-n]').forEach(countUp)}
function openDrawer(name){const t=D.tasks.find(x=>x.task===name);if(!t)return;const Lk=t.links||{};
 const btn=(k,l,p)=>Lk[k]?`<a class="btn ${p?'primary':''}" href="${esc(Lk[k])}" target="_blank" rel="noopener">${l} ↗</a>`:'';
 const v=t.vsum;
 document.getElementById('dbody').innerHTML=`<div class="head"><p class="card-title">${Lk.codimango?`<a href="${esc(Lk.codimango)}" target="_blank" rel="noopener" title="open in codimango">${esc(t.task)} ↗</a>`:esc(t.task)}</p><div class="kind">${esc(kindLine(t))}</div>
 <div>${tag(t)} &nbsp; ${next(t)}</div>
 <div class="btns">${btn('codimango','🥭 Open in codimango',1)}${btn('github','🐙 Files at server commit')}${btn('latest','📂 Latest on main')}
 <button class="btn" data-msgtask="${esc(t.task)}">💬 Message the owner</button></div></div>
 <div class="sec next-sec"><h3>🚀 NEXT STEPS</h3>${t.steps.map((s,i)=>`<div class="step"><span class="n">${i+1}</span><span>${esc(s.do)}</span><span class="eta">${esc(s.eta)}</span></div>`).join('')||'<div class="dim">nothing to do 🎉</div>'}
  <div class="who">👤 ${esc(t.assignee)}</div></div>
 ${v.issues.length?`<div class="sec"><h3>⚠️ PROBLEMS · ${v.passed}/${v.total} checks passed</h3><ul class="lst">${v.issues.map(i=>L(i.severity==='fail'?'bad':'pend',i.severity==='fail'?'✘':'▲',`<b>${esc(i.check)}</b> ${esc(i.why)} <span class="dim">→ ${esc(i.fix)}</span>`)).join('')}</ul></div>`:''}
 <div class="sec"><h3>👥 REVIEW</h3><ul class="lst">${t.rsum.bullets.map(([k,x])=>L(k,CH[k],esc(x))).join('')}</ul>
  ${t.decisions.length&&t.decisions[t.decisions.length-1].reason?`<div class="dim" style="margin-top:6px">last review: “${esc(t.decisions[t.decisions.length-1].reason)}”</div>`:''}</div>
 ${t.versions.length?`<div class="sec"><h3>🗂 ROUNDS</h3><div class="timeline">${t.versions.map((x,i)=>`${i?'<span class="arrow">→</span>':''}<span class="ver"><b>${x.label}</b> ${x.commits} commit${x.commits===1?'':'s'}${x.ended?` <span class="${x.ended==='accept'?'b-ok':'b-bad'}">${x.ended==='accept'?'✔':'↩'}</span> <span class="dim">${fdate(x.at)}</span>`:' <span class="dim">so far</span>'}</span>`).join('')}</div></div>`:''}
 ${t.last_check?`<div class="sec"><h3>🧪 PRESUBMIT</h3><ul class="lst">${tipCheck(t).replace(/^<h4>.*?<\/h4><ul>|<\/ul>$/g,'')}</ul></div>`:''}
 <div class="sec"><h3>🔗 WHO & SERVER</h3><ul class="lst">${tipOwner(t).replace(/^<h4>.*?<\/h4><ul>|<\/ul>$/g,'')}${tipSync(t).replace(/^<h4>.*?<\/h4><ul>|<\/ul>$/g,'')}</ul></div>
 <div class="dim" style="margin-top:10px">terminal: <code>board show ${esc(t.task)}</code></div>`;
 const d=document.getElementById('drawer');d.classList.remove('open');d.classList.toggle('wide',!!localStorage.getItem('wb-wide'));void d.offsetWidth;d.classList.add('open')}
const HC={};const hostColor=h=>HC[h]||(HC[h]=['#f78fb3','#7ab8ff','#7bd88f','#f5c26b','#b39dff'][Object.keys(HC).length%5]);
function renderTeam(){const me=localStorage.getItem('wb-to')||'all';
 const srv=(D.servers||[]).map(s=>`<div class="srv"><h3><span class="badge" style="background:${hostColor(s.id)}">${esc(s.id)}</span> server
  <span class="dim">· last sync ${s.last_sync_ago_s==null?'never':age(s.last_sync_ago_s)+' ago'}</span>
  <span class="${s.last_sync_ago_s!=null&&s.last_sync_ago_s<600?'ok':'bad'}">${s.last_sync_ago_s!=null&&s.last_sync_ago_s<600?'● online':'● quiet'}</span></h3>
  <div class="dim">${s.sessions.length} active session(s) · owns/working on ${s.owned.length} task(s)</div>
  <ul class="lst">${s.sessions.map(x=>L('pend','✍️',`${esc(x.alias.split('·').slice(1).join('·')||x.alias)} <span class="dim">${age(x.ago_s)} ago</span>`)).join('')||L('dim','·','no active sessions in the last 2h')}</ul></div>`).join('');
 const msgs=(D.messages||[]).slice(-30).reverse().map(m=>`<div class="msg ${m.from.includes('dashboard')?'me':''}"><div class="meta">${esc(m.from)} → <b>${esc(m.to_label)}</b>${m.task?' · '+esc(m.task):''} · ${fdate(m.at)}
  ${m.acked_by.length?' · <span class="ok">✓ read by '+m.acked_by.length+'</span>':' · <span class="run">unread</span>'}</div><div>${esc(m.text)}</div></div>`).join('')||'<div class="dim">no messages yet</div>';
 const opts=['all',...(D.servers||[]).map(s=>s.id),...(D.sessions||[])];
 const feed=(D.feed||[]).map((f,i)=>`<div class="fi" style="animation-delay:${Math.min(i*8,300)}ms"><span class="t">${new Date(f.at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</span>
  <span><span class="badge" style="background:${hostColor(f.host)}">${esc(f.host)}</span></span><span>${esc(f.what)} ${f.task?'<b>'+esc(f.task)+'</b>':''}<div class="w">${esc(f.who)}</div></span></div>`).join('')||'<div class="dim">quiet</div>';
 document.getElementById('team').innerHTML=`<div class="team"><div>${srv}
  <div class="panel"><h3>💬 send a message</h3>
  <div class="dim" style="margin-bottom:6px">How it travels: saved to the shared private ledger → the target server picks it up on its next sync (≤2 min) →
  the hook shows it inside the target Claude session on its next step → the session acks/replies with <code>board ack</code> / <code>board msg</code>.
  Pick a server to reach every session there, or "everyone".</div>
  <div class="compose"><select id="mto">${opts.map(o=>`<option ${o===me?'selected':''} value="${esc(o)}">${o==='all'?'📣 everyone':/^[0-9a-z]+$/.test(o)&&(D.servers||[]).some(s=>s.id===o)?'🖥 server '+esc(o):'👤 '+esc(o)}</option>`).join('')}</select>
  <input id="mtask" placeholder="task (optional)" size="28"><textarea id="mtext" placeholder="e.g. please pick up pgmem after you finish, I'm on vobject"></textarea>
  <button class="btn primary" id="msend">Send 🚀</button><span id="mstatus"></span></div></div>
  <div class="panel"><h3>📨 messages</h3>${msgs}</div></div>
  <div class="panel feed"><h3>🕒 activity across servers (24h)</h3>${feed}</div></div>`}
async function sendMsg(){const to=document.getElementById('mto').value,text=document.getElementById('mtext').value,task=document.getElementById('mtask').value;
 const st=document.getElementById('mstatus');if(!LIVE){st.innerHTML='<span class="bad">sending needs the live page (board serve)</span>';return}
 st.textContent='sending…';localStorage.setItem('wb-to',to);
 try{const r=await fetch('api/msg',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({to,text,task})});const j=await r.json();
  st.innerHTML=j.ok?`<span class="sent">✓ in the ledger for ${esc(j.to)}${j.synced?' — they see it within ~2 min':' (queued, publishes on next sync)'}</span>`:`<span class="bad">${esc(j.error)}</span>`;
  if(j.ok){document.getElementById('mtext').value='';const d=await (await fetch('data.json',{cache:'no-store'})).json();D=d;renderTeam()}}catch(e){st.innerHTML='<span class="bad">failed</span>'}}
function render(){const W=D.week;document.getElementById('week').innerHTML=`📈 W${W.week}: <b>${W.this_week}</b> accepted · last week at this point ${W.same_point_last_week} · 4-week median ${W.median_4wk}`;
 const ageS=D.codimango_at?Math.max(0,(Date.now()-new Date(D.codimango_at))/1000):null;
 document.getElementById('when').textContent=(LIVE?'live · ':'')+'codimango data '+(ageS==null?'?':age(ageS))+' old · page '+new Date(D.generated_at).toLocaleTimeString();
 renderBoard();renderStats();if(!document.getElementById('team').hidden)renderTeam()}
// ---- interactions
const tip=document.getElementById('tip');let hideT=null;
function showTip(html,x,y){clearTimeout(hideT);tip.innerHTML=html;tip.classList.add('on');const r=tip.getBoundingClientRect();
 let px=x+14,py=y+14;if(px+r.width>innerWidth-8)px=x-r.width-14;if(py+r.height>innerHeight-8)py=y-r.height-14;tip.style.left=Math.max(8,px)+'px';tip.style.top=Math.max(8,py)+'px'}
function hideSoon(){clearTimeout(hideT);hideT=setTimeout(()=>tip.classList.remove('on'),280)}
document.addEventListener('mouseover',e=>{if(tip.contains(e.target)){clearTimeout(hideT);return}
 const td=e.target.closest('td[data-tip]'),th=e.target.closest('th[data-h]');
 if(th){showTip(`<h4>${esc(th.textContent.replace(/ [▲▼]$/,''))}</h4>${esc(HEAD[th.dataset.h])}<div class="hint">click to sort within each group</div>`,e.clientX,e.clientY);return}
 if(!td){hideSoon();return}const t=D.tasks.find(x=>x.task===td.parentElement.dataset.t);if(t)showTip(TIPS[td.dataset.tip](t),e.clientX,e.clientY)});
tip.addEventListener('mouseleave',hideSoon);
document.addEventListener('click',e=>{const g=e.target.closest('[data-g]'),dd=e.target.closest('[data-d]'),o=e.target.closest('[data-o]'),r=e.target.closest('tr.row'),tb=e.target.closest('[data-tab]'),th=e.target.closest('th[data-k]');
 if(tip.contains(e.target))return;
 if(g){S.groups.has(g.dataset.g)?S.groups.delete(g.dataset.g):S.groups.add(g.dataset.g);renderBoard();const n=document.querySelector(`[data-g="${g.dataset.g}"]`);n&&n.classList.add('pop')}
 if(dd){S.done.has(dd.dataset.d)?S.done.delete(dd.dataset.d):S.done.add(dd.dataset.d);renderBoard()}
 const tf=e.target.closest('[data-tagf]');if(tf){const k=tf.dataset.tagf;if(!k)S.tags.clear();else S.tags.has(k)?S.tags.delete(k):S.tags.add(k);renderBoard()}
 if(o){S.owner=o.dataset.o;renderBoard()}if(r)openDrawer(r.dataset.t);
 if(th){const k=th.dataset.k;if(S.sort!==k){S.sort=k;S.dir=1}else if(S.dir>0)S.dir=-1;else S.sort=null;renderBoard()}
 if(tb){document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x===tb));['board','team','stats'].forEach(k=>document.getElementById(k).hidden=tb.dataset.tab!==k);
  if(tb.dataset.tab==='stats')renderStats();if(tb.dataset.tab==='team')renderTeam()}
 if(e.target.id==='msend')sendMsg();
 if(e.target.id==='expand'){const d=document.getElementById('drawer');d.style.width='';localStorage.removeItem('wb-w');d.classList.toggle('wide');localStorage.setItem('wb-wide',d.classList.contains('wide')?'1':'')}
 const mt=e.target.closest('[data-msgtask]');if(mt){document.querySelector('[data-tab=team]').click();const t=D.tasks.find(x=>x.task===mt.dataset.msgtask);
  setTimeout(()=>{document.getElementById('mtask').value=mt.dataset.msgtask;if(t&&t.owner&&t.owner.includes('·')){const sel=document.getElementById('mto');[...sel.options].forEach(o=>{if(o.value===t.owner)o.selected=true})}document.getElementById('mtext').focus()},50)}
 if(e.target.id==='close')document.getElementById('drawer').classList.remove('open')});
(()=>{const g=document.getElementById('grip'),d=document.getElementById('drawer');let on=false;
 g.addEventListener('mousedown',e=>{on=true;g.classList.add('drag');e.preventDefault()});
 document.addEventListener('mousemove',e=>{if(!on)return;const w=Math.max(360,Math.min(innerWidth-40,innerWidth-e.clientX));d.classList.remove('wide');d.style.width=w+'px'});
 document.addEventListener('mouseup',()=>{if(!on)return;on=false;g.classList.remove('drag');localStorage.setItem('wb-w',d.style.width)});
 const w=localStorage.getItem('wb-w');if(w)d.style.width=w})();
document.getElementById('q').addEventListener('input',e=>{S.q=e.target.value;renderBoard()});
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement.id!=='q'){e.preventDefault();document.getElementById('q').focus()}
 if(e.key==='e'&&document.activeElement.tagName!=='INPUT'&&document.activeElement.tagName!=='TEXTAREA'&&document.getElementById('drawer').classList.contains('open')){document.getElementById('expand').click()}
 if(e.key==='Escape'){document.getElementById('drawer').classList.remove('open');tip.classList.remove('on');document.getElementById('q').value='';S.q='';renderBoard()}});
window.addEventListener('beforeunload',()=>localStorage.setItem('wb-prev',JSON.stringify(Object.fromEntries(D.tasks.map(t=>[t.task,{tag:t.tag,valid:t.valid,next:t.next,review:t.review,owner:t.owner}])))));
render();
if(LIVE)setInterval(async()=>{try{const r=await fetch('data.json',{cache:'no-store'});if(r.ok){D=await r.json();render()}}catch(_){document.getElementById('dot').className='dot bad'}},30000);
setInterval(()=>{if(D.codimango_at){const s=(Date.now()-new Date(D.codimango_at))/1000;document.getElementById('when').textContent=(LIVE?'live · ':'')+'codimango data '+age(s)+' old · page '+new Date(D.generated_at).toLocaleTimeString()}},15000);
</script></body></html>
"""
