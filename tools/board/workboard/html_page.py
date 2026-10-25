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
tr.row{cursor:pointer}@keyframes rowin{from{opacity:0;transform:translateY(4px)}to{opacity:1}}
tr.row:hover td{background:#232735}tr.row td:first-child{border-left:4px solid var(--s)}
tr.group td{background:#171a21;color:var(--dim);font-weight:700;padding:7px 10px;border-bottom:1px solid var(--line)}
td.task{font-weight:700;max-width:330px;overflow:hidden;text-overflow:ellipsis}td.own{max-width:220px;overflow:hidden;text-overflow:ellipsis}
.spark{color:var(--pink);display:inline-block;animation:twinkle 1.4s ease-in-out infinite}@keyframes twinkle{50%{opacity:.25;transform:scale(.8) rotate(20deg)}}
.tag{display:inline-block;padding:1px 9px;border-radius:7px;color:#14161c;font-weight:700;font-size:12px}
.age{color:var(--dim);margin-left:6px}.age.warn{color:var(--amber)}.age.block{color:var(--red)}
.ok{color:var(--green)}.run{color:var(--amber)}.bad{color:var(--red)}.dim{color:var(--dim)}.info{color:var(--blue)}
.tk{font-weight:800;letter-spacing:-1px}.tk.g{color:var(--green)}.tk.d{color:#5b6070}.tk.a{color:var(--amber)}.tk.r{color:var(--red)}
tr.row.flash td{animation:flash 1.6s ease}@keyframes flash{0%{background:#f78fb333}100%{background:transparent}}
#rows.anim tr.row{animation:rowin .35s ease both}.age2{display:block;font-size:11.5px;margin:1px 0 0 0}
select.kind{background:var(--panel);border:1px solid var(--line);color:var(--text);border-radius:999px;padding:5px 10px;font:inherit;cursor:pointer}
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
aside.open{transform:none}aside.noanim .sec{animation:none;opacity:1}aside.wide{width:min(1180px,92vw)}aside.wide #dbody{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
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
<div class="controls"><div class="seg" id="owner"></div><select class="kind" id="kind" title="task type"><option value="">🧩 all types</option><option value="multi-turn">🔁 multi-turn</option><option value="single-turn">1️⃣ single-turn</option></select><input type="search" id="q" placeholder="🔍 search tasks  ( / )"><span class="health" id="health"></span></div>
<div class="tbl"><table><thead><tr>
<th data-k="task" data-h="task">Task</th><th data-k="next" data-h="next">Next</th><th data-k="tag" data-h="tag">Status</th>
<th data-k="owner" data-h="owner">Owner</th><th data-k="valid" data-h="valid">Validation</th><th data-k="review" data-h="review">Human review</th>
<th data-k="check" data-h="check">Presubmit</th><th data-k="sync" data-h="sync">Server</th></tr></thead><tbody id="rows"></tbody></table></div>
<div class="legend"><span><span class="spark">✦</span> changed</span><span><span style="color:#ff4d4d">▌</span>red edge = broken, fix first</span><span>Presubmit: <span class="tk g">✓</span><span class="tk d">○</span> building session · independent agent (○ not run)</span>
<span>Server: <span class="tk g">✓</span><span class="tk r">✘</span> imported · validated</span><span><span class="tk d">✓</span> grey = last outcome, not for your latest commit (hover for why)</span><span>✍️ working · 💤 idle · 👀 active · 📜 CLAIMS.md · 🔓 free</span><span class="dim">hover anything for details · click a task for its card</span></div>
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
const G = {MINE:['#ff8f6b','🙋','action needed'],VALIDATING:['#7ab8ff','⏳','server validating'],
 REVIEWING:['#b39dff','👀','with reviewers'],DONE:['#8b90a0','🎉','done']};
const GHELP = {MINE:'Something for you or one of your sessions to do: fix, address feedback, presubmit, review, submit. Broken ones (red edge) come first within each status.',
 VALIDATING:'Nothing to do — codimango is importing or validating your latest push.',
 REVIEWING:'Nothing to do — submitted and waiting on human reviewers.',DONE:'Accepted, in training or archived.'};
const dg = t => (t.group==='ATTENTION'||t.group==='READY')?'MINE':t.group;
const TAGO = ['Sent back','Draft','Not imported','Needs reviewers','In review','Accepted','In training','Archived'];
const TAGC = {'Draft':'#e0b860','Sent back':'#ff875f','Needs reviewers':'#8fb8e0','In review':'#5fafff','Accepted':'#7bd88f','In training':'#5fd7d7',
 'Archived':'#808080','Not imported':'#585858'};
const NEXT = {FIX:'🔧',RESOLVE:'🤺',RERUN:'🔁',SUBMIT:'🚀',GET:'👀',RUN:'🧪',WAIT:'⏳',ADDRESS:'📝',IMPORT:'📥','—':'🎉'};
const HEAD = {task:'The task folder. Hover a task name for what it is; click for its card with next steps.',
 next:'What to do next, worked out from validation, reviews, sync and ownership. Hover for why.',
 tag:'Status in codimango (Draft, Sent back, Needs reviewers, In review, Accepted, In training, Archived), with how long it has been there underneath. The board opens sorted by this.',
 owner:'Who is on it: ✍️ claimed and working now · 💤 claimed but idle · 👀 a session touched it recently (no claim) · 📜 listed in CLAIMS.md · 🔓 nobody.',
 valid:'codimango validation. Hover shows only the problems and how to fix them.',
 review:'Human review in codimango: ✔ accepted · ✘ sent back (n times) · 👀 in review · ⌛ waiting for a reviewer · · not submitted. Hover for the last decision.',
 check:'Two presubmits: 1st tick = the session building the task, 2nd = an independent fresh agent. Green ✓ clean on this commit · red ✘ failures · grey = last result is from an older commit (re-run) · ○ = not run. Hover shows what each suggested fixing.',
 sync:'Two ticks: 1st = codimango has your latest push (grey while importing, amber if it is on an older commit) · 2nd = validated (green passed · red ✘ failed or a reviewer sent it back · grey while running or results are old).'};
const S = {tags:new Set(), groups:new Set(['MINE','VALIDATING']), gfirst:true, kind:'', sig:{}, owner:'all', q:'', sort:'tag', dir:1, first:true, rowh:{}, keys:'', blocks:{},
 prev:JSON.parse(localStorage.getItem('wb-prev')||'{}')};
const code = s => esc(s).replace(/`([^`]+)`/g,'<code>$1</code>');
const esc = s => String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const age = s => s==null?'?':s<60?'<1m':s<3600?Math.floor(s/60)+'m':s<86400?Math.floor(s/3600)+'h':Math.floor(s/86400)+'d';
const fdate = x => x?new Date(x).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'—';
const L = (cls,ch,txt) => `<li><span class="b-${cls}">${ch}</span><span>${txt}</span></li>`;
const CH = {ok:'●',pend:'○',bad:'✘',dim:'·',info:'→'};
const tick = (n,green,amber) => n?`<span class="tk ${green?'g':amber?'a':'d'}">${'✓'.repeat(n)}</span>`:'<span class="tk d">✓✓</span>';
function kindLine(t){const c=t.category||{};const track=(t.track||'').includes('multi')?'multi-turn':(t.track?'single-turn':'');
 return [track&&('SWE-bench '+track), (c.category||'').replace(/_/g,' '), (c.subdomain||'').replace(/_/g,' '), (c.languages||[]).join('/'), c.difficulty].filter(Boolean).join(' · ')}
function ownerIdle(t){return t.owner_last_at?(Date.now()-Date.parse(t.owner_last_at))/1000:null}
function owner(t){const h=t.claim_health,o=esc(t.owner);if(h==='DONE')return'';if(h==='FREE'||!t.owner)return'<span class="info">🔓 free</span>';
 if(h==='OWNED'){const i=ownerIdle(t);return i!=null&&i<1200?`<span style="color:var(--violet)">✍️ ${o}</span> <span class="dim">now</span>`:`<span class="dim">💤 ${o} · idle ${i==null?'?':age(i)}</span>`}
 if(h==='ACTIVE')return`<span class="run">👀 ${o}</span> <span class="dim">${age((t.active||[{}])[0].ago_s)}</span>`;
 if(h==='CONFLICT')return`<span class="bad">🤺 ${o}</span>`;if(h==='EXPIRED')return`<span class="dim">💤 ${o}</span>`;
 if(h==='LEGACY')return`<span class="dim">📜 ${o}</span>`;return`<span style="color:var(--violet)">👤 ${o}</span>`}
function valid(t){const v=t.vsum;if(t.older_results&&t.valid!=='RUN')return'<span class="run">↻ older commit</span>';const f=v.issues.filter(i=>i.severity==='fail').length,w=v.issues.filter(i=>i.severity==='warn').length;
 if(t.valid==='RUN')return'<span class="run">○ running</span>';if(!v.total)return'<span class="dim">· none yet</span>';
 if(f)return`<span class="bad">✘ ${f} issue${f>1?'s':''}</span>`;if(w)return`<span class="run">▲ ${w} warning${w>1?'s':''}</span>`;return'<span class="ok">✔ clean</span>'+(v.info&&v.info.length?' <span class="dim">ⓘ</span>':'')}
function review(t){const raw=t.status_raw,n=t.decisions.filter(d=>d.kind==='revision').length;
 if(raw==='accepted')return'<span class="ok">✔ accepted</span>';if(raw==='used_in_training')return'<span style="color:var(--teal)">✔ in training</span>';
 if(raw==='needs_revision')return`<span class="bad">✘ sent back${n>1?' '+n+'×':''}</span>`;if(raw==='being_reviewed')return'<span style="color:var(--violet)">👀 in review</span>';
 if(raw==='needs_reviewers_assigned')return'<span class="info">⌛ awaiting reviewer</span>';if(raw==='archived')return'<span class="dim">📦 archived</span>';
 return n?`<span class="dim">· draft (↩${n}×)</span>`:'<span class="dim">· not submitted</span>'}
const TK=(st,glyph)=>st==='ok'?'<span class="tk g">✓</span>':st==='bad'?'<span class="tk r">✘</span>':st==='amber'?'<span class="tk a">✓</span>':st==='none'?'<span class="tk d">○</span>':`<span class="tk d">${glyph||'✓'}</span>`;
function gate(t){return (t.rsum&&t.rsum.gates)||{author:{check:{state:'none'},review:{state:'none'}},independent:{check:{state:'none'},review:{state:'none'}}}}
function check(t){const g=gate(t);return ['author','independent'].map(r=>{const c=g[r].check;return TK(c.state,c.state==='old'&&c.fail?'✘':'✓')}).join('')}
function sync(t){const s=t.sync,codes=(t.findings||[]).map(f=>f.code);
 // 1st tick: does codimango have your latest push?  2nd tick: is the validation result for that commit?
 const imp=s==='OK'||s==='OK·doc'||s==='STALE_VALID'?'ok':s==='IMPORTING'?'grey':s==='HEAD≠SERVER'?'amber':'none';
 const oldv=s==='IMPORTING'||s==='HEAD≠SERVER'||s==='STALE_VALID'||codes.includes('VALID≠SERVER');
 const bad=t.valid==='FAIL'||t.status_raw==='needs_revision';
 const val=t.valid==='RUN'?'grey':oldv?(t.valid==='PASS'||bad?'grey':'none'):bad?'bad':t.valid==='PASS'?'ok':'none';
 return TK(imp)+TK(val,bad?'✘':'✓')}
function next(t){const n=t.next||'',e=NEXT[n.split(' ')[0]]||'•';const col=n.startsWith('FIX')||n.startsWith('RESOLVE')?'var(--red)':n.startsWith('SUBMIT')?'var(--green)':n.startsWith('WAIT')?'var(--dim)':'var(--amber)';
 return `${e} <span style="color:${col}">${esc(n)}</span>`}
function tag(t){return `<span class="tag" style="background:${TAGC[t.tag]||'#666'}">${esc(t.tag)}</span><span class="age age2 ${t.age_level||''}">${esc(AGEW[t.age_label]||'')} ${age(t.state_age_s)}</span>`}
const AGEW={'decided':'decided','submitted':'submitted','in review since (approx.)':'in review','archived':'archived','back in draft since (approx.)':'back','created':'created'};
// ---- hover cards: short, only what matters
function tipTask(t){return `<h4>${esc(t.task)}</h4><ul>${L('info','◆',esc(kindLine(t)||'no category yet'))}${t.category&&t.category.domain?L('dim','·',esc(t.category.domain)):''}${t.category&&t.category.usecase?L('dim','·',esc(t.category.usecase.replace(/_/g,' '))):''}</ul>`}
function tipNext(t){return `<h4>next · ETA</h4><ul>${t.steps.map(s=>L('pend','→',`${code(s.do)} <span class="dim">${esc(s.eta)}</span>`)).join('')||L('ok','●','nothing to do')}</ul>`}
function tipTag(t){let h=`<h4>${esc(t.tag)} · ${esc(t.age_label||'')} ${age(t.state_age_s)} ago</h4><ul>`;if(t.entered_pool_at)h+=L('dim','↗','submitted '+fdate(t.entered_pool_at));
 t.decisions.slice(-3).forEach(d=>h+=L(d.kind==='accept'?'ok':'bad',d.kind==='accept'?'✔':'↩',(d.kind==='accept'?'accepted ':'sent back ')+fdate(d.at)));
 if(t.age_level&&t.age_level!=='ok')h+=L(t.age_level==='block'?'bad':'pend','!',t.age_level==='block'?'overdue for this state':'getting old');return h+'</ul>'}
function tipOwner(t){let h=`<h4>who · source: ${esc(t.claim_source||'none')}</h4><ul>`;if(t.claim_health==='OWNED'){const i=ownerIdle(t);h+=L(i!=null&&i<1200?'ok':'dim',i!=null&&i<1200?'✍️':'💤',i==null?'claimed; no activity recorded':i<1200?'working on it now':'assigned but idle for '+age(i))}(t.active||[]).slice(0,3).forEach(a=>h+=L('pend','👀',`${esc(a.alias)} · ${age(a.ago_s)} ago`));
 if(t.claim_health==='OWNED')h+=L('ok','👤','claimed by '+esc(t.owner));if(t.legacy)h+=t.claim_health==='LEGACY'?L('info','📜',`CLAIMS.md: ${esc(t.legacy.legacy_owner)} · ${esc(t.legacy.status)} · ${esc(t.legacy.updated)}`):L('dim','📜',`old CLAIMS.md row (not an active owner): ${esc(t.legacy.legacy_owner)} · ${esc(t.legacy.status)}`);
 if(t.claim_health==='FREE')h+=L('info','🔓','nobody');h+=L('dim','→',esc(t.assignee));return h+'</ul>'}
function tipValid(t){const v=t.vsum;if(t.older_results)return'<h4>validation</h4><ul>'+L('pend','↻','these results are for an older commit — your latest push has not been validated')+L('info','→','codimango task rerun '+esc(t.task))+'</ul>';if(t.valid==='RUN'&&!v.issues.length)return'<h4>validation</h4><ul>'+L('pend','○','running')+'</ul>';
 const inf=(v.info||[]).map(i=>L('dim','ⓘ',`<b>${esc(i.check)}</b> ${esc(i.why)} (informational, not blocking)`)).join('');
 if(!v.issues.length)return`<h4>validation</h4><ul>${L('ok','●',`${v.total-(v.info||[]).length} of ${v.total} checks clear`)}${inf}</ul>`;
 return `<h4>validation · ${v.passed}/${v.total} clear</h4><ul>${v.issues.map(i=>L(i.severity==='fail'?'bad':'pend',i.severity==='fail'?'✘':'▲',`<b>${esc(i.check)}</b> ${esc(i.why)}<br><span class="dim">→ ${esc(i.fix.replace('{task}',t.task))}</span>`)).join('')}${v.skipped&&v.skipped.length?L('dim','⤷',esc([...new Set(v.skipped)].join(', '))+' skipped until the above passes'):''}${inf}</ul>`}
function tipReview(t){let h=`<h4>human review · ${esc(t.rsum.human)}</h4><ul>`;
 t.decisions.slice(-3).forEach(d=>h+=L(d.kind==='accept'?'ok':'bad',d.kind==='accept'?'✔':'↩',`${d.kind==='accept'?'accepted':'sent back'} ${fdate(d.at)}`));
 const d=t.decisions[t.decisions.length-1];if(d&&d.reason)h+=L('dim','“',esc(d.reason.slice(0,140)));
 if(t.review_history_stale)h+=L('pend','↻','review history is refreshing — rounds may be incomplete');
 if(t.entered_pool_at&&!t.decisions.length)h+=t.status_raw==='draft'?L('info','↩','previously submitted '+fdate(t.entered_pool_at)+', back in draft'):L('info','⌛','submitted '+fdate(t.entered_pool_at)+', no decision yet');
 if(!t.entered_pool_at)h+=L('dim','·','not submitted yet');
 const g=gate(t);h+=L(g.author.review.state==='ok'&&g.independent.review.state==='ok'?'ok':'pend','🤖',`required agent approvals: building session ${g.author.review.state==='ok'?'✓':'—'} · independent agent ${g.independent.review.state==='ok'?'✓':'—'}`);return h+'</ul>'}
function tipCheck(t){const g=gate(t);let h='<h4>presubmit · building session + independent agent</h4><ul>';
 [['author','1️⃣ building session','board check run '+t.task+' --role author'],['independent','2️⃣ independent agent','fresh agent: board check record '+t.task+' --role independent …']].forEach(([r,l,how])=>{const c=g[r].check;
  if(c.state==='none'){h+=L('dim','·',`${l}: not run <span class="dim">→ ${esc(how)}</span>`);return}
  h+=L(c.state==='ok'?'ok':c.state==='bad'?'bad':'dim',c.fail?'✘':'●',`${l}: ${c.fail?c.fail+' failure(s)':'clean'}${c.warn?', '+c.warn+' warning(s)':''} · ${fdate(c.at)}${c.state==='old'?' · <b>older commit — re-run</b>':''}`);
  if(c.summary)h+=L('info','💡','suggested: '+esc(c.summary))});return h+'</ul>'}
function tipSync(t){const s=t.sync;let h='<h4>server · 1st tick imported · 2nd tick validated</h4><ul>';
 if((t.findings||[]).some(f=>f.code==='VALID≠SERVER'))h+=L('pend','↻','validation results are for an older server commit (grey 2nd tick)');
 if(t.valid==='FAIL'){const i=t.vsum.issues.filter(x=>x.severity==='fail');h+=L('bad','✘','validation failed'+(i.length?': '+esc(i.map(x=>x.check).join(', ')):''))}
 if(t.status_raw==='needs_revision')h+=L('bad','✘','sent back by the reviewer');if(t.valid==='RUN')h+=L('dim','⏳','validating now');
 if(s==='OK'||s==='OK·doc')h+=L('ok','●','server has your latest commit')+L(t.validated?'ok':'pend',t.validated?'●':'○',t.validated?'and validated it':'validation running');
 else if(s==='IMPORTING')h+=L('info','⏳','your push is being imported (a few minutes)');
 else if(s==='STALE_VALID')h+=L('pend','▲','validated an older commit; code changed since')+L('info','→','codimango task rerun');
 else if(s==='HEAD≠SERVER')h+=L('pend','▲',(t.findings.find(f=>f.code==='HEAD≠SERVER')||{}).summary||'latest push not on server')+L('info','→','rerun if it does not catch up');
 else h+=L('dim','·','not compared');return h+'</ul>'}
const TIPS={task:tipTask,next:tipNext,tag:tipTag,owner:tipOwner,valid:tipValid,review:tipReview,check:tipCheck,sync:tipSync};
function changed(t){const p=S.prev[t.task];return p&&(p.tag!==t.tag||p.valid!==t.valid||p.next!==t.next||p.review!==t.review||p.owner!==t.owner)}
function visible(){return D.tasks.filter(t=>S.groups.has(dg(t))&&(!S.tags.size||S.tags.has(t.tag))&&(!S.kind||t.kind===S.kind)&&
 (S.owner==='all'||(S.owner==='free'?['FREE','EXPIRED'].includes(t.claim_health):S.owner==='active'?((t.claim_health==='ACTIVE'&&((t.active||[])[0]||{}).ago_s<1200)||(t.claim_health==='OWNED'&&ownerIdle(t)!=null&&ownerIdle(t)<1200)):S.owner==='claimed'?['OWNED','LEGACY'].includes(t.claim_health):true))&&
 (!S.q||t.task.includes(S.q.toLowerCase())))}
function setHTML(id,html){if(S.blocks[id]!==html){S.blocks[id]=html;document.getElementById(id).innerHTML=html}}
function rowHtml(t){return `<tr class="row" data-t="${esc(t.task)}" style="--s:${t.group==='ATTENTION'?'#ff4d4d':G[dg(t)][0]}"><td class="task" data-tip="task">${changed(t)?'<span class="spark">✦</span> ':''}${esc(t.task)}</td>
  <td data-tip="next">${next(t)}</td><td data-tip="tag">${tag(t)}</td><td data-tip="owner" class="own">${owner(t)}</td><td data-tip="valid">${valid(t)}</td>
  <td data-tip="review">${review(t)}</td><td data-tip="check">${check(t)}</td><td data-tip="sync">${sync(t)}</td></tr>`}
function rowSig(t){return [t.next,t.tag,t.valid,t.review,t.owner,t.claim_health,t.sync,check(t),sync(t)].join('|')}   // flash only on real changes, not ticking ages
function renderBoard(){const counts={};D.tasks.forEach(t=>{if(!S.kind||t.kind===S.kind)counts[dg(t)]=(counts[dg(t)]||0)+1});
 let chips=Object.entries(G).map(([g,[c,e,l]])=>`<button class="chip ${S.groups.has(g)?'':'off'}" data-g="${g}" title="${esc(GHELP[g])}"><span class="c" style="background:${c}"></span><span class="e">${e}</span> ${l} <b>${counts[g]||0}</b></button>`).join('');
 const inGroups=D.tasks.filter(t=>S.groups.has(dg(t))&&(!S.kind||t.kind===S.kind));
 const tagc={};inGroups.forEach(t=>tagc[t.tag]=(tagc[t.tag]||0)+1);[...S.tags].forEach(x=>{if(!tagc[x])S.tags.delete(x)});
 chips+=`<span class="sub-chips"><span class="dim">status:</span>${Object.entries(tagc).sort((a,b)=>TAGO.indexOf(a[0])-TAGO.indexOf(b[0])).map(([k,n])=>`<button class="chip ${!S.tags.size||S.tags.has(k)?'':'off'}" data-tagf="${esc(k)}"><span class="c" style="background:${TAGC[k]||'#666'}"></span>${esc(k)} <b>${n}</b></button>`).join('')}${S.tags.size?'<button class="chip" data-tagf="">✕ all</button>':''}</span>`;
 if(!S.gfirst)chips+='<button class="chip" data-greset="1" title="back to the default view">↺ reset</button>';
 setHTML('chips',chips);
 setHTML('owner',['all','free','active','claimed'].map(o=>`<button class="${S.owner===o?'on':''}" data-o="${o}">${{all:'👥 all',free:'🔓 free',active:'✍️ working now',claimed:'👤 claimed'}[o]}</button>`).join(''));
 setHTML('bar',Object.entries(G).map(([g,[c]])=>`<span style="flex:${counts[g]||0};background:${c}"></span>`).join(''));
 let rows=visible();const order=Object.keys(G);
 const val=t=>{const k=S.sort;return k==='tag'?(TAGO.indexOf(t.tag)<0?99:TAGO.indexOf(t.tag))*1e9+(t.group==='ATTENTION'?0:5e8)-Math.min(t.state_age_s||0,4e8)
  :k==='review'?t.rsum.agent.length:k==='valid'?t.vsum.issues.length:String(t[k]??'')};
 rows=[...rows].sort((a,b)=>order.indexOf(dg(a))-order.indexOf(dg(b))||(S.sort?((val(a)>val(b)?1:val(a)<val(b)?-1:0)*S.dir):0)||a.task.localeCompare(b.task));
 const items=[];let last=null;rows.forEach(t=>{const g=dg(t);if(g!==last){last=g;const[c,e,l]=G[g];items.push(['§'+g,`<tr class="group"><td colspan="8" style="border-left:4px solid ${c}" title="${esc(GHELP[g])}">${e} ${l} · ${rows.filter(r=>dg(r)===g).length}</td></tr>`])}
  items.push([t.task,rowHtml(t)])});
 const keys=items.map(x=>x[0]).join('|');const tb=document.getElementById('rows');
 if(keys!==S.keys||!items.length){              // different rows or order: rebuild (animate only on first paint)
  tb.classList.toggle('anim',S.first);if(S.first)setTimeout(()=>tb.classList.remove('anim'),1500);tb.innerHTML=items.map(x=>x[1]).join('')||'<tr><td colspan="8" class="empty">🌈 nothing matches — try another filter</td></tr>';
  S.keys=keys;S.rowh=Object.fromEntries(items);S.sig=Object.fromEntries(rows.map(t=>[t.task,rowSig(t)]))}
 else items.forEach(([k,h])=>{if(S.rowh[k]!==h){S.rowh[k]=h;const old=[...tb.children].find(r=>(r.dataset.t||'')===k||(k[0]==='§'&&r.classList.contains('group')&&r.textContent.includes(G[k.slice(1)][2])));
  if(old){const tmp=document.createElement('tbody');tmp.innerHTML=h;const n=tmp.firstElementChild;if(n.classList.contains('row')){const t=rows.find(r=>r.task===k),sg=rowSig(t);if(S.sig[k]!==sg)n.classList.add('flash');S.sig[k]=sg}old.replaceWith(n)}}});
 S.first=false;
 document.querySelectorAll('th[data-k]').forEach(th=>{const want=th.textContent.replace(/ [▲▼]$/,'')+(S.sort===th.dataset.k?(S.dir>0?' ▲':' ▼'):'');if(th.textContent!==want)th.textContent=want});
 const h=D.health;setHTML('health',Object.entries(h).map(([k,v])=>`<span class="${v.ok?'ok':'bad'}">${v.ok?'✔':'✘'} ${k}</span>`).join(' · ')+(D.ledger_ok===null?'':` · <span class="${D.ledger_ok?'ok':'bad'}">${D.ledger_ok?'✔':'✘'} ledger${D.ledger_at?' '+age((Date.now()-Date.parse(D.ledger_at))/1000)+' ago':''}</span>`)+(D.refresh_error?` · <span class="bad">refresh failing: ${esc(D.refresh_error)}</span>`:''));
 const stale=D.codimango_at&&(Date.now()-new Date(D.codimango_at))/1000>600;
 document.getElementById('dot').className='dot'+(Object.values(h).every(v=>v.ok)&&!D.refresh_error&&!stale&&D.ledger_ok!==false?'':' bad')}
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
function openDrawer(name,refresh){const t=D.tasks.find(x=>x.task===name);if(!t)return;const Lk=t.links||{};S.open=name;
 const btn=(k,l,p)=>Lk[k]?`<a class="btn ${p?'primary':''}" href="${esc(Lk[k])}" target="_blank" rel="noopener">${l} ↗</a>`:'';
 const v=t.vsum;
 const html=`<div class="head"><p class="card-title">${Lk.codimango?`<a href="${esc(Lk.codimango)}" target="_blank" rel="noopener" title="open in codimango">${esc(t.task)} ↗</a>`:esc(t.task)}</p><div class="kind">${esc(kindLine(t))}</div>
 <div>${tag(t)} &nbsp; ${next(t)}</div>
 <div class="btns">${btn('codimango','🥭 Open in codimango',1)}${btn('github','🐙 Files at server commit')}${btn('latest','📂 Latest on main')}
 <button class="btn" data-msgtask="${esc(t.task)}">💬 Message the owner</button></div></div>
 <div class="sec next-sec"><h3>🚀 NEXT STEPS</h3>${t.steps.map((s,i)=>`<div class="step"><span class="n">${i+1}</span><span>${code(s.do)}</span><span class="eta">${esc(s.eta)}</span></div>`).join('')||'<div class="dim">nothing to do 🎉</div>'}
  <div class="who">👤 ${esc(t.assignee)}</div></div>
 ${v.issues.length?`<div class="sec"><h3>⚠️ PROBLEMS · ${v.passed}/${v.total} checks clear</h3><ul class="lst">${v.issues.map(i=>L(i.severity==='fail'?'bad':'pend',i.severity==='fail'?'✘':'▲',`<b>${esc(i.check)}</b> ${esc(i.why)} <span class="dim">→ ${esc(i.fix)}</span>`)).join('')}</ul></div>`:''}
 <div class="sec"><h3>👥 REVIEW</h3><ul class="lst">${t.rsum.bullets.map(([k,x])=>L(k,CH[k],esc(x))).join('')}</ul>
  ${t.decisions.length&&t.decisions[t.decisions.length-1].reason?`<div class="dim" style="margin-top:6px">last review: “${esc(t.decisions[t.decisions.length-1].reason)}”</div>`:''}</div>
 ${t.versions.length?`<div class="sec"><h3>🗂 ROUNDS</h3><div class="timeline">${t.versions.map((x,i)=>`${i?'<span class="arrow">→</span>':''}<span class="ver"><b>${x.label}</b> ${x.commits} commit${x.commits===1?'':'s'}${x.ended?` <span class="${x.ended==='accept'?'b-ok':'b-bad'}">${x.ended==='accept'?'✔':'↩'}</span> <span class="dim">${fdate(x.at)}</span>`:' <span class="dim">so far</span>'}</span>`).join('')}</div></div>`:''}
 <div class="sec"><h3>🧪 PRESUBMIT</h3><ul class="lst">${tipCheck(t).replace(/^<h4>.*?<\/h4><ul>|<\/ul>$/g,'')}</ul></div>
 <div class="sec"><h3>🔗 WHO & SERVER</h3><ul class="lst">${tipOwner(t).replace(/^<h4>.*?<\/h4><ul>|<\/ul>$/g,'')}${tipSync(t).replace(/^<h4>.*?<\/h4><ul>|<\/ul>$/g,'')}</ul></div>
 <div class="dim" style="margin-top:10px">terminal: <code>board show ${esc(t.task)}</code></div>`;
 if(refresh&&S.drawerHtml===html)return;S.drawerHtml=html;document.getElementById('dbody').innerHTML=html;
 const d=document.getElementById('drawer');if(refresh)return;d.classList.remove('noanim');d.classList.remove('open');d.classList.toggle('wide',!!localStorage.getItem('wb-wide'));void d.offsetWidth;d.classList.add('open')}
function refreshDrawer(){const d=document.getElementById('drawer');if(!S.open||!d.classList.contains('open'))return;
 const top=d.scrollTop;d.classList.add('noanim');openDrawer(S.open,true);d.scrollTop=top}
const HC={};const hostColor=h=>HC[h]||(HC[h]=['#f78fb3','#7ab8ff','#7bd88f','#f5c26b','#b39dff'][Object.keys(HC).length%5]);
function renderTeam(){const me=localStorage.getItem('wb-to')||'all';
 const srv=(D.servers||[]).map(s=>`<div class="srv"><h3><span class="badge" style="background:${hostColor(s.id)}">${esc(s.id)}</span> server
  <span class="dim">· heartbeat ${s.last_sync_ago_s==null?'never':age(s.last_sync_ago_s)+' ago'}</span>
  <span class="${s.last_sync_ago_s!=null&&s.last_sync_ago_s<600?'ok':'bad'}">${s.last_sync_ago_s==null?'● never synced':s.last_sync_ago_s<600?'● sync fresh':'● sync stale'}</span></h3>
  <div class="dim">${s.sessions.length} session(s) seen in the last 2h · working on ${s.owned.length} task(s)${s.last_sync_ago_s==null?' · <span class="bad">no heartbeat yet — run board setup there</span>':''}${s.last_activity_ago_s!=null?' · last activity '+age(s.last_activity_ago_s)+' ago':''}</div>
  <ul class="lst">${s.sessions.map(x=>L('pend','✍️',`${esc(x.alias.split('·').slice(1).join('·')||x.alias)} <span class="dim">${age(x.ago_s)} ago</span>`)).join('')||L('dim','·','no active sessions in the last 2h')}</ul></div>`).join('');
 const msgs=(D.messages||[]).slice(-30).reverse().map(m=>`<div class="msg ${m.from.includes('dashboard')?'me':''}"><div class="meta">${esc(m.from)} → <b>${esc(m.to_label)}</b>${m.task?' · '+esc(m.task):''} · ${fdate(m.at)}
  ${m.acked_by.length?' · <span class="ok">✓ acked by '+m.acked_by.length+'</span>':' · <span class="run">not acked yet</span>'}</div><div>${esc(m.text)}</div></div>`).join('')||'<div class="dim">no messages yet</div>';
 const opts=['all',...(D.servers||[]).map(s=>s.id),...(D.sessions||[])];
 const feed=(D.feed||[]).map((f,i)=>`<div class="fi" style="animation-delay:${Math.min(i*8,300)}ms"><span class="t">${new Date(f.at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</span>
  <span><span class="badge" style="background:${hostColor(f.host)}">${esc(f.host)}</span></span><span>${esc(f.what)} ${f.task?'<b>'+esc(f.task)+'</b>':''}<div class="w">${esc(f.who)}</div></span></div>`).join('')||'<div class="dim">quiet</div>';
 document.getElementById('team').innerHTML=`<div class="team"><div>${srv}
  <div class="panel"><h3>💬 send a message</h3>
  <div class="dim" style="margin-bottom:6px">How it travels: saved to the shared private ledger → the target server picks it up on its next sync (normally ≤2 min while it has a heartbeat) →
  the hook shows it inside the target Claude session on its next step (Codex runs see it only via <code>board inbox</code>) → the session acks/replies with <code>board ack</code> / <code>board msg</code>.
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
  st.innerHTML=j.ok?`<span class="sent">✓ in the ledger for ${esc(j.to)}${j.synced?' — published; it reaches them after their server\'s next sync and their next tool step':' (queued, publishes on next sync)'}</span>`:`<span class="bad">${esc(j.error)}</span>`;
  if(j.ok){document.getElementById('mtext').value='';const d=await (await fetch('data.json',{cache:'no-store'})).json();D=d;renderTeam()}}catch(e){st.innerHTML='<span class="bad">failed</span>'}}
function render(){const W=D.week;setHTML('week',`📈 W${W.week}: <b>${W.this_week}</b> accepted · last week at this point ${W.same_point_last_week} · 4-week median ${W.median_4wk}`);
 renderWhen();renderBoard();refreshDrawer();if(!document.getElementById('stats').hidden)renderStats();if(!document.getElementById('team').hidden)renderTeam()}
function renderWhen(){const ageS=D.codimango_at?Math.max(0,(Date.now()-new Date(D.codimango_at))/1000):null;
 const exact=s=>s==null?'?':s<3600?Math.round(s/60)+'m':Math.floor(s/3600)+'h'+String(Math.round(s%3600/60)).padStart(2,'0')+'m';
 document.getElementById('when').textContent=(LIVE?'live · ':'')+'codimango data '+exact(ageS)+' old'+(D.codimango_detail&&!D.health.codimango.ok?' — '+D.codimango_detail:'')+' · page built '+exact(Math.max(0,(Date.now()-new Date(D.generated_at))/1000))+' ago';
}
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
 if(g){const k=g.dataset.g;if(S.gfirst){S.groups=new Set([k]);S.gfirst=false}else{S.groups.has(k)?S.groups.delete(k):S.groups.add(k);if(!S.groups.size)S.groups.add(k)}
  renderBoard();const n=document.querySelector(`[data-g="${k}"]`);n&&n.classList.add('pop')}
 if(e.target.closest('[data-greset]')){S.groups=new Set(['MINE','VALIDATING']);S.gfirst=true;S.tags.clear();renderBoard()}
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
document.getElementById('kind').addEventListener('change',e=>{S.kind=e.target.value;renderBoard()});
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement.id!=='q'){e.preventDefault();document.getElementById('q').focus()}
 if(e.key==='e'&&document.activeElement.tagName!=='INPUT'&&document.activeElement.tagName!=='TEXTAREA'&&document.getElementById('drawer').classList.contains('open')){document.getElementById('expand').click()}
 if(e.key==='Escape'){document.getElementById('drawer').classList.remove('open');tip.classList.remove('on');document.getElementById('q').value='';S.q='';renderBoard()}});
window.addEventListener('beforeunload',()=>localStorage.setItem('wb-prev',JSON.stringify(Object.fromEntries(D.tasks.map(t=>[t.task,{tag:t.tag,valid:t.valid,next:t.next,review:t.review,owner:t.owner}])))));
render();
if(LIVE)setInterval(async()=>{try{const r=await fetch('data.json',{cache:'no-store'});if(r.ok){D=await r.json();render()}}catch(_){document.getElementById('dot').className='dot bad'}},20000);
setInterval(renderWhen,15000);
</script></body></html>
"""
