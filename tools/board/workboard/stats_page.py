"""Stats v2 window: CSS + JS injected into the inline page. Pure SVG, no libraries.

Design: /tmp/wb-review/stats/04-design.md. The server sends one compact per-task fact table (`D.s2`, built by
stats2.py); everything below aggregates it locally for any range / grain / filter, so filters are instant.
Every chart: one value axis, a legend for 2+ series, hover tooltip, a Chart|Table toggle and a footer line
(date meaning · freshness · coverage · exact/estimated).
"""

STATS_CSS = r"""
#stats{--agent-claude:#9085e9;--agent-codex:#199e70;--agent-muse:#d95926;--agent-human:#3987e5;--agent-unknown:#8a8fa0}
.s2top{position:sticky;top:0;z-index:5;background:var(--bg);padding-bottom:4px}.s2views{display:flex;gap:6px;padding:8px 0 4px;flex-wrap:wrap}
.s2views button{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:18px;padding:6px 14px;font-size:13px;cursor:pointer}.s2views button.on{background:#7ab8ff22;border-color:#7ab8ff;color:#7ab8ff}
.s2lab{color:var(--dim);font-size:11px;margin:0 2px 0 6px;text-transform:uppercase;letter-spacing:.05em}.s2basis button{border-radius:14px}
.s2qline{font-size:11.5px;color:var(--dim);margin:6px 0}.s2qline span{cursor:help}.s2dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-left:2px;vertical-align:1px}
.s2bar{background:var(--bg);display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line)}
.s2bar select,.s2bar input,.s2bar button{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:6px;padding:4px 7px;font-size:12px}
.s2bar button.on{border-color:#7ab8ff;color:#7ab8ff}.s2bar .tz{margin-left:auto;color:var(--dim);font-size:11px}
.s2q{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin:8px 0}.s2q div{min-width:0;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:6px 8px;font-size:12px}
.s2q b{font-weight:600}.s2q .why{color:var(--dim);font-size:11px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.s2h{margin:16px 0 6px;font-size:14px;color:var(--text);letter-spacing:.02em}.s2h small{color:var(--dim);font-weight:400}
.s2k{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.s2k .kp{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px;cursor:pointer}
.s2k .kp.on{box-shadow:inset 0 3px 0 #7ab8ff}.s2k .v{font-size:28px;font-weight:650;line-height:1.1}.s2k .l{color:var(--dim);font-size:12px}.s2k .d{font-size:11px;color:#c3c2b7;margin-top:3px}
.s2g{display:grid;grid-template-columns:repeat(12,1fr);gap:10px;margin-top:10px;align-items:start}.s2f{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px;min-width:0}
.s2f h4{margin:0 0 2px;font-size:13px;font-weight:600}.s2f .sub{color:var(--dim);font-size:11px;margin-bottom:6px}.s2f .ctl{float:right;display:flex;gap:4px}
.s2f .ctl button,.s2f .ctl select{background:transparent;color:var(--dim);border:1px solid var(--line);border-radius:5px;font-size:11px;padding:2px 6px}.s2f .ctl button.on{color:#7ab8ff;border-color:#7ab8ff}
.s2f .foot{color:var(--dim);font-size:10.5px;margin-top:6px;border-top:1px solid var(--line);padding-top:4px}
.s2f svg{display:block;width:100%;overflow:visible}.s2f svg text{fill:#c3c2b7;font-size:10.5px}.s2f svg .ax{stroke:var(--line)}.s2f svg .base{stroke:#383835}
.s2f table{width:100%;border-collapse:collapse;font-size:11.5px}.s2f th{color:var(--dim);font-weight:500;text-align:left;border-bottom:1px solid var(--line);padding:3px 5px;position:sticky;top:0;background:var(--panel)}
.s2f td{padding:3px 5px;border-bottom:1px solid #20242e;vertical-align:top}.s2f .scroll{max-height:420px;overflow:auto}
.s2leg{display:flex;flex-wrap:wrap;gap:10px;font-size:11px;color:#c3c2b7;margin:2px 0 4px}.s2leg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:-1px}
.s2leg span{cursor:pointer}.s2leg span.off{opacity:.35}
.s2note{color:var(--dim);font-size:12px;padding:18px 6px;text-align:center}.s2warn{color:#fab219}
#s2tip{position:fixed;z-index:50;pointer-events:none;background:#0f1116;border:1px solid var(--line);border-radius:6px;padding:6px 8px;font-size:11.5px;color:var(--text);max-width:320px;display:none;box-shadow:0 4px 18px #0008}
.s2m td.c{white-space:nowrap;font-size:10.5px}.s2m .chip{display:inline-block;padding:0 4px;border-radius:3px;margin:1px;background:#20242e}
.s2m tr:hover td{background:#20242e;cursor:pointer}.s2m td:first-child,.s2m th:first-child{position:sticky;left:0;background:var(--panel);z-index:1}.s2sw{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}
@media(max-width:1200px){.s2q,.s2k{grid-template-columns:repeat(3,1fr)}.s2g>.s2f{grid-column:1/-1!important}}
"""

STATS_JS = r"""
const S2C={claude:'#9085e9',codex:'#199e70',muse:'#d95926',human:'#3987e5',other:'#d55181',unknown:'#8a8fa0'};
const S2P={sourcing:'#3987e5',drafting:'#d95926',calibration:'#199e70',presubmit:'#c98500',independent_review:'#d55181',revision:'#008300',draft_fixing:'#9085e9',validation_babysit:'#e66767',submit:'#7ab8ff',unclassified:'#8a8fa0'};
const S2L={created:['#8a8fa0','○','Created'],worked_on:['#3987e5','✎','Worked on'],submitted:['#7ab8ff','◆','Submitted'],first_submitted:['#7ab8ff','◆','First submitted'],accepted:['#0ca30c','✓','Accepted'],atr:['#5fd7d7','✓','Auto-accepted'],revision:['#ec835a','↩','Revision requested']};
const PHN={sourcing:'sourcing',drafting:'drafting',calibration:'calibration',presubmit:'presubmit (owner)',independent_review:'independent review',revision:'revision',draft_fixing:'draft fixing',validation_babysit:'validation babysit',submit:'submit',unclassified:'unclassified'};
const SEQ=['#20242e','#184f95','#256abf','#3987e5','#86b6ef'];
const SS={view:'throughput',linemode:'cum',showRoster:false,range:'8w',grain:'week',compare:'same',basis:'accepted',kind:'',repo:'',agent:'',from:'',to:'',dim:'k',barmode:'grouped',rweek:'',rout:'all',mweeks:12,tables:{},hidden:{}};
function s2esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
let S2TZ='America/Los_Angeles',S2DF=null,S2TF=null;
function s2fmt(d){const p={};for(const x of S2DF.formatToParts(d))p[x.type]=x.value;return `${p.year}-${p.month}-${p.day}`}
const S2DK=new Map();function dkey(iso){if(!iso)return null;let k=S2DK.get(iso);if(k!==undefined)return k;const d=new Date(iso);k=isNaN(d)?null:s2fmt(d);S2DK.set(iso,k);return k}
const S2TOD=new Map();function tod(iso){if(!iso)return 0;let v=S2TOD.get(iso);if(v!==undefined)return v;const p={};for(const x of S2TF.formatToParts(new Date(iso)))p[x.type]=x.value;v=((+p.hour%24)*3600+(+p.minute)*60+(+p.second));S2TOD.set(iso,v);return v}
function nowTod(){return tod(new Date().toISOString())}
function dadd(k,n){const d=new Date(k+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)}
const S2WK=new Map();function wkey(k){let v=S2WK.get(k);if(v)return v;const d=new Date(k+'T12:00:00Z');const wd=(d.getUTCDay()+6)%7;v=dadd(k,-wd);S2WK.set(k,v);return v}
function mkey(k){return k.slice(0,7)}
function bkey(k){return SS.grain==='day'?k:SS.grain==='week'?wkey(k):mkey(k)}
const S2BL=new Map();function blabel(b){const key=SS.grain+b;if(S2BL.has(key))return S2BL.get(key);const v=blabel0(b);S2BL.set(key,v);return v}
function blabel0(b){if(SS.grain==='month'){const d=new Date(b+'-01T12:00:00Z');return d.toLocaleString('en',{month:'short',year:'2-digit',timeZone:'UTC'})}const d=new Date(b+'T12:00:00Z');return d.toLocaleString('en',{month:'short',day:'numeric',timeZone:'UTC'})}
function todayKey(){return s2fmt(new Date())}
function range(){const t=todayKey();let from,to=dadd(t,1);const r=SS.range;
 if(r==='custom'&&SS.from&&SS.to)return[SS.from,dadd(SS.to,1)];
 if(r==='today')from=t;else if(r==='7d')from=dadd(t,-6);else if(r==='30d')from=dadd(t,-29);else if(r==='90d')from=dadd(t,-89);else if(r==='mtd')from=t.slice(0,8)+'01';else if(r==='all')from='2026-01-01';else from=dadd(wkey(t),-49);return[from,to]}
function buckets(from,to){const out=[];let k=from;while(k<to){const b=bkey(k);if(!out.length||out[out.length-1]!==b)out.push(b);k=dadd(k,1)}return out}
function s2tasks(from,to){const D2=D.s2||{tasks:[]};return D2.tasks.filter(t=>(!SS.kind||t.k===SS.kind)&&(!SS.repo||t.r===SS.repo)&&(!SS.agent||t.act.some(a=>a[2]===SS.agent&&a[0]>=from&&a[0]<to)))}
// events for a basis: [[dayKey, task]]
function evs(ts,basis){const out=[],P=(iso,t,f)=>{const k=dkey(iso);if(k)out.push([k,t,f,iso])};for(const t of ts){
 if(basis==='created')P(t.cr,t.t);
 else if(basis==='submitted'){for(const s of t.sub)P(s[0],t.t,t.subfb)}
 else if(basis==='first_submitted'){if(t.sub[0])P(t.sub[0][0],t.t,t.subfb)}
 else if(basis==='accepted'){for(const d of t.dec)if(d[1]==='accept'||d[1]==='accept_fb')P(d[0],t.t,d[1]==='accept_fb')}
 else if(basis==='atr'){for(const d of t.dec)if(d[1]==='atr_accept')P(d[0],t.t)}
 else if(basis==='revision'){for(const d of t.dec)if(d[1]==='revision')P(d[0],t.t)}
 else if(basis==='worked_on'){for(const a of t.act)if(a[1]!=='submit'&&(!SS.agent||a[2]===SS.agent))out.push([a[0],t.t,false,a[7]])}}
 return out}
function distinctIn(ev,from,to){const s=new Set();for(const e of ev)if(e[0]>=from&&e[0]<to)s.add(e[1]);return s.size}
function byBucket(ev,bks,from,to){const m=new Map(bks.map(b=>[b,new Set()]));for(const e of ev){if(e[0]<from||e[0]>=to)continue;const b=bkey(e[0]);if(m.has(b))m.get(b).add(e[1])}return bks.map(b=>m.get(b).size)}
function delta(ev,grain){const t=todayKey(),el=nowTod(),full=SS.compare==='full';let cf,pf,pt;
 if(grain==='day'){cf=t;pf=dadd(t,-1);pt=pf}else{cf=wkey(t);pf=dadd(cf,-7);pt=dadd(t,-7)}   // prior window ends at the same local time of day
 const cur=new Set(),pri=new Set();for(const e of ev){if(e[0]>=cf&&e[0]<=t)cur.add(e[1]);
  if(full){if(e[0]>=pf&&e[0]<cf)pri.add(e[1])}else if(e[0]>=pf&&(e[0]<pt||(e[0]===pt&&tod(e[3])<=el)))pri.add(e[1])}
 const c=cur.size,p=pri.size;return{c,p,abs:c-p,txt:p===0?(c?`new (+${c})`:'0'):`${c-p>=0?'+':''}${c-p} (${Math.round(100*(c-p)/p)}%)`}}
function fmtN(x){if(x==null)return'—';if(x>=1e9)return(x/1e9).toFixed(2)+'B';if(x>=1e6)return(x/1e6).toFixed(1)+'M';if(x>=1e3)return(x/1e3).toFixed(1)+'k';return String(Math.round(x*10)/10)}
function pct(a){a=a.filter(x=>x!=null&&isFinite(x)).sort((x,y)=>x-y);const q=p=>a.length?a[Math.min(a.length-1,Math.floor(p*(a.length-1)+.5))]:null;return{p50:q(.5),p75:q(.75),p90:q(.9),n:a.length}}
function hrs(h){return h==null?'—':h>=48?(h/24).toFixed(1)+'d':Math.round(h)+'h'}
// ------------------------------------------------------------------ tooltip + figure shell
function tipOn(e,html){const t=document.getElementById('s2tip');t.innerHTML=html;t.style.display='block';const x=Math.min(e.clientX+14,innerWidth-330),y=Math.min(e.clientY+14,innerHeight-t.offsetHeight-8);t.style.left=x+'px';t.style.top=y+'px'}
function tipOff(){document.getElementById('s2tip').style.display='none'}
const S2TIPS={};let S2N=0;function tipId(html){const id='t'+(S2N++);S2TIPS[id]=html;return id}
function fig(id,span,title,sub,body,table,foot,ctl=''){const tb=SS.tables[id];return `<div class="s2f" style="grid-column:span ${span}" data-fig="${id}"><div class="ctl">${ctl}<button data-s2tbl="${id}" class="${tb?'on':''}">${tb?'Chart':'Table'}</button></div><h4>${title}</h4><div class="sub">${sub}</div>${tb?`<div class="scroll">${table}</div>`:body}<div class="foot">${foot}</div></div>`}
function tbl(head,rows){return `<table><tr>${head.map(h=>`<th>${s2esc(h)}</th>`).join('')}</tr>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</table>`}
function legend(items){return `<div class="s2leg">${items.map(([k,l,c])=>`<span data-s2leg="${k}" class="${SS.hidden[k]?'off':''}"><i style="background:${c}"></i>${s2esc(l)}</span>`).join('')}</div>`}
// ------------------------------------------------------------------ SVG primitives (one value axis each)
function niceMax(v){if(v<=4)return Math.max(1,Math.ceil(v));if(v<=8)return 8;const p=Math.pow(10,Math.floor(Math.log10(v))),n=v/p;return(n<=1?1:n<=2?2:n<=5?5:10)*p}
function yAxis(W,H,L,top,max,unit){let s='';const ticks=max<4?Math.max(1,max):4;for(let i=0;i<=ticks;i++){const v=max*i/ticks,y=H-20-(H-20-top)*i/ticks;s+=`<line class="${i?'ax':'base'}" x1="${L}" x2="${W}" y1="${y}" y2="${y}"/><text x="${L-6}" y="${y+3}" text-anchor="end">${fmtN(v)}</text>`}return s}
function bars(bks,series,mode,H=220,W=900){const L=38,top=8,vis=series.filter(s=>!SS.hidden[s.id]);if(!bks.length)return'<div class="s2note">No buckets in this range.</div>';
 const tot=bks.map((_,i)=>mode==='stacked'?vis.reduce((a,s)=>a+(s.values[i]||0),0):Math.max(0,...vis.map(s=>s.values[i]||0)));const max=niceMax(Math.max(1,...tot));
 const bw=(W-L)/bks.length,gap=2,n=mode==='stacked'?1:Math.max(1,vis.length),cw=Math.min(24,(bw*0.8-gap*(n-1))/n);let s=yAxis(W,H,L,top,max);
 const y=v=>H-20-(H-20-top)*v/max;
 bks.forEach((b,i)=>{const x0=L+i*bw+(bw-(cw*n+gap*(n-1)))/2;let acc=0;const tip=tipId(`<b>${s2esc(blabel(b))}</b><br>`+vis.map(s=>`<span class="s2sw" style="background:${s.color}"></span>${s2esc(s.label)}: <b>${s.values[i]||0}</b>${s.prior?` · prior ${s.prior[i]||0}`:''}`).join('<br>'));
  vis.forEach((se,j)=>{const v=se.values[i]||0;if(!v)return;const x=mode==='stacked'?x0:x0+j*(cw+gap);const y1=mode==='stacked'?y(acc+v):y(v),y0=mode==='stacked'?y(acc):y(0);acc+=v;const h=Math.max(0,y0-y1-(mode==='stacked'?gap:0));
   s+=`<path d="M${x},${y0}V${y1+Math.min(4,h)}q0,-4 4,-4h${Math.max(0,cw-8)}q4,0 4,4V${y0}Z" fill="${se.color}"/>`});
  s+=`<rect x="${L+i*bw}" y="${top}" width="${bw}" height="${H-20-top}" fill="transparent" data-tip2="${tip}"/>`;
  if(bks.length<=16||i%Math.ceil(bks.length/12)===0)s+=`<text x="${L+i*bw+bw/2}" y="${H-6}" text-anchor="middle">${s2esc(blabel(b))}</text>`});
 return `<svg viewBox="0 0 ${W} ${H}" role="img" style="max-width:${W}px">${s}</svg>`}
function lines(bks,series,H=200,W=900){const L=38,top=8,vis=series.filter(s=>!SS.hidden[s.id]);if(!bks.length)return'<div class="s2note">No data.</div>';const max=niceMax(Math.max(1,...vis.flatMap(s=>s.values).filter(v=>v!=null)));
 const x=i=>L+(bks.length===1?(W-L)/2:i*(W-L-10)/(bks.length-1)),y=v=>H-20-(H-20-top)*v/max;let s=yAxis(W,H,L,top,max);
 vis.forEach(se=>{let d='',pen=false;se.values.forEach((v,i)=>{if(v==null){pen=false;return}d+=(pen?'L':'M')+x(i)+','+y(v);pen=true});s+=`<path d="${d}" fill="none" stroke="${se.color}" stroke-width="2" stroke-linejoin="round"/>`;se.values.forEach((v,i)=>{if(v!=null&&(se.values[i-1]==null||se.values[i+1]==null||i===se.values.length-1))s+=`<circle cx="${x(i)}" cy="${y(v)}" r="4" fill="${se.color}" stroke="#1a1d25" stroke-width="2"/>`});let li=se.values.length-1;while(li>0&&se.values[li]==null)li--;if(se.values[li]!=null)s+=`<text x="${x(li)-4}" y="${y(se.values[li])-8}" text-anchor="end">${se.values[li]}</text>`});
 bks.forEach((b,i)=>{const w=(W-L)/bks.length;const tip=tipId(`<b>${s2esc(blabel(b))}</b><br>`+vis.map(se=>`<span class="s2sw" style="background:${se.color}"></span>${s2esc(se.label)}: <b>${se.values[i]==null?'—':se.values[i]}</b>`).join('<br>'));s+=`<rect x="${x(i)-w/2}" y="${top}" width="${w}" height="${H-20-top}" fill="transparent" data-tip2="${tip}"/>`;if(bks.length<=16||i%Math.ceil(bks.length/12)===0)s+=`<text x="${x(i)}" y="${H-6}" text-anchor="middle">${s2esc(blabel(b))}</text>`});
 return `<svg viewBox="0 0 ${W} ${H}" role="img" style="max-width:${W}px">${s}</svg>`}
function donut(segs,unit){const tot=segs.reduce((a,s)=>a+s.v,0);if(!tot)return'<div class="s2note">Nothing to split in this range.</div>';const R=80,r=50,cx=100,cy=100;let a0=-Math.PI/2,s='';
 segs.forEach(sg=>{const a1=a0+2*Math.PI*sg.v/tot,large=a1-a0>Math.PI?1:0,p=(rr,a)=>[cx+rr*Math.cos(a),cy+rr*Math.sin(a)];const g=segs.length>1?0.012:0;const[x1,y1]=p(R,a0+g),[x2,y2]=p(R,a1-g),[x3,y3]=p(r,a1-g),[x4,y4]=p(r,a0+g);
  const tip=tipId(`<b>${s2esc(sg.l)}</b><br>${sg.v} ${unit} · ${(100*sg.v/tot).toFixed(1)}%`+(sg.members?`<br><span class="dim">${s2esc(sg.members)}</span>`:''));
  s+=segs.length===1?`<circle cx="${cx}" cy="${cy}" r="${(R+r)/2}" fill="none" stroke="${sg.c}" stroke-width="${R-r}" data-tip2="${tip}"/>`:`<path d="M${x1},${y1}A${R},${R} 0 ${large} 1 ${x2},${y2}L${x3},${y3}A${r},${r} 0 ${large} 0 ${x4},${y4}Z" fill="${sg.c}" data-tip2="${tip}"/>`;a0=a1});
 s+=`<text x="${cx}" y="${cy-2}" text-anchor="middle" style="font-size:22px;fill:#e7e9ef;font-weight:600">${fmtN(tot)}</text><text x="${cx}" y="${cy+14}" text-anchor="middle">${unit}</text>`;
 return `<div style="display:flex;gap:14px;align-items:center"><svg viewBox="0 0 200 200" style="width:200px;flex:none">${s}</svg><div style="flex:1">${segs.map(sg=>`<div style="font-size:12px;margin:3px 0"><span class="s2sw" style="background:${sg.c}"></span>${s2esc(sg.l)} <b>${sg.v}</b> <span class="dim">${(100*sg.v/tot).toFixed(0)}%</span></div>`).join('')}</div></div>`}
function hbars(rows,unit,color='#3987e5',W=900){if(!rows.length)return'<div class="s2note">No rows.</div>';const max=niceMax(Math.max(1,...rows.map(r=>r.v)));const L=Math.min(190,Math.round(W*.34)),rh=22,H=rows.length*rh+18;let s='';
 for(let i=0;i<=4;i++){const x=L+(W-L-40)*i/4;s+=`<line class="${i?'ax':'base'}" x1="${x}" x2="${x}" y1="0" y2="${H-14}"/><text x="${x}" y="${H-2}" text-anchor="middle">${fmtN(max*i/4)}</text>`}
 rows.forEach((r,i)=>{const w=(W-L-40)*r.v/max,y=i*rh+3;const tip=tipId(`<b>${s2esc(r.l)}</b><br>${fmtN(r.v)} ${unit}${r.t?'<br>'+r.t:''}`);
  if(r.segs){let x=L;r.segs.forEach(sg=>{const ww=(W-L-40)*sg.v/max;if(ww>0)s+=`<rect x="${x}" y="${y}" width="${Math.max(0,ww-2)}" height="${rh-7}" rx="2" fill="${sg.c}"/>`;x+=ww})}
  else s+=`<path d="M${L},${y}h${Math.max(0,w-4)}q4,0 4,4v${rh-15}q0,4 -4,4h${-Math.max(0,w-4)}Z" fill="${r.c||color}"/>`;
  s+=`<text x="${L-6}" y="${y+12}" text-anchor="end">${s2esc(r.l.length>26?r.l.slice(0,25)+'…':r.l)}</text><text x="${L+w+6}" y="${y+12}">${fmtN(r.v)}</text><rect x="0" y="${y-2}" width="${W}" height="${rh}" fill="transparent" data-tip2="${tip}"/>`});
 return `<svg viewBox="0 0 ${W} ${H}" role="img" style="max-width:${W}px">${s}</svg>`}
function heat(rows,cols,colLabels,unit){const max=Math.max(1,...rows.flatMap(r=>r.vals));const cell=v=>v?SEQ[Math.min(4,1+Math.floor(3.999*v/max))]:SEQ[0];
 return `<table class="s2m"><tr><th></th>${colLabels.map(c=>`<th style="font-size:10px">${s2esc(c)}</th>`).join('')}</tr>${rows.map(r=>`<tr><td><span class="s2sw" style="background:${r.c}"></span>${s2esc(r.l)}</td>${r.vals.map((v,j)=>`<td style="background:${cell(v)};text-align:center;color:${v/max>.6?'#0f1116':'#e7e9ef'}" data-tip2="${tipId(`<b>${s2esc(r.l)}</b> · ${s2esc(colLabels[j])}<br>${v} ${unit}`)}">${v||''}</td>`).join('')}</tr>`).join('')}</table>`}
// ------------------------------------------------------------------ sections
const S2V=[['throughput','📈 Throughput'],['team','👥 Team & track'],['models','🤖 Agents & models'],['tasks','🗂 Tasks'],['blockers','🚧 Blockers']];
function s2bar(D2){const repos=[...new Set(D2.tasks.map(t=>t.r))].sort(),opt=(v,l,cur)=>`<option value="${s2esc(v)}"${v===cur?' selected':''}>${s2esc(l)}</option>`;
 const views=`<div class="s2views">${S2V.map(([v,l])=>`<button data-s2view="${v}" class="${SS.view===v?'on':''}">${l}</button>`).join('')}</div>`;
 const filters=`<div class="s2bar"><span class="s2lab">Tasks</span><select data-s2="kind">${opt('','ST + MT',SS.kind)}${opt('st','Single-turn',SS.kind)}${opt('mt','Multi-turn',SS.kind)}</select>
 <select data-s2="repo">${opt('','All repos',SS.repo)}${repos.map(r=>opt(r,r,SS.repo)).join('')}</select>
 <select data-s2="agent">${opt('','All agents',SS.agent)}${['claude','codex','muse','human','unknown'].map(a=>opt(a,a[0].toUpperCase()+a.slice(1),SS.agent)).join('')}</select>
 <span class="s2lab">Time</span><select data-s2="range">${[['today','Today'],['7d','Last 7 days'],['30d','Last 30 days'],['8w','Last 8 weeks'],['90d','Last 90 days'],['mtd','Month to date'],['all','All time'],['custom','Custom…']].map(([v,l])=>opt(v,l,SS.range)).join('')}</select>
 ${SS.range==='custom'?`<input type="date" data-s2="from" value="${SS.from}"> through <input type="date" data-s2="to" value="${SS.to}">`:''}
 ${['day','week','month'].map(g=>`<button data-s2g="${g}" class="${SS.grain===g?'on':''}">${g[0].toUpperCase()+g.slice(1)}</button>`).join('')}
 <select data-s2="compare">${opt('same','compare at same point',SS.compare)}${opt('full','compare full periods',SS.compare)}</select>
 <button data-s2reset="1">Reset</button><span class="tz">${s2esc(S2TZ)}</span></div>`;
 const bases=[['accepted','✓ Accepted'],['submitted','◆ Submitted'],['worked_on','✎ Worked on'],['created','○ Created'],['revision','↩ Revisions requested']];
 const basis=['throughput','models'].includes(SS.view)?`<div class="s2bar s2basis"><span class="s2lab">Show</span>${bases.map(([v,l])=>`<button data-s2basis="${v}" class="${SS.basis===v?'on':''}">${l}</button>`).join('')}</div>`:'';
 return `<div class="s2top">${views}${filters}${basis}</div>`}
function s2quality(D2){const q=(D2.quality||[]).filter(x=>x.id!=='snapshot');return `<div class="s2qline">Data completeness: ${q.map(x=>{const p=x.eligible?Math.round(100*x.covered/x.eligible):0;const col=x.status==='exact'?'var(--green)':x.status==='unavailable'?'var(--dim)':'#fab219';
 return `<span title="${s2esc(x.reason||'complete')}" style="color:${col}">${s2esc(x.label.toLowerCase())} ${x.status==='unavailable'?'not connected':p+'%'}</span>`}).join(' · ')} <span class="dim">(hover for details)</span></div>`}
function s2kpis(ts,from,to){const K=[['accepted','Accepted'],['submitted','Submitted'],['worked_on','Worked on'],['created','Created'],['revision','Revisions requested']];
 const tiles=K.map(([b,l])=>{const ev=evs(ts,b),v=distinctIn(ev,from,to),dd=delta(ev,'day'),ww=delta(ev,'week'),c=S2L[b]||['#3987e5','•',l];
  return `<div class="kp ${SS.basis===b?'on':''}" data-s2basis="${b}" title="distinct tasks in the selected range"><div class="l">${c[1]} ${l}</div><div class="v">${v}</div><div class="d">DoD ${dd.txt}</div><div class="d">WoW ${ww.txt}</div></div>`});
 const fp=firstPass(ts,from,to);tiles.push(`<div class="kp" title="first decision was an accept, among tasks whose first decision fell in range"><div class="l">✓ First-pass accept</div><div class="v">${fp.d?Math.round(100*fp.a/fp.d)+'%':'—'}</div><div class="d">${fp.a}/${fp.d} first decisions (complete histories)</div><div class="d">${fp.d?'':'no decisions in range'}</div></div>`);
 return `<div class="s2k">${tiles.join('')}</div>`}
function firstPass(ts,from,to){let a=0,d=0;for(const t of ts){if(!t.rc)continue;const f=t.dec.find(x=>['accept','atr_accept','revision','reject'].includes(x[1]));if(!f)continue;const k=dkey(f[0]);if(!k||k<from||k>=to)continue;d++;if(f[1]==='accept'||f[1]==='atr_accept')a++}return{a,d}}
function s2throughput(D2,ts,from,to){const bks=buckets(from,to),q=D2.quality||[],sq=q.find(x=>x.id==='submissions')||{};
 let series,body;if(SS.barmode==='stacked'){const b=SS.basis,st=ts.filter(t=>t.k==='st'),mt=ts.filter(t=>t.k==='mt');series=[{id:'mt',label:'Multi-turn',color:'#256abf',values:byBucket(evs(mt,b),bks,from,to)},{id:'st',label:'Single-turn',color:'#86b6ef',values:byBucket(evs(st,b),bks,from,to)}]}
 else series=['accepted','submitted','worked_on'].map(b=>({id:b,label:S2L[b][2],color:S2L[b][0],values:byBucket(evs(ts,b),bks,from,to)}));
 body=legend(series.map(s=>[s.id,s.label,s.color]))+bars(bks,series,SS.barmode==='stacked'?'stacked':'grouped',240,940);
 const table=tbl(['Period',...series.map(s=>s.label)],bks.map((b,i)=>[s2esc(blabel(b)),...series.map(s=>s.values[i])]));
 const ctl=`<button data-s2bm="grouped" class="${SS.barmode==='grouped'?'on':''}">grouped</button><button data-s2bm="stacked" class="${SS.barmode==='stacked'?'on':''}">ST/MT</button>`;
 return fig('thr',8,`${SS.grain==='day'?'Day':SS.grain==='week'?'Week':'Month'}-over-${SS.grain} throughput`,`distinct tasks per ${SS.grain}${SS.barmode==='stacked'?' · '+(S2L[SS.basis]||[0,0,SS.basis])[2]+' split by ST/MT':''}`,body,table,
  `Date: accept decision / submission event / activity day · Coverage: submissions exact for ${sq.covered||0}/${sq.eligible||0} (rest = latest enteredPoolAt) · Exact counts`,ctl)}
function s2cumulative(ts,from,to,bks){const ends=bks.map(bk=>SS.grain==='month'?dadd(bk+'-01',32).slice(0,7)+'-01':SS.grain==='week'?dadd(bk,7):dadd(bk,1));const cum=SS.linemode==='cum';
 const all=['accepted','submitted','worked_on','created'].map(b=>{let values;if(cum){const first=new Map();for(const e of evs(ts,b==='submitted'?'first_submitted':b)){const f=first.get(e[1]);if(!f||e[0]<f)first.set(e[1],e[0])}const days=[...first.values()].sort();let j=0;values=ends.map(end=>{while(j<days.length&&days[j]<end)j++;return j})}
  else values=byBucket(evs(ts,b),bks,from,to);return{id:'l_'+b,label:(cum?'Σ ':'')+S2L[b][2],color:S2L[b][0],values}});
 const ctl=`<button data-s2lm="cum" class="${cum?'on':''}">Cumulative</button><button data-s2lm="period" class="${cum?'':'on'}">Per ${SS.grain}</button>`;
 return fig('cum',12,cum?'Cumulative output':`Output per ${SS.grain}`,cum?'all-time distinct tasks at each period end (submitted = first submission)':`distinct tasks in each ${SS.grain}, each period on its own`,legend(all.map(s=>[s.id,s.label,s.color]))+lines(bks,all,210,1420),tbl(['Period',...all.map(s=>s.label)],bks.map((b,i)=>[s2esc(blabel(b)),...all.map(s=>s.values[i])])),'Date: event time · accepts from review decisions · worked on = any commit or board activity that day',ctl)}
// colours follow the entity (frequency across all tasks), never its rank under the current filter
function s2order(dim,f){const all=(D.s2||{tasks:[]}).tasks,m=new Map();for(const t of all){const k=f(t);m.set(k,(m.get(k)||0)+1)}return[...m].sort((a,b)=>b[1]-a[1]||String(a[0]).localeCompare(String(b[0]))).map(x=>x[0])}
function s2split(D2,ts,from,to,force){const b=force?'worked_on':SS.basis,dim=force||SS.dim,taskDims={k:['ST/MT',t=>t.k==='mt'?'Multi-turn':t.k==='st'?'Single-turn':'Unknown'],r:['Repo',t=>t.r],c:['Category',t=>t.c],s:['Current status',t=>t.s]};
 let segs=[],unit='tasks',dis='';
 if(dim==='phase'||dim==='agent'||dim==='model'){if(b!=='worked_on')dis=`A donut would double-count tasks for ${(S2L[b]||[0,0,b])[2]} × ${dim}. Choose an additive basis (Worked on counts activity records) or a unique task dimension.`;
  else{unit='activity records';const m=new Map();for(const t of ts)for(const a of t.act){if(a[0]<from||a[0]>=to||a[1]==='submit')continue;const key=dim==='phase'?a[1]:dim==='agent'?a[2]:(a[3]||'unknown model');m.set(key,(m.get(key)||0)+a[4])}
   segs=[...m].map(([k,v])=>({l:dim==='phase'?PHN[k]||k:k,v,c:dim==='phase'?S2P[k]||'#8a8fa0':dim==='agent'?S2C[k]||S2C.other:'#3987e5'}))}}
 else{const f=taskDims[dim][1],ev=evs(ts,b),ids=new Set(ev.filter(e=>e[0]>=from&&e[0]<to).map(e=>e[1]));const m=new Map();for(const t of ts)if(ids.has(t.t)){const k=f(t);m.set(k,(m.get(k)||0)+1)}
  const pal=['#3987e5','#d95926','#199e70','#c98500','#d55181'],order=s2order(dim,f);segs=[...m].map(([k,v])=>({l:k,v,c:k==='Unknown'||k==='unknown'?'#8a8fa0':dim==='k'?(k==='Multi-turn'?'#3987e5':'#d95926'):pal[order.indexOf(k)]||'#5b6070'}));}
 segs.sort((a,b)=>b.v-a.v);if(segs.length>6){const rest=segs.slice(5);segs=segs.slice(0,5).concat([{l:'Other ('+rest.length+')',v:rest.reduce((a,s)=>a+s.v,0),c:'#5b6070',members:rest.map(s=>s.l+' '+s.v).join(', ')}])}
 const ctl=`<select data-s2="dim">${[['k','ST/MT'],['r','Repo'],['c','Category'],['s','Status'],['phase','Phase'],['agent','Agent kind'],['model','Model']].map(([v,l])=>`<option value="${v}"${v===dim?' selected':''}>${l}</option>`).join('')}</select>`;
 const body=dis?`<div class="s2note s2warn">${s2esc(dis)}</div>`:donut(segs,unit);
 return fig(force?'split2':'split',force?12:4,force?'Work split by agent':'What it is made of',`${(S2L[b]||[0,0,b])[2]} in range, split by ${dim}`,body,tbl(['Segment','Value','Share'],segs.map(s=>[s2esc(s.l),s.v,(100*s.v/Math.max(1,segs.reduce((a,x)=>a+x.v,0))).toFixed(1)+'%'])),`Date: ${b==='worked_on'?'activity day':'event time'} · ${dim==='phase'||dim==='agent'||dim==='model'?'Estimated classification (see Phases coverage)':'Exact'}`,ctl)}
function s2pipeline(D2,ts){const built=ts.length,imp=ts.filter(t=>t.s!=='not_imported').length,sub=ts.filter(t=>t.sub.length).length,acc=ts.filter(t=>t.dec.some(d=>d[1]==='accept'||d[1]==='atr_accept')||t.s==='accepted'||t.s==='used_in_training').length;
 const st=[['Built',built],['Imported',imp],['Ever submitted',sub],['Ever accepted',acc]],ramp=['#184f95','#256abf','#3987e5','#86b6ef'];
 const funnel=hbars(st.map(([l,v],i)=>({l:`${l}${i?' · '+(100*v/Math.max(1,st[i-1][1])).toFixed(0)+'%':''}`,v,c:ramp[i]})),'tasks','#3987e5',460);
 const now=Date.now(),open=[['draft','Draft'],['needs_reviewers_assigned','Waiting for reviewer'],['being_reviewed','In review'],['needs_revision','Needs revision']];
 const bands=[['0–2d',2],['3–6d',6],['7–13d',13],['14d+',1e9]],bc=['#184f95','#256abf','#3987e5','#86b6ef'];
 const wrows=open.map(([s,l])=>{const tt=ts.filter(t=>t.s===s);const c=[0,0,0,0];let px=0;for(const t of tt){const age=t.se?(now-new Date(t.se))/864e5:null;if(!t.sex)px++;const i=age==null?3:bands.findIndex(b=>age<=b[1]);c[i]++}
  return{l:`${l} (${tt.length})`,v:tt.length,segs:c.map((v,i)=>({v,c:bc[i]})),t:bands.map((b,i)=>`${b[0]}: ${c[i]}`).join(' · ')+`<br>${tt.length-px} exact state start · ${px} proxy`}});
 const flow=s2flow(ts);
 return `<div class="s2g">${fig('fun',4,'Funnel','snapshot now · conversion from previous stage',funnel,tbl(['Stage','Tasks'],st),'Date: now · Exact snapshot (not a nested cohort)')}
 ${fig('wip',4,'Work in progress by age','open tasks by state, age since entering it',legend(bands.map((b,i)=>['ab'+i,b[0],bc[i]]))+hbars(wrows,'tasks','#3987e5',460),tbl(['State','0–2d','3–6d','7–13d','14d+'],wrows.map(r=>[s2esc(r.l),...r.segs.map(x=>x.v)])),'Date: now · age since entering the state: reviewer claim, last submission or revision request when known; otherwise last observed status change (proxy, counted in tooltip)')}
 ${flow}</div>`}
function s2flow(ts){const sd=[],rr=[],cs=[];let proxy=0;for(const t of ts){if(t.subfb){proxy++;continue}
 const ev=[...t.sub.map(s=>[s[0],'S']),...t.dec.filter(d=>['revision','accept','atr_accept','reject'].includes(d[1])).map(d=>[d[0],d[1]==='revision'?'R':'D'])].sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0);
 if(t.sub[0]&&t.cr){const h=(new Date(t.sub[0][0])-new Date(t.cr))/36e5;if(h>=0)cs.push(h)}
 let openS=null,openR=null;for(const[at,k]of ev){if(k==='S'){if(openR){const h=(new Date(at)-new Date(openR))/36e5;if(h>=0)rr.push(h);openR=null}openS=at}
  else{if(openS){const h=(new Date(at)-new Date(openS))/36e5;if(h>=0)sd.push(h);openS=null}openR=k==='R'?at:null}}}
const rows=[['Created → first submit',pct(cs)],['Submit → decision',pct(sd)],['Revision → resubmit',pct(rr)]];const max=niceMax(Math.max(1,...rows.map(r=>r[1].p90||0)));const W=460,L=150,H=rows.length*34+20,x=v=>L+(W-L-40)*v/max;let s='';
 for(let i=0;i<=4;i++){const xx=L+(W-L-40)*i/4;s+=`<line class="${i?'ax':'base'}" x1="${xx}" x2="${xx}" y1="0" y2="${H-14}"/><text x="${xx}" y="${H-2}" text-anchor="middle">${hrs(max*i/4)}</text>`}
 rows.forEach(([l,p],i)=>{const y=i*34+14;if(!p.n){s+=`<text x="${L-6}" y="${y+4}" text-anchor="end">${l}</text><text x="${L+4}" y="${y+4}">no complete intervals</text>`;return}
  s+=`<text x="${L-6}" y="${y+4}" text-anchor="end">${l}</text><line x1="${L}" x2="${x(p.p90)}" y1="${y}" y2="${y}" stroke="#256abf" stroke-width="2"/>${[['p50',p.p50,'#86b6ef'],['p75',p.p75,'#3987e5'],['p90',p.p90,'#256abf']].map(([k,v,c])=>`<circle cx="${x(v)}" cy="${y}" r="5" fill="${c}" stroke="#1a1d25" stroke-width="2"/>`).join('')}<text x="${x(p.p50)}" y="${y-8}" text-anchor="middle">p50 ${hrs(p.p50)}</text><text x="${x(p.p90)+8}" y="${y+4}">p90 ${hrs(p.p90)} · n ${p.n}</text><rect x="0" y="${y-12}" width="${W}" height="26" fill="transparent" data-tip2="${tipId(`<b>${l}</b><br>p50 ${hrs(p.p50)} · p75 ${hrs(p.p75)} · p90 ${hrs(p.p90)}<br>${p.n} complete intervals`)}"/>`});
 return fig('flow',4,'How long things take',`p50 / p75 / p90 of completed intervals (all history; each boundary used once) · ${proxy} tasks without exact submission events excluded`,`<svg viewBox="0 0 ${W} ${H}" style="max-width:${W}px">${s}</svg>`,tbl(['Interval','p50','p75','p90','n'],rows.map(([l,p])=>[l,hrs(p.p50),hrs(p.p75),hrs(p.p90),p.n])),'Date: interval end · Exact boundaries where submission events are hydrated')}
function s2matrix(ts){const t0=todayKey(),weeks=[];let w=wkey(t0);for(let i=0;i<SS.mweeks;i++){weeks.unshift(w);w=dadd(w,-7)}const W0=weeks[0];
 const code=(t,wk)=>{const end=dadd(wk,7),out=[],inw=iso=>{const k=dkey(iso);return k&&k>=wk&&k<end};if(inw(t.cr))out.push(['C','Created','#8a8fa0']);t.sub.forEach((s,i)=>{if(inw(s[0]))out.push(i===0?['S','First submitted','#7ab8ff']:['RS','Resubmitted (v'+(s[1]||i+1)+')','#7ab8ff'])});
  t.dec.forEach(d=>{if(inw(d[0]))out.push(d[1]==='revision'?['RR','Revision requested','#ec835a']:d[1]==='accept'?['A','Accepted','#0ca30c']:d[1]==='accept_fb'?['A?','Accepted (time from current status, no review record)','#0ca30c']:d[1]==='atr_accept'?['AT','Auto-accepted','#5fd7d7']:['D',d[1],'#8a8fa0'])});(t.vt||[]).forEach(v=>{if(inw(v[0]))out.push(v[1]==='VF'?['V✗','Validation failed (observed by)','#d03b3b']:['V✓','Validation cleared (observed by)','#0ca30c'])});if(inw(t.ar))out.push(['X','Archived','#5b6070']);return out};
 const widx=new Map();weeks.forEach((wk,i)=>{for(let d=0;d<7;d++)widx.set(dadd(wk,d),i)});
 const rows=ts.map(t=>{const counts=weeks.map(()=>0),agents=weeks.map(()=>new Set());for(const a of t.act){const i=widx.get(a[0]);if(i!==undefined){counts[i]+=a[4];if(a[1]!=='submit'&&a[2]!=='unknown')agents[i].add(a[2])}}const ev=[t.cr,t.ar,...t.sub.map(x=>x[0]),...t.dec.map(x=>x[0]),...(t.vt||[]).map(x=>x[0])].filter(Boolean);
  const hit=new Set(ev.map(iso=>widx.get(dkey(iso))).filter(i=>i!==undefined));const cells=weeks.map((wk,i)=>hit.has(i)?code(t,wk):[]);return{t,counts,cells,agents,any:counts.some(Boolean)||hit.size>0}}).filter(r=>r.any)
  .sort((a,b)=>{const la=a.counts.findLastIndex?a.counts.findLastIndex(Boolean):0,lb=b.counts.findLastIndex?b.counts.findLastIndex(Boolean):0;return lb-la||a.t.t.localeCompare(b.t.t)});
 const spark=c=>{const m=Math.max(1,...c);return `<svg viewBox="0 0 ${c.length*6} 16" style="width:${c.length*6}px;height:16px">${c.map((v,i)=>`<rect x="${i*6}" y="${16-14*v/m}" width="4" height="${14*v/m}" fill="#3987e5"/>`).join('')}</svg>`};
 const body=`<div class="scroll"><table class="s2m"><tr><th>Task</th><th>activity</th>${weeks.map(w=>`<th>${s2esc(blabel(w))}</th>`).join('')}<th>now</th></tr>${rows.map(r=>`<tr data-s2task="${s2esc(r.t.t)}"><td>${s2esc(r.t.t)} <span class="dim">${r.t.k.toUpperCase()}</span></td><td>${spark(r.counts)}</td>${r.cells.map((c,i)=>`<td class="c" title="${s2esc(r.t.t)} · week of ${s2esc(blabel(weeks[i]))}: ${s2esc(c.map(x=>x[1]).join(' → ')||'no transitions')} · ${r.counts[i]} activity records">${c.slice(0,2).map(x=>`<span class="chip" style="color:${x[2]}">${x[0]}</span>`).join('')}${c.length>2?'+'+(c.length-2):''}${!c.length&&r.counts[i]?'<span class="dim">✎'+r.counts[i]+'</span>':''}${[...r.agents[i]].map(a=>`<span class="s2dot" style="background:${S2C[a]||S2C.other}" title="${s2esc(a)} worked on it"></span>`).join('')}</td>`).join('')}<td>${s2esc(r.t.s.replace(/_/g,' '))}</td></tr>`).join('')}</table></div>`;
 const ctl=`<select data-s2="mweeks">${[8,12,20].map(n=>`<option value="${n}"${n===SS.mweeks?' selected':''}>${n} weeks</option>`).join('')}</select><button data-s2roster="1" class="${SS.showRoster?'on':''}">who worked on what ▾</button>`;
 return fig('mx',12,'Task-by-task, week by week',`named transitions per week (C created · S submitted · RS resubmitted · RR revision requested · A accepted · V✗/V✓ validation failed/cleared · X archived · ✎n activity only · dots = <span class="s2dot" style="background:#9085e9"></span>Claude <span class="s2dot" style="background:#199e70"></span>Codex <span class="s2dot" style="background:#d95926"></span>Muse <span class="s2dot" style="background:#3987e5"></span>you) · ${rows.length} tasks · click a row for its card`,body,body,'Date: transition / activity day · Exact transitions; activity counts from commits + board events (board events start '+(D.s2.ledger_start||'').slice(0,10)+')',ctl)}
function s2roster(ts){const t0=todayKey(),cw=wkey(t0),wk=SS.rweek||cw,end=dadd(wk,7);const weeks=[];let w=cw;for(let i=0;i<12;i++){weeks.push(w);w=dadd(w,-7)}
 const outc=t=>({all:true,submitted:t.sub.some(s=>{const k=dkey(s[0]);return k>=wk&&k<end}),accepted:t.s==='accepted'||t.s==='used_in_training'||t.dec.some(d=>d[1]==='accept'),in_review:['being_reviewed','needs_reviewers_assigned'].includes(t.s),needs_revision:t.s==='needs_revision'})[SS.rout];
 const rows=[];for(const t of ts){if(!outc(t))continue;for(const a of t.act)if(a[0]>=wk&&a[0]<end&&(!SS.agent||a[2]===SS.agent))rows.push({t,a})}
 const order=Object.keys(S2P);rows.sort((x,y)=>order.indexOf(x.a[1])-order.indexOf(y.a[1])||x.t.t.localeCompare(y.t.t));
 const agg=new Map();for(const r of rows){const k=r.t.t+'|'+r.a[1]+'|'+r.a[2]+'|'+(r.a[3]||'');const g=agg.get(k)||{t:r.t,ph:r.a[1],ag:r.a[2],m:r.a[3],n:0,conf:r.a[5],days:new Set(),src:new Set()};g.n+=r.a[4];g.days.add(r.a[0]);(r.a[6]||[]).forEach(x=>g.src.add(x));if(r.a[5]==='high')g.conf='high';agg.set(k,g)}
 const list=[...agg.values()],uncl=list.filter(g=>g.ph==='unclassified').length;
 const ctl=`<select data-s2="rweek">${weeks.map(x=>`<option value="${x}"${x===wk?' selected':''}>week of ${blabel(x)}</option>`).join('')}</select><select data-s2="rout">${[['all','all work'],['submitted','submitted that week'],['accepted','accepted'],['in_review','in review'],['needs_revision','needs revision']].map(([v,l])=>`<option value="${v}"${v===SS.rout?' selected':''}>${l}</option>`).join('')}</select>`;
 const head=['Task','Phase','Agent','Model','Records','Days','Evidence','Confidence'],trs=list.map(g=>[`<span data-s2task="${s2esc(g.t.t)}" style="cursor:pointer">${s2esc(g.t.t)}</span>`,`<span class="s2sw" style="background:${S2P[g.ph]}"></span>${s2esc(PHN[g.ph]||g.ph)}`,`<span class="s2sw" style="background:${S2C[g.ag]||S2C.other}"></span>${s2esc(g.ag)}`,s2esc(g.m||'—'),g.n,g.days.size,s2esc([...g.src].join(', ')),s2esc(g.conf)]);
 const body=list.length?`<div class="scroll">${tbl(head,trs)}</div>`:'<div class="s2note">No evidenced agent work matches this week and outcome.</div>';
 return fig('ros',8,'Who worked on what',`week of ${blabel(wk)} · one row per task × phase × agent · ${list.length} rows, ${uncl} unclassified`,body,body,`Date: evidence day · Estimated phases; agent from the board event nearest each commit (±45 min); exact model only from native Codex/Muse runs`,ctl)}
function s2self(ts){const t=todayKey(),cw=wkey(t),wk=[];let w=cw;for(let i=0;i<9;i++){wk.unshift(w);w=dadd(w,-7)}const ev=evs(ts,'accepted'),per=wk.map(x=>new Set(ev.filter(e=>e[0]>=x&&e[0]<dadd(x,7)).map(e=>e[1])).size);
 const prev=per.slice(-5,-1).sort((a,b)=>a-b),med=prev.length?(prev[1]+prev[2])/2:0,series=[{id:'me',label:'You · accepted per week',color:'#0ca30c',values:per},{id:'med',label:'Your 4-week median',color:'#8a8fa0',values:per.map(()=>med)}];
 return fig('self',8,'You vs your own recent pace','accepted per week, last 9 weeks, against your 4-week median (the current week is partial)',legend(series.map(s=>[s.id,s.label,s.color]))+lines(wk,series,220,940),tbl(['Week','Accepted'],wk.map((x,i)=>[blabel(x),per[i]])),'Date: accept decision · Exact')}
function s2peers(D2){const rows=D2.peers||[];const body=rows.length?tbl(['Scope','Window','Metric','You','Rank','Of','Percentile'],rows.map(r=>[s2esc(r.scope),s2esc(r.window),s2esc(r.metric),r.value,r.rank,r.of,r.of>1?Math.round(100*(r.of-r.rank)/(r.of-1))+'th':'—'])):
 `<div class="s2note">Team / track comparison is not connected.<br><br>Run <code>board rank import /path/to/rank.csv</code><br>or set <code>[rank] daiquery_id</code> to your saved DaiQuery.<br><br><span class="dim">Nothing is inferred from your own data or server load.</span></div>`;
 return fig('peer',4,'You vs team / track','sanctioned rank source only',body,body,'Source: rank.py cache · Exact when connected')}
function s2rework(ts,from,to){const binsA=[0,0,0,0],binsO=[0,0,0,0];let skipped=0;for(const t of ts){if(!t.sub.length&&!t.dec.length)continue;const fk=dkey(t.sub[0]?t.sub[0][0]:t.dec[0][0]);if(fk&&(fk<from||fk>=to)&&SS.range!=='all')continue;if(!t.rc){skipped++;continue}
  let r=0,acc=false;for(const d of t.dec){if(d[1]==='revision')r++;if(d[1]==='accept'||d[1]==='atr_accept'){acc=true;break}}const b=Math.min(3,r);(acc?binsA:binsO)[b]++}
 const labels=['0','1','2','3+'],H=200,W=700,L=38,max=niceMax(Math.max(1,...binsA.map((v,i)=>v+binsO[i])));let s=yAxis(W,H,L,8,max);const bw=(W-L)/4,y=v=>H-20-(H-28)*v/max;
 labels.forEach((lb,i)=>{const x=L+i*bw+bw/2-12,a=binsA[i],o=binsO[i];if(a)s+=`<rect x="${x}" y="${y(a)}" width="24" height="${H-20-y(a)}" fill="#3987e5"/>`;if(o)s+=`<rect x="${x}" y="${y(a+o)}" width="24" height="${Math.max(0,y(a)-y(a+o)-2)}" fill="#86b6ef" opacity=".55"/>`;
  s+=`<text x="${x+12}" y="${y(a+o)-4}" text-anchor="middle">${a+o}</text><text x="${x+12}" y="${H-6}" text-anchor="middle">${lb} rounds</text><rect x="${L+i*bw}" y="0" width="${bw}" height="${H}" fill="transparent" data-tip2="${tipId(`<b>${lb} revision rounds</b><br>${a} accepted · ${o} still open (lower bound: may need more rounds)`)}"/>`});
 const labelsT=labels;const coh=new Map(),mature=dadd(todayKey(),-14);for(const t of ts){if(!t.rc||!t.sub[0]||t.subfb)continue;const k0=dkey(t.sub[0][0]);if(!k0||(SS.range!=='all'&&(k0<from||k0>=to)))continue;const k=bkey(k0);const f=t.dec.find(x=>['accept','atr_accept','revision','reject'].includes(x[1]));const c=coh.get(k)||[0,0,0];if(f){c[1]++;if(f[1]==='accept'||f[1]==='atr_accept')c[0]++}else if(k0<mature)c[1]++;else c[2]++;coh.set(k,c)}
 const ck=buckets(SS.range==='all'?([...coh.keys()].sort()[0]||from):from,to).filter(b=>SS.grain!=='day'||true),fpS=[{id:'fp',label:'First-pass %',color:'#3987e5',values:ck.map(k=>{const c=coh.get(k);return c&&c[1]?Math.round(100*c[0]/c[1]):null})}];
 return `<div class="s2g">${fig('rw',6,'How many revision rounds?','tasks first submitted in range, by revision rounds before acceptance · dark = accepted, light = still open',`<div class="s2leg"><span><i style="background:#3987e5"></i>accepted</span><span><i style="background:#86b6ef;opacity:.55"></i>still open (lower bound)</span></div><svg viewBox="0 0 ${W} ${H}" style="max-width:${W}px">${s}</svg>`,tbl(['Rounds','Accepted','Still open'],labelsT.map((l,i)=>[l,binsA[i],binsO[i]])),`Date: first submission · Exact: only tasks with complete, current review history (${skipped} excluded, never counted as zero) · auto-accepts counted as accepts`)}
 ${fig('fp',6,'Is first-pass acceptance improving?',`share of first decisions that were accepts, by ${SS.grain} of first submission · undecided after 14 days counts as not first-pass`,lines(ck,fpS,200,700),tbl(['Cohort','First-pass accepts','Decided','Waiting (<14d)','Rate'],ck.filter(k=>coh.get(k)).map(k=>{const c=coh.get(k);return[blabel(k),c[0],c[1],c[2],c[1]?Math.round(100*c[0]/c[1])+'%':'—']})),'Date: first submission · Exact for complete histories; gaps = no mature cohort that '+SS.grain)}</div>`}
const BLK=[['calibration',/too (easy|hard)|pass ?rate|calibrat|band|saturat|0\/5|5\/5|difficult/i,'#199e70'],['grader / tests',/test|assert|grader|unfair|leak|cheat|hack|oracle|flak/i,'#d95926'],['instruction / spec',/instruction|spec|ambig|unstated|requirement|determin|unclear|wording|step \d/i,'#3987e5'],['environment / infra',/docker|build|timeout|environment|depend|network|install/i,'#c98500'],['provenance / originality',/provenance|contamin|novel|original|copied|3p|ai[- ]generated/i,'#d55181'],['README / docs',/readme|doc|completion rate|model analysis/i,'#9085e9']];
function s2blockers(ts,from,to){const cls=r=>{for(const[k,re]of BLK)if(re.test(r||''))return k;return'unknown'};const cnt=new Map(),wk=new Map(),tasks=new Map();
 for(const t of ts)for(const d of t.dec){if(d[1]!=='revision')continue;const k=dkey(d[0]);if(!k||k<from||k>=to)continue;const c=cls(d[2]);cnt.set(c,(cnt.get(c)||0)+1);(tasks.get(c)||tasks.set(c,[]).get(c)).push(t.t);const w=wkey(k);const m=wk.get(w)||{};m[c]=(m[c]||0)+1;wk.set(w,m)}
 const col=k=>(BLK.find(b=>b[0]===k)||[0,0,'#8a8fa0'])[2],rows=[...cnt].sort((a,b)=>b[1]-a[1]),tot=rows.reduce((a,r)=>a+r[1],0);let cum=0;
 const pareto=hbars(rows.map(([k,v])=>{cum+=v;return{l:k,v,c:'#3987e5',t:`${(100*v/tot).toFixed(0)}% · cumulative ${(100*cum/tot).toFixed(0)}%<br>${[...new Set(tasks.get(k))].slice(0,6).join(', ')}`}}),'revision requests','#3987e5',700);
 const wks=[...wk.keys()].sort(),keys=rows.map(r=>r[0]),trend=bars(wks,keys.map(k=>({id:'b_'+k,label:k,color:col(k),values:wks.map(w=>(wk.get(w)||{})[k]||0)})),'stacked',200,700);
 return `<div class="s2g">${fig('blk',6,'What blocks acceptance?','human revision requests in range, classified from the reviewer’s reason',rows.length?pareto:'<div class="s2note">No revision requests in this range.</div>',tbl(['Class','Requests','Share'],rows.map(([k,v])=>[k,v,(100*v/Math.max(1,tot)).toFixed(0)+'%'])),'Date: decision time · Estimated: keyword rules over the decision reason (first 120 chars); unmatched stay “unknown”')}
 ${fig('blkt',6,'Blockers week by week','revision requests per week by class',legend(keys.map(k=>['b_'+k,k,col(k)]))+(wks.length?trend:'<div class="s2note">No data.</div>'),tbl(['Week',...keys],wks.map(w=>[blabel(w),...keys.map(k=>(wk.get(w)||{})[k]||0)])),'Date: decision time · Estimated classes')}</div>`}
function s2agents(D2,ts,from,to){const ph=(D2.phases||[]).filter(p=>p!=='submit'),m=new Map();for(const t of ts)for(const a of t.act){if(a[0]<from||a[0]>=to||a[1]==='submit')continue;const key=a[2]+(a[3]?' · '+a[3]:'');const r=m.get(key)||{l:key,c:S2C[a[2]]||S2C.other,vals:ph.map(()=>0)};r.vals[ph.indexOf(a[1])]+=a[4];m.set(key,r)}
 const rows=[...m.values()].sort((a,b)=>b.vals.reduce((x,y)=>x+y,0)-a.vals.reduce((x,y)=>x+y,0));
 const tk=D2.tokens||{},acc=tk.accounting||{},gate=(acc.coverage_pct||0)>=30,daily=(tk.daily||[]).slice(-14),kinds=['claude','codex','muse'];
 const dser=kinds.map(k=>({id:'tk_'+k,label:k,color:S2C[k],values:daily.map(d=>((d.kinds||{})[k]||{}).total||0)}));
 const models=(tk.models||[]).slice(0,10).map(([k,mm,v])=>({l:`${k} · ${mm}`,v,c:S2C[k]||S2C.other}));
 return `<div class="s2g">${fig('ag',7,'Which agent did which part?','activity records by agent (and exact model when known) × phase, in range',rows.length?heat(rows,ph,ph.map(p=>PHN[p]||p),'records'):'<div class="s2note">No attributed activity in this range.</div>',tbl(['Agent',...ph.map(p=>PHN[p]||p)],rows.map(r=>[s2esc(r.l),...r.vals])),'Date: evidence day · Estimated · contribution, not exclusive credit · “unknown” = no board evidence near the commit (board events start '+(D2.ledger_start||'').slice(0,10)+')')}
 ${fig('tok',5,'Tokens: what they produce','raw token use per day by agent (exact counters)'+(gate?' · per-task efficiency coming next':''),(gate?'':`<div class="s2warn" style="font-size:12px;margin-bottom:4px">Insufficient attribution: ${acc.coverage_pct||0}% of ${fmtN(acc.total)} reported tokens are linked to tasks (minimum 30%). Per-task efficiency is hidden; raw totals below are exact.</div>`)+legend(dser.map(s=>[s.id,s.label,s.color]))+bars(daily.map(d=>d.day),dser,'stacked',170,560)+hbars(models,'tokens','#3987e5',560),tbl(['Agent · model','Tokens'],models.map(m=>[s2esc(m.l),fmtN(m.v)])),'Date: token day · Exact counters as reported by each agent (cache/reasoning semantics differ by kind) · model totals = sessions visible now')}</div>`}
function renderStats2(){const D2=D.s2;const el=document.getElementById('stats');if(!D2||!D2.tasks){el.innerHTML='<div class="empty">stats are being built…</div>';return}
 S2TZ=D2.timezone||S2TZ;S2DF=new Intl.DateTimeFormat('en-CA',{timeZone:S2TZ,year:'numeric',month:'2-digit',day:'2-digit'});S2TF=new Intl.DateTimeFormat('en-GB',{timeZone:S2TZ,hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});for(const k in S2TIPS)delete S2TIPS[k];S2N=0;
 const t0=performance.now(),[from,to]=range(),ts=s2tasks(from,to),v=SS.view;let body='';
 if(v==='throughput')body=`${s2kpis(ts,from,to)}<div class="s2g">${s2throughput(D2,ts,from,to)}${s2split(D2,ts,from,to)}${s2cumulative(ts,from,to,buckets(from,to))}</div>${s2pipeline(D2,ts)}`;
 else if(v==='team')body=`<div class="s2g">${s2peers(D2)}${s2self(ts)}</div>`;
 else if(v==='models')body=`${s2agents(D2,ts,from,to)}<div class="s2g">${s2split(D2,ts,from,to,'agent')}</div>`;
 else if(v==='tasks')body=`<div class="s2g">${s2matrix(ts)}</div>${SS.showRoster?`<div class="s2g">${s2roster(ts)}</div>`:''}`;
 else body=`${s2rework(ts,from,to)}${s2blockers(ts,from,to)}`;
 el.innerHTML=`${s2bar(D2)}${s2quality(D2)}<div class="s2h"><small>${s2esc(blabel(from))} → ${s2esc(blabel(dadd(to,-1)))} · ${ts.length} tasks in filter</small></div>${body}
 <div class="dim" style="font-size:10.5px;margin:10px 0">rendered in ${Math.round(performance.now()-t0)} ms · generated ${s2esc(new Date(D2.generated_at).toLocaleString())}</div>`;
 if(!document.getElementById('s2tip')){const d=document.createElement('div');d.id='s2tip';document.body.appendChild(d)}}
function s2hash(){const p=new URLSearchParams();for(const k of['view','range','grain','compare','basis','kind','repo','agent','from','to','dim'])if(SS[k]&&SS[k]!==({view:'throughput',range:'8w',grain:'week',compare:'same',basis:'accepted',dim:'k'})[k])p.set(k,SS[k]);history.replaceState(null,'','#stats'+(p.toString()?'?'+p:''))}
function s2load(){const m=location.hash.match(/^#stats\?(.*)$/);if(m)for(const[k,v]of new URLSearchParams(m[1]))if(k in SS)SS[k]=v}
function s2wire(){const el=document.getElementById('stats');if(el.dataset.s2)return;el.dataset.s2='1';s2load();
 el.addEventListener('change',e=>{const k=e.target.dataset.s2;if(!k)return;SS[k]=k==='mweeks'?+e.target.value:e.target.value;s2hash();renderStats2()});
 el.addEventListener('click',e=>{const t=e.target.closest('[data-s2g],[data-s2basis],[data-s2tbl],[data-s2bm],[data-s2leg],[data-s2reset],[data-s2task],[data-s2view],[data-s2lm],[data-s2roster]');if(!t)return;
  if(t.dataset.s2view){SS.view=t.dataset.s2view;s2hash();renderStats2();return}if(t.dataset.s2lm){SS.linemode=t.dataset.s2lm;renderStats2();return}if(t.dataset.s2roster){SS.showRoster=!SS.showRoster;renderStats2();return}
  if(t.dataset.s2g)SS.grain=t.dataset.s2g;else if(t.dataset.s2basis)SS.basis=t.dataset.s2basis;else if(t.dataset.s2tbl)SS.tables[t.dataset.s2tbl]=!SS.tables[t.dataset.s2tbl];else if(t.dataset.s2bm)SS.barmode=t.dataset.s2bm;
  else if(t.dataset.s2leg)SS.hidden[t.dataset.s2leg]=!SS.hidden[t.dataset.s2leg];else if(t.dataset.s2reset)Object.assign(SS,{range:'8w',grain:'week',compare:'same',basis:'accepted',kind:'',repo:'',agent:'',from:'',to:'',dim:'k',barmode:'grouped',hidden:{}});
  else if(t.dataset.s2task){if(typeof openDrawer==='function')openDrawer(t.dataset.s2task);return}s2hash();renderStats2()});
 el.addEventListener('mousemove',e=>{const t=e.target.closest('[data-tip2]');if(t&&S2TIPS[t.dataset.tip2])tipOn(e,S2TIPS[t.dataset.tip2]);else tipOff()});el.addEventListener('mouseleave',tipOff)}
"""
