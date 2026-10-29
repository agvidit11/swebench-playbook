"""Runs the Stats page's metric functions under Node (skipped when node is unavailable)."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from workboard import html_page

HARNESS = r"""
const P=()=>new Proxy(function(){},{get:(t,k)=>k===Symbol.toPrimitive?(()=>''):k==='then'?undefined:P(),apply:()=>P(),set:()=>true});
const el=()=>({innerHTML:'',textContent:'{}',style:{},dataset:{},classList:{add(){},remove(){},toggle(){},contains(){return false}},addEventListener(){},querySelector:()=>el(),querySelectorAll:()=>[],closest:()=>null,appendChild(){},prepend(){}});
const store={data:{textContent:JSON.stringify({tasks:[]})}};
globalThis.document={getElementById:id=>store[id]||(store[id]=el()),querySelector:()=>el(),querySelectorAll:()=>[],addEventListener(){},createElement:()=>el(),body:el(),documentElement:el(),hidden:true,visibilityState:'hidden'};
globalThis.window=globalThis;globalThis.localStorage={getItem:()=>null,setItem(){}};globalThis.location={hash:''};globalThis.history={replaceState(){}};
globalThis.matchMedia=()=>({matches:false,addEventListener(){}});globalThis.setInterval=()=>0;globalThis.setTimeout=()=>0;globalThis.addEventListener=()=>{};
globalThis.MutationObserver=class{observe(){}};globalThis.ResizeObserver=class{observe(){}};globalThis.fetch=async()=>({ok:false});
"""

CASES = r"""
const out={};
S2TZ='America/Los_Angeles';S2DF=new Intl.DateTimeFormat('en-CA',{timeZone:S2TZ,year:'numeric',month:'2-digit',day:'2-digit'});
S2TF=new Intl.DateTimeFormat('en-GB',{timeZone:S2TZ,hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
// same elapsed: now = Thu 13:00 local; an accept yesterday at 18:00 must NOT count in the prior DoD window
todayKey=()=>'2026-10-29';nowTod=()=>13*3600;
const T=(iso,k)=>[dkey(iso),'t'+k,false,iso];
const ev=[T('2026-10-29T17:00:00Z',1),T('2026-10-28T19:00:00Z',2),T('2026-10-29T01:00:00Z',3)];   // 10:00 today, 12:00 yday, 18:00 yday
SS.compare='same';out.dod=delta(ev,'day');SS.compare='full';out.dodFull=delta(ev,'day');SS.compare='same';
// flow: S1,S2,R,S3,A -> submit->decision pairs once (S2->R, S3->A); revision->resubmit once (R->S3)
const t={t:'x',cr:'2026-10-01T00:00:00Z',subfb:false,rc:true,s:'accepted',k:'mt',r:'r',act:[],
 sub:[['2026-10-02T00:00:00Z',1],['2026-10-03T00:00:00Z',2],['2026-10-06T00:00:00Z',3]],
 dec:[['2026-10-04T00:00:00Z','revision',''],['2026-10-08T00:00:00Z','accept','']]};
const html=s2flow([t]);out.flowN=(html.match(/· n \d+/g)||[]).map(x=>x.slice(2));
// rework: an incomplete history is excluded, not counted in the zero bin
SS.range='all';const inc={...t,t:'y',rc:false,dec:[['2026-10-08T00:00:00Z','accept','']]};
out.rework=s2rework([t,inc],'2026-01-01','2027-01-01').includes('1 excluded');
console.log(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "node not installed")
class StatsJsTest(unittest.TestCase):
    def run_js(self):
        js = re.findall(r"<script[^>]*>(.*?)</script>", html_page.PAGE, re.S)[-1].replace("__LIVE__", "true")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "t.js"
            f.write_text(HARNESS + "\n(0,eval)(" + json.dumps(js + "\n" + CASES) + ");")
            p = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr[-2000:])
        return json.loads(p.stdout.strip().splitlines()[-1])

    def test_metrics(self):
        out = self.run_js()
        self.assertEqual((out["dod"]["c"], out["dod"]["p"]), (1, 1))        # yesterday 12:00 counts, 18:00 does not
        self.assertEqual(out["dodFull"]["p"], 2)                             # full prior day counts both
        self.assertEqual(out["flowN"], ["n 1", "n 2", "n 1"])               # created→submit 1, submit→decision 2, rev→resubmit 1
        self.assertTrue(out["rework"])


if __name__ == "__main__":
    unittest.main()
