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
.keyhelp{margin-left:auto;color:var(--dim);font-size:11.5px;align-self:center}
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
.tokenline{display:block;color:var(--dim);font-size:10.5px;font-weight:400;margin-top:2px}.primary-action{font-weight:700}.advice-action{display:block;color:var(--dim);font-size:11px;margin-top:2px}
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
.server-grid{display:grid;grid-template-columns:repeat(2,minmax(260px,1fr));gap:12px;margin-bottom:14px}.srv{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--panel)}
.srv h3{margin:0 0 6px;font-size:14px}.srv .live{margin:0}.badge{display:inline-block;padding:0 7px;border-radius:6px;font-size:11.5px;font-weight:700;color:#14161c}
.team{display:grid;grid-template-columns:var(--tl,420px) 10px minmax(420px,1fr);gap:14px;align-items:start}.team-side{position:sticky;top:10px}.feed{max-height:44vh;overflow:auto}.fi{display:grid;grid-template-columns:52px 64px 1fr;gap:8px;padding:6px 4px;border-bottom:1px solid #22252f;animation:rowin .3s ease both}
.fi .t{color:var(--dim)}.fi .w{color:var(--dim);font-size:12px}.msg{border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin:6px 0;background:#181b22;animation:up .3s ease}
.msg .meta{color:var(--dim);font-size:12px}.msg.me{border-color:#f78fb355}.compose{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.compose select{max-width:100%;min-width:0}.compose select,.compose input,.compose textarea{background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:10px;padding:7px 10px;font:inherit}
.compose textarea{flex:1 1 100%;min-height:60px}.sent{color:var(--green);animation:fadein .3s}aside .x{position:absolute;top:14px;right:18px;cursor:pointer;color:var(--dim);font-size:16px;transition:transform .2s}
.session-table{overflow:auto;border:1px solid var(--line);border-radius:10px}.session-table table{font-size:12.5px}.session-table th{padding:7px 8px}.session-table td{padding:6px 8px;white-space:normal;vertical-align:top}.session-table td:first-child{width:30px;text-align:center;font-size:16px}.session-table .srow{cursor:pointer}.session-table .srow:hover td{background:#232735}.session-table .sgroup td{background:#151820;color:var(--dim);font-weight:700}.session-table .focus{max-width:280px}.session-table .advice{max-width:300px}.session-detail .line{margin:5px 0}.session-detail b{color:var(--text)}.route{font-size:11.5px;margin-top:3px}.diag{margin-top:8px}
@media(max-width:900px){.server-grid,.team{grid-template-columns:1fr}.team-side{position:static}}
@media(max-width:900px){.keyhelp{display:none}}
.pa-status{display:none;margin-top:3px}@media(max-width:1200px){.c-status{display:none}.pa-status{display:block}}
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
.who{margin-top:8px;color:var(--violet)}.pill{display:inline-block;border:1px solid;border-radius:999px;padding:0 7px;margin-right:4px;font-size:11.5px;line-height:17px}.step.routine{opacity:.45}.step.routine .n{background:var(--dim)}
.timeline{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.ver{border:1px solid var(--line);border-radius:8px;padding:3px 9px;background:var(--panel2)}
.ver b{color:var(--pink)}.arrow{color:var(--dim)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-bottom:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;transition:transform .2s}.card:hover{transform:translateY(-3px)}
.card .big{font-size:26px;font-weight:800}.card .lbl{color:var(--dim)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:14px}.panel h3{margin:0 0 10px;font-size:14px}
.hbar{display:flex;align-items:center;gap:10px;margin:5px 0}.hbar .l{width:120px;color:var(--dim)}
.hbar .b{height:14px;border-radius:4px;transition:width .8s cubic-bezier(.2,.9,.3,1.1)}.empty{color:var(--dim);padding:30px;text-align:center}
code{background:#0e1016;border:1px solid var(--line);border-radius:5px;padding:0 4px}
.tgutter{cursor:col-resize;align-self:stretch;border-radius:4px;background:linear-gradient(90deg,transparent 4px,var(--line) 4px,var(--line) 6px,transparent 6px)}
.tgutter:hover,.tgutter.drag{background:linear-gradient(90deg,transparent 3px,var(--pink) 3px,var(--pink) 7px,transparent 7px)}.session-table{overflow-x:auto}
@media(max-width:900px){.tgutter{display:none}}
</style></head><body>
<header><span class="logo">🧭</span><h1>workboard</h1><span class="sub">your tasks across every server and session</span>
<span class="live"><span class="dot" id="dot"></span><span id="when"></span></span></header>
<div class="wrap">
<div class="week" id="week"></div><div class="bar" id="bar"></div>
<div class="tabs"><button class="tab on" data-tab="board" title="Board (b)">📋 Board</button><button class="tab" data-tab="team" title="Team (t)">💬 Team</button><button class="tab" data-tab="stats">📊 Stats</button><span class="keyhelp">/ search · b board · t team · e expand · Esc close</span></div>
<section id="board">
<div class="controls" id="chips"></div>
<div class="controls"><div class="seg" id="owner"></div><select class="kind" id="kind" title="task type"><option value="">🧩 all types</option><option value="multi-turn">🔁 multi-turn</option><option value="single-turn">① single-turn</option></select><input type="search" id="q" placeholder="🔍 search tasks  ( / )"><span class="health" id="health"></span></div>
<div class="tbl"><table><thead><tr>
<th data-k="task" data-h="task">Task</th><th data-k="next" data-h="next">Primary action</th><th data-k="tag" data-h="tag" class="c-status">Status</th>
<th data-k="owner" data-h="owner">Owner</th><th data-k="valid" data-h="valid">Validation</th>
<th data-k="check" data-h="check">Presubmit</th><th data-k="sync" data-h="sync">Server</th><th data-h="tags">Tags</th></tr></thead><tbody id="rows"></tbody></table></div>
<div class="legend"><span><span class="spark">✦</span> changed</span><span><span style="color:#ff4d4d">▌</span> red edge = fix first</span><span>Presubmit: <span class="tk g">✓</span><span class="tk d">○</span> building · independent (○ not run)</span>
<span>Server: <span class="tk g">✓</span><span class="tk r">✘</span> imported · validated</span><span><span class="tk d">✓</span> grey = older commit</span><span>✍ working · 💤 assigned idle · ⏳ pipeline · 🛠 pushed recently · 🔓 free (incl. never worked)</span><span class="dim">local tokens are indexed estimates; hover cells for evidence · click a task for details</span></div>
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
const RK={cat:'category',pa:'primary',g:'group',n:'next',al:'age_level',o:'owner',ch:'claim_health',v:'valid',r:'review',s:'sync',tg:'tag',sr:'status_raw',vd:'validated',ag:'age_label',os:'ownership_state',ow:'ownership_reason',oa:'owner_last_at',k:'kind',vp:'vp',vs:'vsum',old:'older_results',as:'assignee',ep:'entered_pool_at',rhs:'review_history_stale',ss:'state_since',ax:'assignment',ac:'activity',pp:'pipeline',lp:'last_push',gs:'gate_summary',rs:'rsum',rc:'revision_count',ld:'latest_decision',fc:'finding_codes',sy:'sync_summary',lg:'legacy_summary',ta:'tags',kl:'kind_line',lu:'local_usage',dv:'detail_version',rv:'row_version'};
function inflateRow(row){const x=Object.fromEntries(Object.entries(row).map(([k,v])=>[RK[k]||k,v]));if(Array.isArray(x.vsum)){const[p,t,issues,skipped,info]=x.vsum;x.vsum={passed:p,total:t,issues:issues.map(i=>({severity:i[0],check:i[1],why:i[2],fix:'open the task card for full validation detail'})),skipped,info:info.map(i=>({check:i[0],why:i[1]}))}}if(x.gate_summary&&x.gate_summary.a){const g=x.gate_summary;x.gate_summary={author:{check:{state:g.a[0],fail:g.a[1],warn:g.a[2],at:g.a[4],summary:g.a[5]},review:{state:g.a[3]}},independent:{check:{state:g.i[0],fail:g.i[1],warn:g.i[2],at:g.i[4],summary:g.i[5]},review:{state:g.i[3]}}}}if(Array.isArray(x.tags))x.tags=x.tags.map(i=>Array.isArray(i)?{k:i[0],label:i[1],why:i[2]}:i);if(Array.isArray(x.assignment))x.assignment={state:x.assignment[0],owner:x.assignment[1],reason:x.assignment[2]};else if(typeof x.assignment==='string')x.assignment={state:x.assignment};if(Array.isArray(x.activity))x.activity={state:x.activity[0],last_at:x.activity[1],reason:x.activity[2]};if(Array.isArray(x.pipeline))x.pipeline={state:x.pipeline[0],since:x.pipeline[1],reason:x.pipeline[2]};if(Array.isArray(x.last_push))x.last_push={at:x.last_push[0],session_alias:x.last_push[1],time_kind:x.last_push[2]};if(Array.isArray(x.rsum))x.rsum={agent:x.rsum[0],agent_current:x.rsum[1],agent_green:x.rsum[2],human:x.rsum[3]};if(Array.isArray(x.latest_decision))x.latest_decision={kind:x.latest_decision[0],at:x.latest_decision[1],reason:x.latest_decision[2]};if(Array.isArray(x.local_usage))x.local_usage={by_kind:{claude:x.local_usage[0],codex:x.local_usage[1],muse:x.local_usage[2]},total:x.local_usage[3],coverage_pct:x.local_usage[4],approximate:x.local_usage[5]};return x}
const decodeBoard=data=>data.tasks?(data.tasks||[]).map(inflateRow):(data.rows||[]).map(values=>inflateRow(Object.fromEntries((data.fields||[]).map((key,i)=>[key,values[i]]))));D.tasks=decodeBoard(D);
const G = {MINE:['#ff8f6b','🙋','action needed'],READYSUB:['#7bd88f','🚀','ready to submit'],VALIDATING:['#7ab8ff','⏳','server validating'],
 REVIEWING:['#b39dff','👀','with reviewers'],DONE:['#8b90a0','🎉','done']};
const GHELP = {MINE:'Something for you or one of your sessions to do: fix, address feedback, presubmit, review, submit. Broken ones (red edge) come first within each status.',
 READYSUB:'Both presubmits clean and both agent approvals in on the current commit — submit (or resubmit) it.',
 VALIDATING:'Nothing to do — codimango is importing or validating your latest push.',
 REVIEWING:'Nothing to do — submitted and waiting on human reviewers.',DONE:'Accepted, in training or archived.'};
const dg = t => /^(SUBMIT|RESUBMIT)/.test(t.next||'')?'READYSUB':(t.group==='ATTENTION'||t.group==='READY')?'MINE':t.group;
const TAGO = ['Needs revision','Draft','Not imported','Needs reviewers','In review','Accepted','In training','Archived'];
const TAGC = {'Draft':'#e0b860','Needs revision':'#ff875f','Needs reviewers':'#8fb8e0','In review':'#5fafff','Accepted':'#7bd88f','In training':'#5fd7d7',
 'Archived':'#808080','Not imported':'#585858'};
const NEXT = {FIX:'🔧',RESOLVE:'🤺',RERUN:'🔁',SUBMIT:'🚀',RESUBMIT:'🚀',GET:'👀',RUN:'🧪',WAIT:'⏳',ADDRESS:'📝',IMPORT:'📥','—':'🎉'};
const HEAD = {task:'The task folder. Hover a task name for what it is; click for its card with next steps.',
 next:'The one thing to do now, named so it explains itself (e.g. Fix oracle, Calibrate · step 2 too easy, Presubmit · owner, Agent review · 3P, Revalidate on server, Human review · waiting). Red = broken, amber = your move, green = ready to ship, grey = waiting. Hover for why, the exact steps, and the gates that must pass to reach acceptance.',
 tag:'Status in codimango incl. the human review (Draft, Needs revision, Needs reviewers, In review, Accepted, In training, Archived). Underneath: versions.pushes — 1.2 = revision requested once, 2 pushes since — and "overdue" when it has sat too long. Hover for the review history. The board opens sorted by this.',
 owner:'Display state derived from three independent axes: assignment, current activity, and pipeline, plus the latest remote change. Free appears only when every blocker is clear.',
 valid:'codimango validation. Hover shows only the problems and how to fix them.',
 review:'Human review in codimango: ✔ accepted · ✘ needs revision (n times) · 👀 in review · ⌛ waiting for a reviewer · · not submitted. Hover for the last decision.',
 check:'Two presubmits: 1st tick = the session building the task, 2nd = an independent fresh agent. Green ✓ clean on this commit · red ✘ failures · grey = last result is from an older commit (re-run) · ○ = not run. Hover shows what each suggested fixing.',
 tags:'Quick labels: who worked on it in the last 48h (Claude / Codex / Muse), MT/ST, ready / near submit, retire? when an agent suggested parking it, revision rounds, infra-only failures, idle owner.',
 sync:'Two ticks: 1st = codimango has your latest push (grey while importing, amber if it is on an older commit) · 2nd = validated (green passed · red ✘ failed or a reviewer sent it back · grey while running or results are old).'};
const S = {tags:new Set(), groups:new Set(['MINE','READYSUB','VALIDATING']), gfirst:true, kind:'', sig:{}, owner:'all', q:'', sort:'tag', dir:1, first:true, rowh:{}, keys:'', blocks:{},spend:{},
 prev:JSON.parse(localStorage.getItem('wb-prev')||'{}'),etags:D._etags||{},details:{},detailEtags:{},detailRowVersions:{},drawerRowVersion:null,
 teamKeys:'',teamh:{},teamSig:{},activityIds:new Set(),teamReady:false,lastNetworkAt:Date.now()};
const code = s => esc(s).replace(/`([^`]+)`/g,'<code>$1</code>');
const esc = s => String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const age = s => s==null?'?':s<60?'<1m':s<3600?Math.floor(s/60)+'m':s<86400?Math.floor(s/3600)+'h':Math.floor(s/86400)+'d';
const nt = n => n==null?'—':n>=1e9?(n/1e9).toFixed(1)+'b':n>=1e6?(n/1e6).toFixed(1)+'m':n>=1e3?(n/1e3).toFixed(1)+'k':String(n);
const fdate = x => x?new Date(x).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'—';
const elapsed = (at,fallback=null) => at?Math.max(0,(Date.now()-Date.parse(at))/1000):fallback;
const taskAge = t => elapsed(t.state_since,t.state_age_s);
function shortName(value){const whole=String(value||''),raw=whole.split('·').pop().trim(),m=whole.match(/\b([a-z][\w-]*-[0-9a-f]{2,})\b/i);return m?m[1]:(raw.split(/[\s(]/)[0]||'assigned').slice(0,22)}
const kindCue=x=>`${x.kind_icon||'❔'} ${{claude:'C',codex:'X',muse:'M',human:'H',unlinked:'?'}[x.kind]||'?'}`;
const L = (cls,ch,txt) => `<li><span class="b-${cls}">${ch}</span><span>${txt}</span></li>`;
const CH = {ok:'●',pend:'○',bad:'✘',dim:'·',info:'→'};
const tick = (n,green,amber) => n?`<span class="tk ${green?'g':amber?'a':'d'}">${'✓'.repeat(n)}</span>`:'<span class="tk d">✓✓</span>';
function kindLine(t){if(t.kind_line)return t.kind_line;const c=t.category||{};const track=(t.track||'').includes('multi')?'multi-turn':(t.track?'single-turn':'');
 return [track&&('SWE-bench '+track), (c.category||'').replace(/_/g,' '), (c.subdomain||'').replace(/_/g,' '), (c.languages||[]).join('/'), c.difficulty].filter(Boolean).join(' · ')}
function ownerIdle(t){return elapsed(t.owner_last_at)}
function ownState(t){return t.ownership_state||(t.claim_health==='DONE'?'done':t.claim_health==='ACTIVE'?'actively_working':t.claim_health==='OWNED'||t.claim_health==='LEGACY'?'assigned_idle':t.claim_health==='CONFLICT'?'conflict':t.claim_health==='PIPELINE'?'in_pipeline':t.claim_health==='RECENT'?'worked_recently':t.claim_health==='UNSEEN'?'never_seen':'available')}
function ownReason(t){return t.ownership_reason||({done:'task lifecycle is complete',conflict:'more than one assignment is live',actively_working:'recent task activity',in_pipeline:'server work is in progress',assigned_idle:'assignment is live with no recent activity',worked_recently:'remote change within 72 hours',available:'no assignment, activity, pipeline, or recent change',never_seen:'insufficient fresh evidence'}[ownState(t)]||'')}
function assigneeText(t){const s=ownState(t);if(s==='done'||s==='in_pipeline')return'nobody needed right now';if(s==='worked_recently')return'check with '+((t.last_push||{}).session_alias||'the last session')+' first';if(s==='assigned_idle')return(t.owner||'assigned owner')+' — message or take over';if(s==='actively_working')return'keep with '+(t.owner||'the active session');if(s==='available')return'any free session can claim it';return'inspect the three ownership axes first'}
function worker(t,full){const a=((t.activity||{}).aliases||[]).find(x=>x&&!full.includes(String(x).split('·').pop()));return a?` <span class="dim" title="${esc(a)}">· ${esc(String(a).split('·').pop())} working</span>`:''}
function owner(t){const s=ownState(t),full=String(t.owner||''),o=esc(shortName(full));if(s==='done')return'';if(s==='available')return'<span class="info">🔓 free</span>';
 if(s==='actively_working'){const a=((t.active||[])[0]||{}),at=a.at||(t.activity||{}).last_at;return`<span style="color:var(--violet)" title="${esc(full)}">✍ working (${o||'active session'})</span>${worker(t,full)} <span class="dim">· <span class="clock" data-at="${esc(at||'')}" data-fallback="${a.ago_s??''}">—</span> ago</span>`}
 if(s==='in_pipeline')return`<span class="info">⏳ in pipeline</span>${o?' <span class="dim" title="'+esc(full)+'">· '+o+'</span>':''}`;
 if(s==='worked_recently'){const p=(t.last_push||{}).at;return`<span class="run">🛠 pushed <span class="clock" data-at="${esc(p||'')}">—</span> ago</span>`}
 if(s==='never_seen')return'<span class="info">🔓 free</span> <span class="dim">· never worked</span>';
 if(s==='conflict')return`<span class="bad" title="${esc(full)}">⚔ conflict (${o})</span>`;
 if(s==='assigned_idle'){return`<span class="dim" title="${esc(full)}">💤 assigned idle (${o||'assigned'}, idle <span class="clock" data-at="${esc(t.owner_last_at||'')}">—</span>)</span>`}
 return`<span style="color:var(--violet)">👤 ${o}</span>`}
function valid(t){const v=t.vsum;if(t.older_results&&t.valid!=='RUN')return'<span class="run">↻ older commit</span>';const f=v.issues.filter(i=>i.severity==='fail').length,w=v.issues.filter(i=>i.severity==='warn').length;
 if(t.valid==='RUN')return'<span class="run">○ running</span>';if(!v.total)return'<span class="dim">· none yet</span>';
 if(f)return`<span class="bad">✘ ${f} issue${f>1?'s':''}</span>`;if(w)return`<span class="run">▲ ${w} warning${w>1?'s':''}</span>`;return v.info&&v.info.length?'<span class="dim">ⓘ</span>':'<span class="dim">·</span>'}   // only problems are shown
function review(t){const raw=t.status_raw,n=t.revision_count??(t.decisions||[]).filter(d=>d.kind==='revision').length;
 if(raw==='accepted')return'<span class="ok">✔ accepted</span>';if(raw==='used_in_training')return'<span style="color:var(--teal)">✔ in training</span>';
 if(raw==='needs_revision')return`<span class="bad">✘ needs revision${n>1?' '+n+'×':''}</span>`;if(raw==='being_reviewed')return'<span style="color:var(--violet)">👀 in review</span>';
 if(raw==='needs_reviewers_assigned')return'<span class="info">⌛ awaiting reviewer</span>';if(raw==='archived')return'<span class="dim">📦 archived</span>';
 return n?`<span class="dim">· draft (↩${n}×)</span>`:'<span class="dim">· not submitted</span>'}
const TK=(st,glyph)=>st==='ok'?'<span class="tk g">✓</span>':st==='bad'?'<span class="tk r">✘</span>':st==='amber'?'<span class="tk a">✓</span>':st==='none'?'<span class="tk d">○</span>':`<span class="tk d">${glyph||'✓'}</span>`;
function gate(t){return t.gate_summary||(t.rsum&&t.rsum.gates)||{author:{check:{state:'none'},review:{state:'none'}},independent:{check:{state:'none'},review:{state:'none'}}}}
function check(t){const g=gate(t);return ['author','independent'].map(r=>{const c=g[r].check;return c.provisional&&c.state!=='old'?TK('amber',c.fail?'✘':'✓'):TK(c.state,c.state==='old'&&c.fail?'✘':'✓')}).join('')}
function sync(t){const s=t.sync,codes=t.finding_codes||(t.findings||[]).map(f=>f.code);
 // 1st tick: does codimango have your latest push?  2nd tick: is the validation result for that commit?
 const imp=s==='OK'||s==='OK·doc'||s==='STALE_VALID'?'ok':s==='IMPORTING'?'grey':s==='HEAD≠SERVER'?'amber':'none';
 const oldv=s==='IMPORTING'||s==='HEAD≠SERVER'||s==='STALE_VALID'||codes.includes('VALID≠SERVER');
 const bad=t.valid==='FAIL'||t.status_raw==='needs_revision';
 const val=t.valid==='RUN'?'grey':oldv?(t.valid==='PASS'||bad?'grey':'none'):bad?'bad':t.valid==='PASS'?'ok':'none';
 return TK(imp)+TK(val,bad?'✘':'✓')}
const TONE={block:'var(--red)',act:'var(--amber)',ship:'var(--green)',wait:'var(--dim)',done:'var(--dim)'};
function next(t){const p=t.primary;if(p)return `${esc(p.emoji)} <span style="color:${TONE[p.tone]||'var(--amber)'}">${esc(p.label)}</span>`;const n=t.next||'',e=NEXT[n.split(' ')[0]]||'•';const col=n.startsWith('FIX')||n.startsWith('RESOLVE')?'var(--red)':(n.startsWith('SUBMIT')||n.startsWith('RESUBMIT'))?'var(--green)':n.startsWith('WAIT')?'var(--dim)':'var(--amber)';
 return `${e} <span style="color:${col}">${esc(n)}</span>`}
function tag(t){return `<span class="tag" style="background:${TAGC[t.tag]||'#666'}">${esc(t.tag)}</span>${t.status_raw==='being_reviewed'?' <span class="dim">👀</span>':''}<span class="age age2" title="versions.pushes">${esc(t.vp||'')}${t.age_level==='block'?' <span class="bad">· overdue</span>':''}</span>`}
const AGEW={'decided':'decided','submitted':'submitted','in review since (approx.)':'in review','archived':'archived','back in draft since (approx.)':'back','created':'created'};
// ---- hover cards: short, only what matters
function tipTask(t){const c=t.category||{},sent=[c.usecase&&String(c.usecase).replace(/_/g,' '),c.subdomain&&'in '+String(c.subdomain).replace(/_/g,' '),c.difficulty&&'('+c.difficulty+')'].filter(Boolean).join(' ');return `<h4>${esc(t.task)}</h4><ul>${sent?L('ok','✎',esc(sent.charAt(0).toUpperCase()+sent.slice(1))):''}${L('info','◆',esc(kindLine(t)||'no category yet'))}${t.category&&t.category.domain?L('dim','·',esc(t.category.domain)):''}${t.category&&t.category.usecase?L('dim','·',esc(t.category.usecase.replace(/_/g,' '))):''}</ul>`}
const GATE={ok:['ok','✓'],bad:['bad','✘'],wait:['pend','⏳'],todo:['dim','○']};
function gatesList(p){return (p.done_when||[]).map(([st,l])=>L(GATE[st][0],GATE[st][1],esc(l))).join('')}
function tipNext(t){const p=t.primary;if(p){const steps=t.steps||[];return `<h4>${esc(p.emoji)} ${esc(p.label)}</h4><ul>${p.why?L('info','→',code(p.why)):''}${steps.slice(0,4).map(s=>L(s.routine?'dim':'pend','·',`<span class="${s.routine?'dim':''}">${code(s.do)}</span> <span class="dim">${esc(s.eta)}</span>`)).join('')}</ul><h4 style="margin-top:8px">done when · gates to acceptance</h4><ul>${gatesList(p)}</ul>`}
 const steps=t.steps||[];if(!steps.length)return `<h4>next</h4><ul>${L(t.next==='—'?'ok':'pend','→',esc(t.next||'nothing to do'))}${L('dim','·','open the task card for the full ordered steps and ETAs')}</ul>`;return `<h4>next · ETA</h4><ul>${steps.map(s=>L(s.routine?'dim':'pend','→',`<span class="${s.routine?'dim':''}">${code(s.do)}</span> <span class="dim">${esc(s.eta)}</span>`)).join('')||L('ok','●','nothing to do')}</ul>`}
function tipTag(t){let h=`<h4>${esc(t.tag)} · ${esc(t.age_label||'')} ${age(taskAge(t))} ago</h4><ul>`;
 if(t.vp){const [a,b]=t.vp.split('.');h+=L('info','#',`${esc(t.vp)} = ${a==='0'?'never sent back':'revision requested '+a+'×'} · ${b} push${b==='1'?'':'es'} ${a==='0'?'so far':'since the last request'}`)}if(t.entered_pool_at)h+=L('dim','↗','submitted '+fdate(t.entered_pool_at));
 const dec=t.decisions||[t.latest_decision].filter(Boolean);dec.slice(-3).forEach(d=>h+=L(d.kind==='accept'?'ok':'bad',d.kind==='accept'?'✔':'↩',(d.kind==='accept'?'accepted ':'revision requested ')+fdate(d.at)));
 if(t.age_level&&t.age_level!=='ok')h+=L(t.age_level==='block'?'bad':'pend','!',t.age_level==='block'?'overdue for this state':'getting old');return h+'</ul>'}
function tipOwner(t){const a=t.assignment||{},x=t.activity||{},p=t.pipeline||{},s=ownState(t);let h=`<h4>${esc(s.replace(/_/g,' '))} · ${esc(ownReason(t))}</h4><ul>`;
 h+=L(a.state==='claimed'?'ok':'dim','👤',`assignment: ${esc(a.state||t.claim_health||'unknown')}${a.owner?' · '+esc(a.owner):''}`);
 h+=L(x.state==='active'?'ok':'dim','✍',`activity: ${esc(x.state||((t.active||[]).length?'active':'inactive'))}${x.reason?' · '+esc(x.reason):''}`);
 h+=L(p.state&&p.state!=='none'?'pend':'dim','⏳',`pipeline: ${esc(p.state||'none')}${p.reason?' · '+esc(p.reason):''}`);
 if((t.last_push||{}).at)h+=L('dim','🛠',`latest remote change ${fdate(t.last_push.at)} · ${esc(t.last_push.time_kind||'time')}${t.last_push.session_alias?' · last session '+esc(t.last_push.session_alias):''}`);else h+=L('dim','🛠','latest remote change: none observed');
 const lg=t.legacy||t.legacy_summary;if(lg)h+=t.claim_health==='LEGACY'?L('info','📜',`CLAIMS.md: ${esc(lg.legacy_owner)} · ${esc(lg.status)} · ${esc(lg.updated)}`):L('dim','📜',`old CLAIMS.md row (not an active owner): ${esc(lg.legacy_owner)} · ${esc(lg.status)}`);
 h+=L('dim','→',esc(t.assignee||assigneeText(t)));return h+'</ul>'}
function tipValid(t){const v=t.vsum;if(t.older_results)return'<h4>validation</h4><ul>'+L('pend','↻','these results are for an older commit — your latest push has not been validated')+L('info','→','codimango task rerun '+esc(t.task))+'</ul>';if(t.valid==='RUN'&&!v.issues.length)return'<h4>validation</h4><ul>'+L('pend','○','running')+'</ul>';
 const inf=(v.info||[]).map(i=>L('dim','ⓘ',`<b>${esc(i.check)}</b> ${esc(i.why)} (informational, not blocking)`)).join('');
 if(!v.issues.length)return`<h4>validation</h4><ul>${L('ok','●',`${v.total-(v.info||[]).length} of ${v.total} checks clear`)}${inf}</ul>`;
 return `<h4>validation · ${v.passed}/${v.total} clear</h4><ul>${v.issues.map(i=>L(i.severity==='fail'?'bad':'pend',i.severity==='fail'?'✘':'▲',`<b>${esc(i.check)}</b> ${esc(i.why)}<br><span class="dim">→ ${esc(i.fix.replace('{task}',t.task))}</span>`)).join('')}${v.skipped&&v.skipped.length?L('dim','⤷',esc([...new Set(v.skipped)].join(', '))+' skipped until the above passes'):''}${inf}</ul>`}
function tipReview(t){let h=`<h4>human review · ${esc(t.rsum.human)}</h4><ul>`;const decisions=t.decisions||[t.latest_decision].filter(Boolean);
 decisions.slice(-3).forEach(d=>h+=L(d.kind==='accept'?'ok':'bad',d.kind==='accept'?'✔':'↩',`${d.kind==='accept'?'accepted':'revision requested'} ${fdate(d.at)}`));
 const d=decisions[decisions.length-1];if(d&&d.reason)h+=L('dim','“',esc(d.reason.slice(0,140)));
 if(t.review_history_stale)h+=L('pend','↻','review history is refreshing — rounds may be incomplete');
 if(t.entered_pool_at&&!t.decisions.length)h+=t.status_raw==='draft'?L('info','↩','previously submitted '+fdate(t.entered_pool_at)+', back in draft'):L('info','⌛','submitted '+fdate(t.entered_pool_at)+', no decision yet');
 if(!t.entered_pool_at)h+=L('dim','·','not submitted yet');
 const g=gate(t);h+=L(g.author.review.state==='ok'&&g.independent.review.state==='ok'?'ok':'pend','🤖',`required agent approvals: building session ${g.author.review.state==='ok'?'✓':'—'} · independent agent ${g.independent.review.state==='ok'?'✓':'—'}`);return h+'</ul>'}
function tipCheck(t){const g=gate(t);let h='<h4>presubmit · building session + independent agent</h4><ul>';
 [['author','① building session','board check run '+t.task+' --role author'],['independent','② independent agent','fresh agent: board check record '+t.task+' --role independent …']].forEach(([r,l,how])=>{const c=g[r].check;
  if(c.state==='none'){h+=L('dim','·',`${l}: not run <span class="dim">→ ${esc(how)}</span>`);return}
  h+=L(c.state==='ok'?'ok':c.state==='bad'?'bad':'dim',c.fail?'✘':'●',`${l}: ${c.fail?c.fail+' failure(s)':'clean'}${c.warn?', '+c.warn+' warning(s)':''} · ${fdate(c.at)}${c.state==='old'?(c.older_run?' · <b>older validation run (codimango revalidated since) — re-run</b>':' · <b>older commit — re-run</b>'):''}${c.provisional?' · <span class="run">provisional: recorded while validation was still running</span>':''}`);
  if(c.summary)h+=L('info','💡','suggested: '+esc(c.summary))});return h+'</ul>'}
function tipSync(t){const s=t.sync,codes=t.finding_codes||(t.findings||[]).map(f=>f.code);let h='<h4>server · 1st tick imported · 2nd tick validated</h4><ul>';
 if(codes.includes('VALID≠SERVER'))h+=L('pend','↻','validation results are for an older server commit (grey 2nd tick)');
 if(t.valid==='FAIL'){const i=t.vsum.issues.filter(x=>x.severity==='fail');h+=L('bad','✘','validation failed'+(i.length?': '+esc(i.map(x=>x.check).join(', ')):''))}
 if(t.status_raw==='needs_revision')h+=L('bad','✘','reviewer asked for a revision');if(t.valid==='RUN')h+=L('dim','⏳','validating now');
 if(s==='OK'||s==='OK·doc')h+=L('ok','●','server has your latest commit')+L(t.validated?'ok':'pend',t.validated?'●':'○',t.validated?'and validated it':'validation running');
 else if(s==='IMPORTING')h+=L('info','⏳','your push is being imported (a few minutes)');
 else if(s==='STALE_VALID')h+=L('pend','▲','validated an older commit; code changed since')+L('info','→','codimango task rerun');
 else if(s==='HEAD≠SERVER')h+=L('pend','▲',t.sync_summary||((t.findings||[]).find(f=>f.code==='HEAD≠SERVER')||{}).summary||'latest push not on server')+L('info','→','rerun if it does not catch up');
 else h+=L('dim','·','not compared');return h+'</ul>'}
const TAGK={who:'#b39dff',type:'#7ab8ff',stage:'#7bd88f',warn:'#ff875f',info:'#8b90a0'};
function tagsCell(t){return (t.tags||[]).map(x=>`<span class="pill" style="border-color:${TAGK[x.k]};color:${TAGK[x.k]}">${esc(x.label)}</span>`).join('')}
function taskTokens(t){const u=t.local_usage;if(!u||!u.total)return'';const k=u.by_kind||{},mark=u.approximate?'≈, ':'';return `<span class="tokenline">local tokens: Claude ${nt(k.claude||0)} · Codex ${nt(k.codex||0)} · Muse ${nt(k.muse||0)} (${mark}${u.coverage_pct==null?'coverage unavailable':u.coverage_pct+'% attributed'})</span>`}
function tipTags(t){return `<h4>tags</h4><ul>${(t.tags||[]).map(x=>L('info','◆',`<b>${esc(x.label)}</b>${x.why?' — '+esc(x.why):''}`)).join('')||L('dim','·','none')}</ul>`}
const TIPS={tags:tipTags,task:tipTask,next:tipNext,tag:t=>tipTag(t)+tipReview(t),owner:tipOwner,valid:tipValid,review:tipReview,check:tipCheck,sync:tipSync};
function changed(t){const p=S.prev[t.task];return p&&(p.tag!==t.tag||p.valid!==t.valid||p.next!==t.next||p.review!==t.review||p.owner!==t.owner)}
function visible(){return D.tasks.filter(t=>S.groups.has(dg(t))&&(!S.tags.size||S.tags.has(t.tag))&&(!S.kind||t.kind===S.kind)&&
 (S.owner==='all'||(S.owner==='free'?['available','never_seen'].includes(ownState(t)):S.owner==='active'?ownState(t)==='actively_working':S.owner==='claimed'?ownState(t)==='assigned_idle':S.owner==='pipeline'?ownState(t)==='in_pipeline':S.owner==='recent'?ownState(t)==='worked_recently':true))&&
 (!S.q||t.task.includes(S.q.toLowerCase())))}
function setHTML(id,html){if(S.blocks[id]!==html){S.blocks[id]=html;document.getElementById(id).innerHTML=html}}
function rowHtml(t){return `<tr class="row" data-t="${esc(t.task)}" style="--s:${t.group==='ATTENTION'?'#ff4d4d':G[dg(t)][0]}"><td class="task" data-tip="task">${changed(t)?'<span class="spark">✦</span> ':''}${esc(t.task)}${taskTokens(t)}</td>
  <td data-tip="next" class="primary-action">${next(t)}<div class="pa-status">${tag(t)}</div></td><td data-tip="tag" class="c-status">${tag(t)}</td><td data-tip="owner" class="own">${owner(t)}</td><td data-tip="valid">${valid(t)}</td><td data-tip="check">${check(t)}</td><td data-tip="sync">${sync(t)}</td><td data-tip="tags">${tagsCell(t)}</td></tr>`}
function rowSig(t){return [t.next,t.tag,t.valid,t.review,t.owner,t.claim_health,t.ownership_state,t.sync,check(t),sync(t),JSON.stringify(t.local_usage||{})].join('|')}   // flash only on real changes, not ticking ages
function renderBoard(){const counts={};D.tasks.forEach(t=>{if(!S.kind||t.kind===S.kind)counts[dg(t)]=(counts[dg(t)]||0)+1});
 let chips=Object.entries(G).map(([g,[c,e,l]])=>`<button class="chip ${S.groups.has(g)?'':'off'}" data-g="${g}" title="${esc(GHELP[g])}"><span class="c" style="background:${c}"></span><span class="e">${e}</span> ${l} <b>${counts[g]||0}</b></button>`).join('');
 const inGroups=D.tasks.filter(t=>S.groups.has(dg(t))&&(!S.kind||t.kind===S.kind));
 const tagc={};inGroups.forEach(t=>tagc[t.tag]=(tagc[t.tag]||0)+1);[...S.tags].forEach(x=>{if(!tagc[x])S.tags.delete(x)});
 if(!(S.groups.size===1&&S.groups.has('DONE')))chips+=`<span class="sub-chips"><span class="dim">status:</span>${Object.entries(tagc).sort((a,b)=>TAGO.indexOf(a[0])-TAGO.indexOf(b[0])).map(([k,n])=>`<button class="chip ${!S.tags.size||S.tags.has(k)?'':'off'}" data-tagf="${esc(k)}"><span class="c" style="background:${TAGC[k]||'#666'}"></span>${esc(k)} <b>${n}</b></button>`).join('')}${S.tags.size?'<button class="chip" data-tagf="">✕ all</button>':''}</span>`;
 if(!S.gfirst)chips+='<button class="chip" data-greset="1" title="back to the default view">↺ reset</button>';
 setHTML('chips',chips);
 setHTML('owner',['all','free','active','claimed','pipeline','recent'].map(o=>`<button class="${S.owner===o?'on':''}" data-o="${o}">${{all:'👥 all',free:'🔓 free',active:'✍ working',claimed:'💤 assigned idle',pipeline:'⏳ pipeline',recent:'🛠 pushed recently'}[o]}</button>`).join(''));
 setHTML('bar',Object.entries(G).map(([g,[c]])=>`<span style="flex:${counts[g]||0};background:${c}"></span>`).join(''));
 let rows=visible();const order=Object.keys(G);
 const val=t=>{const k=S.sort;return k==='tag'?(TAGO.indexOf(t.tag)<0?99:TAGO.indexOf(t.tag))*1e9+(t.group==='ATTENTION'?0:5e8)-Math.min(taskAge(t)||0,4e8)
  :k==='review'?t.rsum.agent.length:k==='valid'?t.vsum.issues.length:String(t[k]??'')};
 rows=[...rows].sort((a,b)=>order.indexOf(dg(a))-order.indexOf(dg(b))||(S.sort?((val(a)>val(b)?1:val(a)<val(b)?-1:0)*S.dir):0)||a.task.localeCompare(b.task));
 const items=[];let last=null;rows.forEach(t=>{const g=dg(t);if(g!==last){last=g;const[c,e,l]=G[g];items.push(['§'+g,`<tr class="group" data-group="${g}"><td colspan="8" style="border-left:4px solid ${c}" title="${esc(GHELP[g])}">${e} ${l} · ${rows.filter(r=>dg(r)===g).length}</td></tr>`])}
  items.push([t.task,rowHtml(t)])});
 const keys=items.map(x=>x[0]).join('|');const tb=document.getElementById('rows');
 if(S.first||!items.length){                    // first paint / empty state is the only bulk replacement
  tb.classList.toggle('anim',S.first);if(S.first)setTimeout(()=>tb.classList.remove('anim'),1500);tb.innerHTML=items.map(x=>x[1]).join('')||(D.tasks.length?'<tr><td colspan="8" class="empty">No tasks match these filters. Clear search or reset the view.</td></tr>':'<tr><td colspan="8" class="empty">No task data is available yet. Check source health above or run <code>board sync</code>.</td></tr>')}
 else{                                         // keyed reconcile: moves keep the original DOM node identity
  const keyOf=r=>r.dataset.t||(r.dataset.group?'§'+r.dataset.group:'');
  const existing=new Map([...tb.children].map(r=>[keyOf(r),r]).filter(x=>x[0]));[...tb.children].filter(r=>!keyOf(r)).forEach(r=>r.remove());
  items.forEach(([k,h])=>{let n=existing.get(k);if(!n||S.rowh[k]!==h){const tmp=document.createElement('tbody');tmp.innerHTML=h;const fresh=tmp.firstElementChild;if(fresh.classList.contains('row')){const t=rows.find(r=>r.task===k),sg=rowSig(t);if(n&&S.sig[k]!==sg)fresh.classList.add('flash')}if(n)n.remove();n=fresh}tb.appendChild(n);existing.delete(k)});existing.forEach(r=>r.remove())}
 S.keys=keys;S.rowh=Object.fromEntries(items);S.sig=Object.fromEntries(rows.map(t=>[t.task,rowSig(t)]));
 S.first=false;tickClocks();
 document.querySelectorAll('th[data-k]').forEach(th=>{const want=th.textContent.replace(/ [▲▼]$/,'')+(S.sort===th.dataset.k?(S.dir>0?' ▲':' ▼'):'');if(th.textContent!==want)th.textContent=want});
}
function renderSummary(){const W=D.week||{};setHTML('week',`📈 W${W.week??'—'}: <b>${W.this_week??'—'}</b> accepted · last week at this point ${W.same_point_last_week??'—'} · 4-week median ${W.median_4wk??'—'}`);const h=D.health||{};setHTML('health',Object.entries(h).map(([k,v])=>`<span class="${v.ok?'ok':'bad'}">${v.ok?'✔':'✘'} ${k}</span>`).join(' · ')+(D.ledger_ok==null?'':` · <span class="${D.ledger_ok?'ok':'bad'}">${D.ledger_ok?'✔':'✘'} ledger${D.ledger_at?' '+age(elapsed(D.ledger_at))+' ago':''}</span>`)+(D.refresh_error?` · <span class="bad">refresh failing: ${esc(D.refresh_error)}</span>`:''));const stale=D.codimango_at&&elapsed(D.codimango_at)>600;document.getElementById('dot').className='dot'+(Object.values(h).every(v=>v.ok)&&!D.refresh_error&&!stale&&D.ledger_ok!==false?'':' bad');renderWhen()}
function countUp(el){const end=parseFloat(el.dataset.n);if(isNaN(end))return;let s=null;const step=ts=>{s=s||ts;const p=Math.min(1,(ts-s)/700);el.textContent=(end%1?(end*p).toFixed(1):Math.round(end*p));if(p<1)requestAnimationFrame(step)};requestAnimationFrame(step)}
function renderStats(){const w=D.week||{},f=D.funnel||{},fl=D.flow||{},weekly=D.weekly||[],hr=x=>x==null?'—':x>=48?(x/24).toFixed(1)+'d':Math.round(x)+'h';
 const top=Math.max(1,...weekly.map(r=>r.accepted));const ftop=Math.max(1,f.built||0,f.imported||0);const delta=(w.this_week||0)-(w.same_point_last_week||0),td=D.token_daily||[],ttop=Math.max(1,...td.map(r=>r.total||0)),acct=D.token_accounting||{};
 document.getElementById('stats').innerHTML=`<div class="cards">
 <div class="card"><div class="lbl">🏁 accepted this week</div><div class="big ok" data-n="${w.this_week}">${w.this_week}</div><div class="${delta>=0?'ok':'bad'}">${delta>=0?'▲':'▼'} ${Math.abs(delta)} vs last week at this point</div></div>
 <div class="card"><div class="lbl">📅 4-week median</div><div class="big" data-n="${w.median_4wk}">${w.median_4wk}</div></div>
 <div class="card"><div class="lbl">🔄 submit → accepted</div><div class="big">${hr(fl.latest_round_cycle_p50_h)}</div><div class="dim">p75 ${hr(fl.latest_round_cycle_p75_h)}</div></div>
 <div class="card"><div class="lbl">👀 waiting on reviewer</div><div class="big">${hr(fl.wait_p50_h)}</div><div class="dim">p75 ${hr(fl.wait_p75_h)}</div></div>
 <div class="card"><div class="lbl">🏆 all-time accepted</div><div class="big" data-n="${w.total}">${w.total}</div></div></div>
 <div class="panel"><h3>📈 accepted per week <span class="dim">(<span class="ok">■</span> multi-turn <span style="color:var(--teal)">■</span> single-turn)</span></h3>
 ${weekly.map(r=>`<div class="hbar"><span class="l">${r.week}</span><span class="b" style="width:${r.accepted_mt/top*60}%;background:var(--green)"></span><span class="b" style="width:${r.accepted_st/top*60}%;background:var(--teal);margin-left:-10px"></span><b>${r.accepted}</b><span class="dim">↗ ${r.submitted} submitted · ✎ ${r.worked_on} new</span></div>`).join('')}</div>
 <div class="panel"><h3>🧭 funnel</h3>${[['🧱 built',f.built],['📥 imported',f.imported],['📤 submitted',f.submitted],['✅ accepted',f.accepted]].map(([l,v],i,a)=>`<div class="hbar"><span class="l">${l}</span><span class="b" style="width:${v/ftop*70}%;background:var(--violet)"></span><b>${v}</b>${i?`<span class="dim">${Math.round(100*v/(a[i-1][1]||1))}% of previous</span>`:''}</div>`).join('')}
 <div class="dim">📦 archived ${f.archived} · 🔧 open ${f.open}</div></div>
 <div class="panel"><h3>⌁ local tokens by agent kind · last 14 days</h3>${td.some(r=>r.total)?td.map(r=>{const k=r.kinds||{},c=(k.claude||{}).total||0,x=(k.codex||{}).total||0,m=(k.muse||{}).total||0;return`<div class="hbar"><span class="l">${esc(r.day.slice(5))}</span><span class="b" title="Claude ${nt(c)}" style="width:${c/ttop*55}%;background:var(--violet)"></span><span class="b" title="Codex ${nt(x)}" style="width:${x/ttop*55}%;background:var(--green);margin-left:-10px"></span><span class="b" title="Muse ${nt(m)}" style="width:${m/ttop*55}%;background:var(--amber);margin-left:-10px"></span><b>${nt(r.total)}</b><span class="dim">${r.coverage_pct==null?'—':r.coverage_pct+'% attributed'}</span></div>`}).join(''):'<div class="empty">No indexed token usage in the last 14 days.</div>'}
 <div class="dim">🟣 Claude · 🟢 Codex · 🟠 Muse · coverage ${acct.coverage_pct==null?'unavailable':acct.coverage_pct+'%'} · exact ${nt(acct.exact||0)} · medium ${nt(acct.medium||0)} · ambiguous ${nt(acct.ambiguous||0)} · unattributed ${nt(acct.unattributed||0)}</div></div>`;document.querySelectorAll('#stats [data-n]').forEach(countUp)}
function exposeDrawer(refresh){const d=document.getElementById('drawer');if(refresh)return;d.classList.remove('noanim');d.classList.remove('open');d.classList.toggle('wide',!!localStorage.getItem('wb-wide'));void d.offsetWidth;d.classList.add('open')}
function money(x){return x&&x.available?esc(x.label||((x.currency||'')+' '+Number(x.amount||0).toFixed(2))):'cost unavailable'}
function usageSection(t){const u=t.local_usage||{},k=u.by_kind||{},online=t.online_usage||{},tr=online.trials_by_kind||{},cost=t.local_spend||{},oc=online.cost||{},runs=online.run_count==null?'run count loading/unavailable':(online.run_count_bounded?'at least '+online.run_count+' recent':online.run_count)+' run(s)',trials=online.trial_count==null?'trial count unavailable':(online.trial_count_bounded?'at least '+online.trial_count+' recent':online.trial_count)+' trial(s)';return `<div class="sec"><h3>⌁ TOKENS & RUNS</h3><div class="session-detail"><div class="line"><b>local tokens</b> Claude ${nt(k.claude||0)} · Codex ${nt(k.codex||0)} · Muse ${nt(k.muse||0)}${u.total?` · ${u.approximate?'≈ ':''}${u.coverage_pct==null?'coverage unavailable':u.coverage_pct+'% attributed'}`:' · none attributed'}</div><div class="line"><b>local spend</b> ${money(cost)}${cost.reason?' · <span class="dim">'+esc(cost.reason)+'</span>':''}</div><div class="line"><b>online</b> ${runs} · ${trials}${Object.keys(tr).length?' · '+Object.entries(tr).map(([a,b])=>esc(a)+' '+b).join(' · '):''}</div><div class="line"><b>online spend</b> ${money(oc)}${online.error?' · <span class="bad">'+esc(online.error)+'</span>':''}</div><div class="dim">${esc(online.source||'Codimango counts load on drawer open')} · estimates require a private matching price and authoritative token/model data; unknown is never shown as $0.</div></div></div>`}
function drawTaskDrawer(t,refresh){t={steps:[],versions:[],decisions:[],...t,rsum:{bullets:[],...(t.rsum||{})}};const Lk=t.links||{},v=t.vsum||{issues:[],passed:0,total:0};
 const btn=(k,l,p)=>Lk[k]?`<a class="btn ${p?'primary':''}" href="${esc(Lk[k])}" target="_blank" rel="noopener">${l} ↗</a>`:'';
 const html=`<div class="head"><p class="card-title">${Lk.codimango?`<a href="${esc(Lk.codimango)}" target="_blank" rel="noopener" title="open in codimango">${esc(t.task)} ↗</a>`:esc(t.task)}</p><div class="kind">${esc(kindLine(t))}</div>
 <div>${tag(t)} &nbsp; ${next(t)}</div>
 <div class="btns">${btn('codimango','🥭 Open in codimango',1)}${btn('github','🐙 Files at server commit')}${btn('latest','📂 Latest on main')}
 <button class="btn" data-msgtask="${esc(t.task)}">💬 Message the owner</button></div></div>
 <div class="sec next-sec"><h3>🚀 NEXT STEPS</h3>${t.steps.map((s,i)=>`<div class="step ${s.routine?'routine':''}"><span class="n">${i+1}</span><span>${code(s.do)}</span><span class="eta">${esc(s.eta)}</span></div>`).join('')||'<div class="dim">nothing to do 🎉</div>'}
  <div class="who">👤 ${esc(t.assignee)}</div></div>
 ${t.primary?`<div class="sec"><h3>✅ DONE WHEN · gates to acceptance</h3><ul class="lst">${gatesList(t.primary)}</ul></div>`:''}
 ${v.issues.length?`<div class="sec"><h3>⚠ PROBLEMS · ${v.passed}/${v.total} checks clear</h3><ul class="lst">${v.issues.map(i=>L(i.severity==='fail'?'bad':'pend',i.severity==='fail'?'✘':'▲',`<b>${esc(i.check)}</b> ${esc(i.why)} <span class="dim">→ ${esc(i.fix)}</span>`)).join('')}</ul></div>`:''}
 <div class="sec"><h3>👥 REVIEW</h3><ul class="lst">${t.rsum.bullets.map(([k,x])=>L(k,CH[k],esc(x))).join('')}</ul>
  ${t.decisions.length&&t.decisions[t.decisions.length-1].reason?`<div class="dim" style="margin-top:6px">last review: “${esc(t.decisions[t.decisions.length-1].reason)}”</div>`:''}</div>
 ${t.versions.length?`<div class="sec"><h3>🗂 ROUNDS · ${esc(t.vp||'')}</h3><ul class="lst">${t.versions.map((x,i)=>L(x.ended==='accept'?'ok':x.ended?'bad':'pend',x.ended==='accept'?'✔':x.ended?'↩':'✍',
  `<b>${x.label==='now'?'current round':x.label}</b> · ${x.commits} commit${x.commits===1?'':'s'}${x.ended?` · ${x.ended==='accept'?'accepted':'revision requested'} <b>${fdate(x.at)}</b>`:' so far'}${x.reason?`<div class="dim">“${esc(x.reason.slice(0,200))}”</div>`:''}`)).join('')}</ul></div>`:''}
 ${usageSection(t)}
 <div class="sec"><h3>🧪 PRESUBMIT</h3><ul class="lst">${tipCheck(t).replace(/^<h4>.*?<\/h4><ul>|<\/ul>$/g,'')}</ul></div>
 <div class="sec"><h3>🔗 WHO & SERVER</h3><ul class="lst">${tipOwner(t).replace(/^<h4>.*?<\/h4><ul>|<\/ul>$/g,'')}${tipSync(t).replace(/^<h4>.*?<\/h4><ul>|<\/ul>$/g,'')}</ul></div>
 <div class="dim" style="margin-top:10px">terminal: <code>board show ${esc(t.task)}</code></div>`;
 if(refresh&&S.drawerHtml===html)return;S.drawerHtml=html;document.getElementById('dbody').innerHTML=html;exposeDrawer(refresh)}
async function fetchTask(name,tries=2){const headers={},old=S.details[name]&&S.detailEtags[name];if(old)headers['If-None-Match']=old;
 const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),15000);
 try{const r=await fetch('api/task/'+encodeURIComponent(name),{cache:'no-store',headers,signal:ctl.signal});if(r.status===304&&S.details[name])return S.details[name];if(!r.ok)throw Error('HTTP '+r.status);const detail=await r.json();S.details[name]=detail;S.detailEtags[name]=r.headers.get('ETag')||detail.detail_version||'';return detail}
 catch(e){if(tries>1)return fetchTask(name,tries-1);throw Error(e.name==='AbortError'?'timed out after 15s':(e.message||String(e)))}finally{clearTimeout(timer)}}
async function fetchSpend(name){if(!LIVE||S.spend[name])return;S.spend[name]='loading';try{const r=await fetch('api/spend/'+encodeURIComponent(name),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const value=await r.json();S.spend[name]=value;if(S.details[name])S.details[name].online_usage=value;if(S.open===name&&document.getElementById('drawer').classList.contains('open')){const row=D.tasks.find(x=>x.task===name);drawTaskDrawer({...row,...S.details[name]},true)}}catch(e){S.spend[name]={error:e.message||String(e)}}}
async function openDrawer(name,refresh=false,force=false){const row=D.tasks.find(x=>x.task===name);if(!row)return;S.open=name;
 let detail=S.details[name],changed=detail&&S.detailRowVersions[name]!==row.row_version;
 if(!refresh){S.drawerHtml='';drawTaskDrawer(detail?{...row,...detail}:row,false)}   // show what we have at once
 if(LIVE&&(!detail||force||changed)){const note=document.createElement('div');note.className='dim';note.id='dload';note.textContent='loading full details…';
  const body=document.getElementById('dbody');if(!detail&&!refresh&&body.prepend)body.prepend(note);
  try{detail=await fetchTask(name)}catch(e){const n=document.getElementById('dload');if(n){n.className='bad';n.textContent='could not load full details · '+(e.message||e)+' — showing the board row'}return}
  if(S.open!==name)return}
 const t=detail?{...row,...detail}:row;S.detailRowVersions[name]=row.row_version;S.drawerRowVersion=row.row_version||null;drawTaskDrawer(t,true);fetchSpend(name)}
function refreshDrawer(){const d=document.getElementById('drawer');if(!S.open||!d.classList.contains('open'))return;
 const top=d.scrollTop;d.classList.add('noanim');if(S.open.startsWith('session:'))openSession(S.open.slice(8),true);else{const row=D.tasks.find(x=>x.task===S.open),detail=S.details[S.open];if(row&&(detail||!LIVE))drawTaskDrawer(detail?{...row,...detail}:row,true)}d.scrollTop=top}
const HC={};const hostColor=h=>HC[h]||(HC[h]=['#f78fb3','#7ab8ff','#7bd88f','#f5c26b','#b39dff'][Object.keys(HC).length%5]);
function allSessions(){return (D.servers||[]).flatMap(s=>(s.sessions||[]).map(x=>({...x,host:x.host||s.id})))}
function sessionKey(x){return x.session_key||x.native_id}
function sessionByKey(key){return allSessions().find(x=>sessionKey(x)===key||x.native_id===key)}
function hookTransport(x){if(x.is_actor)return'<span class="dim">human shell</span>';if(x.is_summary)return'<span class="dim">no parent</span>';const r=x.restart||{},tr=x.transport||{};
 const h=r.state==='loaded'?'<span class="ok">hooks loaded</span>':r.state==='probably-missing'?'<span class="bad">hooks probably missing</span>':r.state==='not-applicable'?'<span class="dim">hooks n/a</span>':'<span class="dim">hooks unknown</span>';
 return h+' · '+(tr.available?'<span class="ok">'+esc(tr.kind||'transport ready')+'</span>':'<span class="dim">'+esc(tr.kind||'unavailable')+'</span>')}
function tokenText(x,detail=false){const t=x.tokens||{},c=t.context||{},bits=[`${nt(t.total)} ${t.index_complete===false?'indexed so far':'total'}`,`${nt(t.last_hour)} last hour`,c.pressure_pct==null?'context unavailable':`${c.pressure_pct}% context (${nt(c.tokens)} / ${nt(c.window)})`];if(detail&&t.counters){const n=t.counters;bits.push(`input ${nt(n.input)} · output ${nt(n.output)} · cache read ${nt(n.cache_read)} · cache write ${nt(n.cache_write)}${n.reasoning?' · reasoning '+nt(n.reasoning):''}`)}return t.total==null?'tokens unavailable':bits.join(' · ')}
function adviceText(x,detail=false){const a=x.advice||{},icon={keep:'●',watch:'▲',rotate:'↻',unblock:'!'}[a.state]||'·',cls={keep:'ok',watch:'run',rotate:'bad',unblock:'bad'}[a.state]||'dim';return `<span class="${cls}"><b>${icon} ${esc(a.state||'unavailable')}</b></span> · ${esc(a.reason||x.liveness_reason||'')}${detail&&a.action?`<span class="advice-action">→ ${code(a.action)}</span>`:''}`}
function statusText(x,stable=false){const raw=x.status_group==='waiting'?'waiting for permission':x.status||'unknown',fallback=x.status_ago_s==null?x.ago_s:x.status_ago_s,dur=elapsed(x.status_since,fallback);return esc(raw)+(dur==null?'':` · <span class="clock" data-at="${esc(x.status_since||'')}" data-fallback="${x.status_since?'':fallback??''}">${stable?'—':age(dur)}</span>`)}
function childRuns(x){const kids=(x.child_runs||[]).map(r=>`<li>${esc(r.kind_icon||'')} <b>${esc(r.name||r.native_id)}</b> · ${esc(r.status||'unknown')}${r.cwd_task?' · '+esc(r.cwd_task):''}${r.tokens?' · '+tokenText(r):''} <span class="dim">${r.parent_confidence?'· '+esc(r.parent_confidence)+' parent link':''}</span></li>`).join('');
 const old=x.older_child_run_count||x.older_run_count||0;return kids+(old?`<li class="dim">${old} older run(s) counted, not shown</li>`:'')}
function openSession(key,refresh){const x=sessionByKey(key);if(!x)return;S.open='session:'+sessionKey(x);const tr=x.transport||{},r=x.restart||{},f=x.focus||{},tok=x.tokens||{},adv=x.advice||{};
 const resume=r.needed&&r.command?`<div class="sec"><h3>↻ RESUME TO LOAD HOOKS</h3><div class="bad">${esc(r.reason)}</div><code>${esc(r.command)}</code></div>`:'';
 const children=childRuns(x),canMessage=!x.is_summary&&!x.is_actor;
 const compose=canMessage?`<div class="sec"><h3>💬 MESSAGE THIS SESSION</h3><div class="compose"><select id="dmtask">${taskOptions(sessionKey(x),'')}</select><textarea id="dmtext" placeholder="message this session"></textarea><button class="btn primary" data-dsend="${esc(sessionKey(x))}">Send 🚀</button><span id="dmstatus"></span></div></div>`:'';
 const html=`<div class="head"><p class="card-title">${esc(kindCue(x))} ${esc(x.name||x.alias)}</p><div class="kind">${esc(x.kind||'unknown')} · ${esc(x.host||'unknown host')} · ${esc(sessionKey(x))}</div><div>${statusText(x)}</div></div>
 <div class="sec"><h3>◎ STATUS & FOCUS</h3><div class="session-detail"><div class="line"><b>status</b> ${statusText(x)} · <b>session age</b> <span class="clock" data-at="${esc(x.started_at||'')}" data-fallback="${x.age_s??''}">${age(elapsed(x.started_at,x.age_s))}</span></div><div class="line"><b>focus</b> ${esc((x.tasks||[]).join(', ')||'none detected')} · ${esc(f.confidence||'unknown')} confidence${(f.evidence||[]).length?' · '+esc(f.evidence.join(', ')):''}</div><div class="line"><b>liveness</b> ${esc(x.classification||'unknown')} · ${esc(x.liveness_reason||'no native evidence')}</div></div></div>
 <div class="sec"><h3>⌁ TOKENS & CONTEXT</h3><div class="session-detail"><div class="line">${tokenText(x,true)}</div><div class="line"><b>model</b> ${esc(tok.model||x.model||'unavailable')}${tok.effort||x.effort?' · effort '+esc(tok.effort||x.effort):''} · observed ${tok.observed_at?fdate(tok.observed_at):'never'}</div><div class="line"><b>local spend</b> ${money(tok.spend||{})}${tok.spend&&tok.spend.reason?' · <span class="dim">'+esc(tok.spend.reason)+'</span>':''}</div><div class="line"><b>advice</b> ${adviceText(x,true)}</div><div class="dim">watch at 75% context or 1h idle · rotate at 90% context or 3h safely idle · the board never acts automatically</div></div></div>
 <div class="sec"><h3>⌁ HOOKS / TRANSPORT</h3><div class="session-detail"><div class="line">${hookTransport(x)} · ${esc(tr.reason||'')}</div></div></div>
 <div class="sec"><h3>↕ BOARD ACTIVITY</h3><div class="session-detail"><div class="line"><b>last report</b> ${x.last_report?esc(x.last_report.kind)+(x.last_report.task?' · '+esc(x.last_report.task):'')+' · '+fdate(x.last_report.at):'none'}</div><div class="line"><b>last request</b> ${x.last_request?fdate(x.last_request.at)+(x.last_request.task?' · '+esc(x.last_request.task):''):'none'}</div>${children?`<div class="line"><b>child runs</b><ul class="lst">${children}</ul></div>`:''}</div></div>${resume}${compose}`;
 if(refresh&&S.drawerHtml===html)return;S.drawerHtml=html;document.getElementById('dbody').innerHTML=html;const d=document.getElementById('drawer');if(refresh)return;d.classList.remove('noanim');d.classList.remove('open');d.classList.toggle('wide',!!localStorage.getItem('wb-wide'));void d.offsetWidth;d.classList.add('open')}
function deliveryLabel(m){const d=(m.delivery||{}).state||'published',n=((m.delivery||{}).recipients||[]).length;return d==='acked'?'<span class="ok">✓ acked</span>':d==='delivered'?'<span class="ok">✓ delivered</span>':d==='failed'?'<span class="bad">✘ failed</span>':d==='queued'?'<span class="run">queued locally</span>':`<span class="run">published${n?' · '+n+' recipient(s)':''}</span>`}
function taskOptions(to,selected){let tasks=[];if(to.startsWith('task:'))tasks=[to.slice(5)];else{const s=(D.session_targets||[]).find(x=>x.session_key===to||x.native_id===to);tasks=(s&&s.tasks)||[]}
 return `<option value="">no task</option>${tasks.length>1?'<option value="__all__">all this session’s tasks</option>':''}${tasks.map(t=>`<option ${t===selected?'selected':''} value="${esc(t)}">${esc(t)}</option>`).join('')}`}
function updateComposeTasks(selected){const to=document.getElementById('mto'),task=document.getElementById('mtask');if(to&&task)task.innerHTML=taskOptions(to.value,selected||'')}
function serverCards(){return (D.servers||[]).map(s=>{const c=s.status_counts||{},sa=elapsed(s.last_sync_at,s.last_sync_ago_s),aa=elapsed(s.last_activity_at,s.last_activity_ago_s),fresh=sa!=null&&sa<600;return`<div class="srv"><h3><span class="badge" style="background:${hostColor(s.id)}">${esc(s.id)}</span> server
  <span class="dim">· heartbeat ${sa==null?'never':`<span class="clock" data-at="${esc(s.last_sync_at||'')}" data-fallback="${sa}">${age(sa)}</span> ago`}</span>
  <span class="${fresh?'ok':'bad'}">${sa==null?'● never synced':fresh?'● sync fresh':'● sync stale'}</span></h3>
  <div>${s.session_count||0} session(s) · <span class="ok">${c.busy||0} busy</span> · <span class="run">${c.waiting||0} waiting</span> · ${c.idle||0} idle · ${c.unknown||0} unknown</div>
  <div class="dim">queue ${s.queue||0} · ${(s.owned||[]).length} assigned task(s)${aa!=null?` · ledger activity <span class="clock" data-at="${esc(s.last_activity_at||'')}" data-fallback="${aa}">${age(aa)}</span> ago`:''}${s.human_actor_count?' · '+s.human_actor_count+' human actor(s)':''}</div>
  ${s.sync_error?`<div class="bad">last sync failed: ${esc(s.sync_error)}</div>`:''}${sa==null?`<div class="bad">${esc(s.id)} has never synced — run <code>board status</code> there</div>`:!fresh?`<div class="bad">${esc(s.id)} has not synced for <span class="clock" data-at="${esc(s.last_sync_at||'')}" data-fallback="${sa}">${age(sa)}</span> — run <code>board status</code> there</div>`:''}</div>`}).join('')}
function sessionRow(x){return `<tr class="srow" data-session="${esc(sessionKey(x))}"><td>${esc(kindCue(x))}</td><td><b>${esc(x.name||x.alias)}</b><div class="dim">${esc(x.host||'')} · ${hookTransport(x)}</div></td><td>${statusText(x,true)}</td><td class="focus">${esc((x.tasks||[]).join(', ')||'—')}${x.child_runs&&x.child_runs.length?`<div class="dim">${x.child_runs.length} child run(s)${x.older_child_run_count?' · '+x.older_child_run_count+' older':''}</div>`:''}</td><td>${tokenText(x)}</td><td class="advice">${adviceText(x,true)}</td></tr>`}
function sessionItems(){const order=['waiting','busy','idle','unknown'],labels={waiting:'waiting for permission',busy:'busy',idle:'idle',unknown:'unknown'},items=[];order.forEach(g=>{const xs=allSessions().filter(x=>(x.status_group||'unknown')===g).sort((a,b)=>String(a.name||a.alias).localeCompare(String(b.name||b.alias)));if(!xs.length)return;items.push(['§'+g,`<tr class="sgroup" data-session-group="${g}"><td colspan="6">${esc(labels[g])} · ${xs.length}</td></tr>`]);xs.forEach(x=>items.push([sessionKey(x),sessionRow(x)]))});return items}
function activityItem(f,i=0){return `<div class="fi" data-activity="${esc(f.id||f.at+'|'+f.who+'|'+f.task)}" style="animation-delay:${Math.min(i*8,300)}ms"><span class="t">${new Date(f.at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</span><span><span class="badge" style="background:${hostColor(f.host)}">${esc(f.host)}</span></span><span>${esc(f.what)} ${f.task?'<b>'+esc(f.task)+'</b>':''}<div class="w">${esc(f.who)}</div></span></div>`}
function patchActivity(){const box=document.getElementById('activityitems');if(!box)return;const items=D.feed||[];if(!S.activityIds.size){box.innerHTML=items.map(activityItem).join('')||'<div class="dim">quiet</div>';items.forEach(f=>S.activityIds.add(f.id||f.at+'|'+f.who+'|'+f.task));return}const fresh=items.filter(f=>!S.activityIds.has(f.id||f.at+'|'+f.who+'|'+f.task));[...fresh].reverse().forEach(f=>{const id=f.id||f.at+'|'+f.who+'|'+f.task;box.insertAdjacentHTML('afterbegin',activityItem(f));S.activityIds.add(id)});while(box.children&&box.children.length>150)box.lastElementChild.remove()}
function renderComposer(){let me=localStorage.getItem('wb-to')||'all';const base=[{v:'all',l:'📣 everyone'},...(D.servers||[]).map(s=>({v:s.id,l:'🖥 server '+s.id}))],ses=(D.session_targets||[]).map(s=>({v:s.session_key,l:(s.kind_icon||'')+' '+s.name+' · '+s.host+((s.tasks||[]).length?' · '+s.tasks.length+' task(s)':''),g:'Sessions'})),tasks=Object.entries(D.task_targets||{}).filter(([t,r])=>r.state==='resolved').sort().map(([t,r])=>({v:'task:'+t,l:'◆ '+t+' → '+r.label+' · '+(r.host||'?'),g:'Task owner'})),allopts=[...base.map(o=>({...o,g:'Broadcast'})),...ses,...tasks];if(!allopts.some(x=>x.v===me))me='all';const opts=['Broadcast','Sessions','Task owner'].map(g=>{const os=allopts.filter(o=>o.g===g);return os.length?`<optgroup label="${g}">`+os.map(o=>`<option ${o.v===me?'selected':''} value="${esc(o.v)}">${esc(o.l)}</option>`).join('')+'</optgroup>':''}).join(''),host=document.getElementById('composer');if(!host)return;if(!document.getElementById('mto'))host.innerHTML=`<div class="compose"><select id="mto">${opts}</select><select id="mtask">${taskOptions(me,'')}</select><textarea id="mtext" placeholder="e.g. please finish the current check, then acknowledge this message"></textarea><button class="btn primary" id="msend">Send 🚀</button><span id="mstatus"></span></div>`;else{const to=document.getElementById('mto'),task=document.getElementById('mtask'),selected=to.value||me,chosen=task.value,text=document.getElementById('mtext').value;to.innerHTML=opts;to.value=allopts.some(x=>x.v===selected)?selected:me;updateComposeTasks(chosen);document.getElementById('mtext').value=text}}
function renderTeam(){if(!S.teamReady){document.getElementById('team').innerHTML=`<div class="server-grid" id="servercards"></div><div class="team"><div class="team-side"><div class="panel"><h3>💬 send a message</h3><div class="dim" style="margin-bottom:6px">Queued locally → published → delivered by courier/hook → explicitly acked. Start one normal Claude session with <code>board courier</code>; it waits without model tokens. Keep it open while sessions that started before the board hooks still need messages; stop it once they have been resumed. Task targets pin the displayed owner.</div><div id="composer"></div></div><div class="panel feed"><h3>🕒 activity across servers · 24h</h3><div id="activityitems"></div></div><div class="panel"><h3>📨 messages</h3><div id="teammessages"></div></div></div><div class="tgutter" id="tgutter" title="drag to resize"></div><div><div class="panel"><h3>sessions · click one for evidence and controls</h3><div class="session-table"><table><thead><tr><th>kind</th><th title="hooks / transport are summarized here and explained in the drawer">session</th><th>status · for</th><th title="focus tasks from explicit check-in, tool path, or cwd">focus</th><th title="indexed total · last hour · current context pressure">tokens</th><th>recommended action</th></tr></thead><tbody id="sessionrows"></tbody></table></div><div id="sessiondiags"></div></div><div class="panel"><h3>📋 session hygiene</h3><div class="dim">Advice uses context pressure, idle time, unresolved ownership, local/server drift, permission waits, and hook evidence. It never rotates or restarts a session. Hooks are loaded only when a hook-sourced event was observed in seven days.</div></div></div></div>`;S.teamReady=true}
 setHTML('servercards',serverCards());const items=sessionItems(),keys=items.map(x=>x[0]).join('|'),tb=document.getElementById('sessionrows'),keyOf=r=>r.dataset.session||('§'+(r.dataset.sessionGroup||'')),empty='<tr><td colspan="6" class="empty">No live sessions were discovered. Check the server cards and excluded records, then run <code>board status</code> on a stale host.</td></tr>';if(!S.teamKeys){tb.innerHTML=items.map(x=>x[1]).join('')||empty}else{const existing=Object.fromEntries([...tb.children].map(r=>[keyOf(r),r])),wanted=[];items.forEach(([k,h])=>{let node=existing[k];if(!node||S.teamh[k]!==h){const tmp=document.createElement('tbody');tmp.innerHTML=h;const fresh=tmp.firstElementChild;if(node)node.replaceWith(fresh);node=fresh}S.teamh[k]=h;wanted.push(node)});[...tb.children].forEach(node=>{if(!items.some(([k])=>k===keyOf(node)))node.remove()});wanted.forEach(node=>tb.appendChild(node));if(!items.length)tb.innerHTML=empty}S.teamKeys=keys;S.teamh=Object.fromEntries(items);
 const diags=(D.servers||[]).flatMap(s=>(s.session_diagnostics||[]).map(d=>`${s.id}: ${d.classification} · ${d.reason}`));setHTML('sessiondiags',diags.length?`<details class="diag"><summary class="dim">${diags.length} excluded/error record(s)</summary><div class="dim">${diags.map(esc).join('<br>')}</div></details>`:'');renderComposer();const msgs=(D.messages||[]).slice(-30).reverse().map(m=>`<div class="msg ${m.from.includes('dashboard')?'me':''}"><div class="meta">${esc(m.from)} → <b>${esc(m.to_label)}</b>${m.task?' · '+esc(m.task):''} · ${fdate(m.at)} · ${deliveryLabel(m)}</div><div>${esc(m.text)}</div></div>`).join('')||'<div class="dim">no messages yet</div>';setHTML('teammessages',msgs);patchActivity();tickClocks()}
async function sendMsg(){const to=document.getElementById('mto').value,text=document.getElementById('mtext').value,rawTask=document.getElementById('mtask').value,task=rawTask==='__all__'?'':rawTask;
 const st=document.getElementById('mstatus');if(!LIVE){st.innerHTML='<span class="bad">sending needs the live page (board serve)</span>';return}
 st.textContent='sending…';localStorage.setItem('wb-to',to);
 try{const r=await fetch('api/msg',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({to,text,task})});const j=await r.json();
  st.innerHTML=j.ok?`<span class="sent">✓ ${esc(j.state||'queued')} for ${esc(j.to)} — delivery is recorded separately</span>`:`<span class="bad">${esc(j.error)}</span>`;
  if(j.ok)document.getElementById('mtext').value=''}catch(e){st.innerHTML='<span class="bad">failed</span>'}}
async function sendDrawerMsg(to){const text=document.getElementById('dmtext').value,rawTask=document.getElementById('dmtask').value,task=rawTask==='__all__'?'':rawTask,st=document.getElementById('dmstatus');
 if(!LIVE){st.innerHTML='<span class="bad">sending needs the live page (board serve)</span>';return}st.textContent='sending…';
 try{const r=await fetch('api/msg',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({to,text,task})}),j=await r.json();st.innerHTML=j.ok?`<span class="sent">✓ ${esc(j.state||'queued')}</span>`:`<span class="bad">${esc(j.error)}</span>`;if(j.ok)document.getElementById('dmtext').value=''}catch(e){st.innerHTML='<span class="bad">failed</span>'}}
function render(){renderSummary();renderBoard();if(!document.getElementById('stats').hidden&&Object.keys(D.funnel||{}).length)renderStats();if(!document.getElementById('team').hidden)renderTeam()}
function renderWhen(){const ageS=D.codimango_at?Math.max(0,(Date.now()-new Date(D.codimango_at))/1000):null;
 const exact=s=>s==null?'?':s<3600?Math.round(s/60)+'m':Math.floor(s/3600)+'h'+String(Math.round(s%3600/60)).padStart(2,'0')+'m';
 document.getElementById('when').textContent=(LIVE?'live · ':'')+'codimango data '+exact(ageS)+' old'+(D.codimango_detail&&D.health&&D.health.codimango&&!D.health.codimango.ok?' — '+D.codimango_detail:'')+' · last changed region '+exact(Math.max(0,(Date.now()-S.lastNetworkAt)/1000))+' ago';
}
function tickClocks(){document.querySelectorAll('.clock').forEach(el=>{const v=elapsed(el.dataset.at,el.dataset.fallback===''?null:Number(el.dataset.fallback));el.textContent=age(v)});renderWhen()}
function applyRegion(name,data){if(name==='summary'){Object.assign(D,data);renderSummary()}else if(name==='board'){const open=S.open&&!String(S.open).startsWith('session:')?S.open:null,oldRow=open?(D.tasks||[]).find(x=>x.task===open):null;D.tasks=decodeBoard(data);renderBoard();const newRow=open?D.tasks.find(x=>x.task===open):null,visible=document.getElementById('drawer').classList.contains('open');if(visible&&open&&newRow&&(!oldRow||oldRow.row_version!==newRow.row_version))openDrawer(open,true,true)}else if(name==='team'){Object.assign(D,data);if(!document.getElementById('team').hidden){renderTeam();if(S.open&&String(S.open).startsWith('session:'))refreshDrawer()}}else if(name==='activity'){D.feed=data.items||[];if(!document.getElementById('team').hidden)patchActivity()}else if(name==='stats'){Object.assign(D,data);if(!document.getElementById('stats').hidden)renderStats()}}
async function pollRegion(name){const headers={},old=S.etags[name];if(old)headers['If-None-Match']=old;try{const r=await fetch('api/regions/'+name,{cache:'no-store',headers});if(r.status===304)return false;if(!r.ok)throw Error('HTTP '+r.status);const data=await r.json();S.etags[name]=r.headers.get('ETag')||'';S.lastNetworkAt=Date.now();applyRegion(name,data);return true}catch(_){document.getElementById('dot').className='dot bad';return false}}
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
document.addEventListener('click',e=>{const dr=document.getElementById('drawer');   // any click outside an open card closes it
 if(e.isTrusted&&dr.classList.contains('open')&&!dr.contains(e.target)&&!e.target.closest('[data-tab],#composer,.team-side')&&!e.target.closest('#tip,select,input,textarea,#grip,[data-msgtask],[data-msgsession]')){dr.classList.remove('open');S.open=null;e.stopPropagation();return}
 const g=e.target.closest('[data-g]'),dd=e.target.closest('[data-d]'),o=e.target.closest('[data-o]'),r=e.target.closest('tr.row'),sr=e.target.closest('tr.srow'),tb=e.target.closest('[data-tab]'),th=e.target.closest('th[data-k]');
 if(tip.contains(e.target))return;
 if(g){const k=g.dataset.g;if(S.gfirst){S.groups=new Set([k]);S.gfirst=false}else{S.groups.has(k)?S.groups.delete(k):S.groups.add(k);if(!S.groups.size)S.groups.add(k)}
  renderBoard();const n=document.querySelector(`[data-g="${k}"]`);n&&n.classList.add('pop')}
 if(e.target.closest('[data-greset]')){S.groups=new Set(['MINE','READYSUB','VALIDATING']);S.gfirst=true;S.tags.clear();renderBoard()}
 const tf=e.target.closest('[data-tagf]');if(tf){const k=tf.dataset.tagf;if(!k)S.tags.clear();else S.tags.has(k)?S.tags.delete(k):S.tags.add(k);renderBoard()}
 if(o){S.owner=o.dataset.o;renderBoard()}if(r)openDrawer(r.dataset.t);if(sr)openSession(sr.dataset.session);
 if(th){const k=th.dataset.k;if(S.sort!==k){S.sort=k;S.dir=1}else if(S.dir>0)S.dir=-1;else S.sort=null;renderBoard()}
 if(tb){document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x===tb));['board','team','stats'].forEach(k=>document.getElementById(k).hidden=tb.dataset.tab!==k);
  if(tb.dataset.tab==='stats'){document.getElementById('stats').innerHTML='<div class="empty">loading stats…</div>';pollRegion('stats')}if(tb.dataset.tab==='team'){renderTeam();pollRegion('team');pollRegion('activity')}}
 if(e.target.id==='msend')sendMsg();
 const ds=e.target.closest('[data-dsend]');if(ds)sendDrawerMsg(ds.dataset.dsend);
 if(e.target.id==='expand'){const d=document.getElementById('drawer');d.style.width='';localStorage.removeItem('wb-w');d.classList.toggle('wide');localStorage.setItem('wb-wide',d.classList.contains('wide')?'1':'')}
 const mt=e.target.closest('[data-msgtask]');if(mt){document.querySelector('[data-tab=team]').click();const t=D.tasks.find(x=>x.task===mt.dataset.msgtask);
  setTimeout(()=>{const sel=document.getElementById('mto');sel.value='task:'+mt.dataset.msgtask;updateComposeTasks(mt.dataset.msgtask);document.getElementById('mtask').value=mt.dataset.msgtask;document.getElementById('mtext').focus()},50)}
 const ms=e.target.closest('[data-msgsession]');if(ms){const sel=document.getElementById('mto');if(sel){sel.value=ms.dataset.msgsession;updateComposeTasks();document.getElementById('mtext').focus()}}
 if(e.target.id==='close')document.getElementById('drawer').classList.remove('open')});
(()=>{const g=document.getElementById('grip'),d=document.getElementById('drawer');let on=false;
 g.addEventListener('mousedown',e=>{on=true;g.classList.add('drag');e.preventDefault()});
 document.addEventListener('mousemove',e=>{if(!on)return;const w=Math.max(360,Math.min(innerWidth-40,innerWidth-e.clientX));d.classList.remove('wide');d.style.width=w+'px'});
 document.addEventListener('mouseup',()=>{if(!on)return;on=false;g.classList.remove('drag');localStorage.setItem('wb-w',d.style.width)});
 const w=localStorage.getItem('wb-w');if(w)d.style.width=w})();
(()=>{let on=false;const team=()=>document.querySelector('#team .team');
 document.addEventListener('mousedown',e=>{if(e.target.id==='tgutter'){on=true;e.target.classList.add('drag');e.preventDefault()}});
 document.addEventListener('mousemove',e=>{if(!on||!team())return;const r=team().getBoundingClientRect();const w=Math.max(300,Math.min(r.width-440,e.clientX-r.left));team().style.setProperty('--tl',w+'px')});
 document.addEventListener('mouseup',()=>{if(!on)return;on=false;const g=document.getElementById('tgutter');g&&g.classList.remove('drag');const t=team();t&&localStorage.setItem('wb-tl',t.style.getPropertyValue('--tl'))});
 new MutationObserver(()=>{const t=team(),w=localStorage.getItem('wb-tl');if(t&&w&&!t.style.getPropertyValue('--tl'))t.style.setProperty('--tl',w)}).observe(document.getElementById('team'),{childList:true})})();
document.getElementById('q').addEventListener('input',e=>{S.q=e.target.value;renderBoard()});
document.getElementById('kind').addEventListener('change',e=>{S.kind=e.target.value;renderBoard()});
document.addEventListener('change',e=>{if(e.target.id==='mto'){localStorage.setItem('wb-to',e.target.value);updateComposeTasks()}});
document.addEventListener('keydown',e=>{const typing=['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)||document.activeElement.isContentEditable;
 if(e.key==='/'&&!typing){e.preventDefault();document.getElementById('q').focus()}
 if(e.key==='e'&&!typing&&document.getElementById('drawer').classList.contains('open')){document.getElementById('expand').click()}
 if(!typing&&e.key.toLowerCase()==='t')document.querySelector('[data-tab=team]').click();
 if(!typing&&e.key.toLowerCase()==='b')document.querySelector('[data-tab=board]').click();
 if(e.key==='Escape'){const drawer=document.getElementById('drawer');if(drawer.classList.contains('open'))drawer.classList.remove('open');else if(S.q){document.getElementById('q').value='';S.q='';renderBoard()}tip.classList.remove('on')}});
window.addEventListener('beforeunload',()=>localStorage.setItem('wb-prev',JSON.stringify(Object.fromEntries(D.tasks.map(t=>[t.task,{tag:t.tag,valid:t.valid,next:t.next,review:t.review,owner:t.owner}])))));
render();
if(LIVE){const vis=()=>!document.hidden;   // never poll a hidden tab; catch up once when it becomes visible again
 setInterval(()=>{if(vis()){pollRegion('summary');pollRegion('board')}},60000);setInterval(()=>{if(vis()&&!document.getElementById('team').hidden)pollRegion('team')},20000);setInterval(()=>{if(vis()&&!document.getElementById('team').hidden)pollRegion('activity')},30000);setInterval(()=>{if(vis()&&!document.getElementById('stats').hidden)pollRegion('stats')},300000);
 document.addEventListener('visibilitychange',()=>{if(vis()){pollRegion('summary');pollRegion('board');if(!document.getElementById('team').hidden){pollRegion('team');pollRegion('activity')}}})}
setInterval(tickClocks,15000);
</script></body></html>
"""
