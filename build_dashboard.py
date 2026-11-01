"""Build an offline interactive dashboard from the Spark CSV outputs."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="outputs")
    parser.add_argument("--output", default="dashboard.html")
    args = parser.parse_args()
    root = Path(args.input)
    data = {
        "category": read_rows(root / "category_revenue" / "part-00000.csv"),
        "recommendations": read_rows(root / "recommendations" / "part-00000.csv"),
        "funnel": read_rows(root / "funnel_by_referrer" / "part-00000.csv"),
        "cohort": read_rows(root / "cohort_revenue" / "part-00000.csv"),
        "sample": {"users": 500, "products": 300, "transactions": 2000},
    }
    page = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>E-commerce Analytics Dashboard</title>
<style>
:root{--ink:#172b24;--muted:#64756e;--green:#1b6b4a;--mint:#dff2e8;--line:#dce6e0;--paper:#f4f7f5;--white:#fff;--orange:#e07a45;--blue:#5287a8}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.45 "Segoe UI",Arial,sans-serif}header{padding:25px max(22px,calc((100vw - 1200px)/2));background:#173e30;color:#fff}header h1{margin:0 0 5px;font-size:26px}header p{margin:0;color:#d2e5dc}.wrap{max-width:1200px;margin:22px auto;padding:0 20px}.meta{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}.pill{background:var(--mint);color:#15583d;border-radius:20px;padding:5px 11px;font-size:12px;font-weight:600}.cards{display:grid;grid-template-columns:repeat(4,minmax(140px,1fr));gap:12px;margin-bottom:16px}.card,.panel{background:var(--white);border:1px solid var(--line);border-radius:12px;box-shadow:0 2px 8px #173e300a}.card{padding:15px 17px}.card .label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}.card .value{font-size:25px;font-weight:700;margin-top:5px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.panel{padding:17px 18px;min-width:0}.panel h2{font-size:17px;margin:0 0 2px}.sub{color:var(--muted);font-size:12px;margin-bottom:14px}.controls{display:flex;align-items:center;gap:8px;margin:10px 0 13px;flex-wrap:wrap}.controls label{font-size:12px;color:var(--muted)}select{border:1px solid #cbd9d1;background:white;border-radius:7px;padding:6px 9px;color:var(--ink)}.barrow{display:grid;grid-template-columns:minmax(80px,130px) 1fr auto;align-items:center;gap:9px;margin:9px 0}.barlabel{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px}.track{height:13px;background:#edf2ef;border-radius:9px;overflow:hidden}.bar{height:100%;background:var(--green);border-radius:9px;min-width:2px}.bar.orange{background:var(--orange)}.bar.blue{background:var(--blue)}.barvalue{font-size:12px;color:var(--muted);white-space:nowrap}.table{width:100%;border-collapse:collapse;font-size:12px}.table th,.table td{text-align:left;padding:8px 7px;border-bottom:1px solid #edf1ee}.table th{color:var(--muted);font-weight:600}.table td.num,.table th.num{text-align:right}.heatwrap{overflow:auto}.heat{border-collapse:separate;border-spacing:3px;font-size:11px}.heat th{font-weight:600;color:var(--muted);padding:5px;white-space:nowrap}.heat td{min-width:62px;height:39px;text-align:center;border-radius:5px;color:#143d2c}.heat td.empty{background:#f0f3f1;color:#acb8b1}.note{font-size:11px;color:var(--muted);margin:14px 0 4px}.full{grid-column:1/-1}@media(max-width:760px){.cards{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.full{grid-column:auto}.wrap{padding:0 12px}header{padding:22px 16px}.barrow{grid-template-columns:90px 1fr auto}}
</style></head><body>
<header><h1>E-commerce Analytics Dashboard</h1><p>Product revenue, purchase affinity, acquisition conversion and customer cohorts</p></header>
<main class="wrap"><div class="meta"><span class="pill">Spark 3.5.9</span><span class="pill">Synthetic sample: 10,000 sessions</span><span class="pill">MongoDB and HBase represented through exported sample data</span></div>
<section class="cards"><div class="card"><div class="label">Sessions</div><div class="value" id="kpiSessions">—</div></div><div class="card"><div class="label">Purchase-linked sessions</div><div class="value" id="kpiConversions">—</div></div><div class="card"><div class="label">Session conversion</div><div class="value" id="kpiRate">—</div></div><div class="card"><div class="label">Gross line revenue</div><div class="value" id="kpiRevenue">—</div></div></section>
<section class="grid">
<article class="panel"><h2>Category performance</h2><div class="sub">Revenue uses line-item subtotals before order discounts.</div><div class="controls"><label for="metric">Measure</label><select id="metric"><option value="revenue">Revenue</option><option value="units">Units sold</option></select><label for="categoryCount">Show</label><select id="categoryCount"><option>5</option><option selected>10</option><option>15</option><option>25</option></select></div><div id="categories"></div></article>
<article class="panel"><h2>Acquisition funnel</h2><div class="sub">Converted sessions are joined to qualifying transaction records.</div><div class="controls"><label for="referrer">Channel detail</label><select id="referrer"><option value="all">All channels</option></select></div><div id="channels"></div><div id="channelTable"></div></article>
<article class="panel"><h2>Frequently bought together</h2><div class="sub">Product pairs from the same completed order; count is order co-occurrence.</div><div class="controls"><label for="pairCount">Top pairs</label><select id="pairCount"><option>5</option><option selected>10</option><option>15</option></select></div><div id="pairs"></div></article>
<article class="panel"><h2>Cohort revenue</h2><div class="sub">Registration month by purchase month. Hover a cell for exact revenue.</div><div class="heatwrap" id="cohorts"></div></article>
</section><p class="note">Results are descriptive and come from a generated sample, not production customer or marketing data.</p></main>
<script id="payload" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('payload').textContent),money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(n),num=n=>new Intl.NumberFormat('en-US').format(n),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
D.category.forEach(x=>{x.revenue=+x.revenue;x.units=+x.units});D.funnel.forEach(x=>{for(const k of ['sessions','engaged_sessions','converted_sessions','linked_purchases','conversion_pct'])x[k]=+x[k]});D.recommendations.forEach(x=>x.count=+x.count);D.cohort.forEach(x=>{x.revenue=+x.revenue;x.buyers=+x.buyers;x.cohort_month=String(x.cohort_month).slice(0,7);x.purchase_month=String(x.purchase_month).slice(0,7)});
const totalSessions=D.funnel.reduce((a,x)=>a+x.sessions,0),totalConverted=D.funnel.reduce((a,x)=>a+x.converted_sessions,0),totalRevenue=D.category.reduce((a,x)=>a+x.revenue,0);document.getElementById('kpiSessions').textContent=num(totalSessions);document.getElementById('kpiConversions').textContent=num(totalConverted);document.getElementById('kpiRate').textContent=(100*totalConverted/totalSessions).toFixed(2)+'%';document.getElementById('kpiRevenue').textContent=money(totalRevenue);
const select=document.getElementById('referrer');D.funnel.slice().sort((a,b)=>a.referrer.localeCompare(b.referrer)).forEach(x=>select.insertAdjacentHTML('beforeend',`<option value="${esc(x.referrer)}">${esc(x.referrer)}</option>`));
function renderCategories(){const key=document.getElementById('metric').value,n=+document.getElementById('categoryCount').value,rows=D.category.slice().sort((a,b)=>b[key]-a[key]).slice(0,n),max=Math.max(...rows.map(x=>x[key]),1);document.getElementById('categories').innerHTML=rows.map(x=>`<div class="barrow"><div class="barlabel">${esc(x.category_id)}</div><div class="track"><div class="bar" style="width:${100*x[key]/max}%"></div></div><div class="barvalue">${key==='revenue'?money(x[key]):num(x[key])}</div></div>`).join('')}
function renderChannels(){const chosen=select.value,rows=D.funnel.filter(x=>chosen==='all'||x.referrer===chosen),max=Math.max(...D.funnel.map(x=>x.conversion_pct),1);document.getElementById('channels').innerHTML=D.funnel.slice().sort((a,b)=>b.conversion_pct-a.conversion_pct).map(x=>`<div class="barrow"><div class="barlabel">${esc(x.referrer)}</div><div class="track"><div class="bar orange" style="width:${100*x.conversion_pct/max}%"></div></div><div class="barvalue">${x.conversion_pct.toFixed(2)}%</div></div>`).join('');document.getElementById('channelTable').innerHTML=rows.length?`<table class="table"><thead><tr><th>Channel</th><th class="num">Sessions</th><th class="num">Converted</th><th class="num">Rate</th></tr></thead><tbody>${rows.map(x=>`<tr><td>${esc(x.referrer)}</td><td class="num">${num(x.sessions)}</td><td class="num">${num(x.converted_sessions)}</td><td class="num">${x.conversion_pct.toFixed(2)}%</td></tr>`).join('')}</tbody></table>`:''}
function renderPairs(){const n=+document.getElementById('pairCount').value,rows=D.recommendations.slice().sort((a,b)=>b.count-a.count||a.left.localeCompare(b.left)||a.right.localeCompare(b.right)).slice(0,n);document.getElementById('pairs').innerHTML=`<table class="table"><thead><tr><th>Product pair</th><th class="num">Orders</th></tr></thead><tbody>${rows.map(x=>`<tr><td>${esc(x.left)} + ${esc(x.right)}</td><td class="num">${num(x.count)}</td></tr>`).join('')}</tbody></table>`}
function renderCohorts(){const rows=[...new Set(D.cohort.map(x=>x.cohort_month))].sort(),cols=[...new Set(D.cohort.map(x=>x.purchase_month))].sort(),map=new Map(D.cohort.map(x=>[x.cohort_month+'|'+x.purchase_month,x.revenue])),max=Math.max(...D.cohort.map(x=>x.revenue),1);document.getElementById('cohorts').innerHTML=`<table class="heat"><thead><tr><th>Registered</th>${cols.map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr><th>${esc(r)}</th>${cols.map(c=>{const v=map.get(r+'|'+c);return v===undefined?'<td class="empty">·</td>':`<td title="Registration ${esc(r)} / purchase ${esc(c)}: ${money(v)}" style="background:rgba(38,130,86,${.12+.75*v/max})">${money(v)}</td>`}).join('')}</tr>`).join('')}</tbody></table>`}
document.getElementById('metric').onchange=renderCategories;document.getElementById('categoryCount').onchange=renderCategories;select.onchange=renderChannels;document.getElementById('pairCount').onchange=renderPairs;renderCategories();renderChannels();renderPairs();renderCohorts();
</script></body></html>'''
    embedded = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    output = Path(args.output)
    output.write_text(page.replace("__DATA__", embedded), encoding="utf-8")
    print(f"Built {output.resolve()}")


if __name__ == "__main__":
    main()
