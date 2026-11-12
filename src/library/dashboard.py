"""Local read-only research library dashboard (live progress from the SQLite state)."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

from .discovery import TOPICS
from .store import Store

LABELS = {**{k: v[0] for k, v in TOPICS.items()}, 'existing-library': 'Existing library (seed)'}


def status(root, target=1000):
    store = Store(root, readonly=True)
    q = lambda sql, *a: store.db.execute(sql, a).fetchall()
    counts = {r['status']: r['n'] for r in q('SELECT status, COUNT(*) n FROM papers GROUP BY status')}
    indexed = counts.get('indexed', 0) + counts.get('update_available', 0)
    topics = []
    for r in q("SELECT topic, SUM(status IN ('indexed','update_available')) idx, "
               "SUM(status='extracted') ext, COUNT(*) n FROM papers GROUP BY topic ORDER BY idx DESC"):
        topics.append({'topic': r['topic'], 'label': LABELS.get(r['topic'], r['topic']),
                       'indexed': r['idx'], 'extracted': r['ext'], 'discovered': r['n']})
    recent = [dict(r) for r in q("SELECT arxiv_id, title, topic, extracted_at, indexed_at, parents, status "
                                  "FROM papers WHERE status IN ('extracted','indexed','update_available') "
                                  "AND source='arxiv' ORDER BY extracted_at DESC LIMIT 15")]
    failures = [dict(r) for r in q("SELECT arxiv_id, title, status, last_error, attempts FROM papers "
                                    "WHERE status IN ('failed','skipped') ORDER BY rowid DESC LIMIT 12")]
    reasons = [dict(r) for r in q("SELECT CASE WHEN last_error LIKE 'no versioned HTML%' THEN 'No arXiv HTML' "
                                   "WHEN last_error LIKE 'unreadable%' THEN 'Unreadable or too short' "
                                   "ELSE 'Network / rate limit (retryable)' END reason, COUNT(*) n "
                                   "FROM papers WHERE status IN ('failed','skipped') GROUP BY reason")]
    bundles = [dict(r) for r in q('SELECT * FROM bundles ORDER BY created_at DESC LIMIT 5')]
    events = [dict(r) for r in q('SELECT at, kind, base_id, detail FROM events ORDER BY id DESC LIMIT 12')]
    pages = q('SELECT topic, COUNT(*) pages, SUM(results) results FROM discovery_pages GROUP BY topic')
    rate = q("SELECT COUNT(*) n, MIN(extracted_at) a, MAX(extracted_at) b FROM papers "
             "WHERE extracted_at >= datetime('now', '-30 minutes') AND source='arxiv'")
    current = (Path(root) / 'CURRENT').read_text().strip() if (Path(root) / 'CURRENT').is_file() else None
    store.db.close()
    ready = indexed + counts.get('extracted', 0)
    return {'target': target, 'indexed': indexed, 'ready': ready, 'counts': counts, 'topics': topics,
            'recent': recent, 'failures': failures, 'failure_reasons': reasons, 'bundles': bundles,
            'events': events, 'current_bundle': current,
            'discovery': [dict(r) for r in pages], 'extracted_last_30_min': rate[0]['n'] if rate else 0}


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Research Library</title><style>
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d2433;--muted:#5d6577;--line:#e3e4e8;--accent:#00338d;--ok:#1e7a46;--warn:#9a6700;--bad:#b42318}
@media (prefers-color-scheme:dark){:root{--bg:#14161b;--card:#1c1f26;--ink:#e8eaf0;--muted:#a3a9b8;--line:#2c3039;--accent:#7fa7ff;--ok:#5cc98a;--warn:#e0b44c;--bad:#ff8a80}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px}h1{font-size:22px;margin:0 0 4px}.sub{color:var(--muted);margin:0 0 20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.k{color:var(--muted);font-size:13px}.v{font-size:26px;font-weight:650;font-variant-numeric:tabular-nums}
.bar{height:10px;background:var(--line);border-radius:5px;overflow:hidden;margin-top:8px}.bar>i{display:block;height:100%;background:var(--accent)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media (max-width:760px){.two{grid-template-columns:1fr}}
h2{font-size:15px;margin:0 0 10px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:6px 4px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:500}.num{text-align:right;font-variant-numeric:tabular-nums}.muted{color:var(--muted)}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}a{color:var(--accent)}.wrap{overflow-x:auto}
</style></head><body><main><h1>Research Library</h1><p class="sub" id="sub">Loading…</p>
<div class="grid" id="kpis"></div><div class="card" style="margin-bottom:12px"><h2>Ingestion progress</h2><div id="progress"></div></div>
<div class="two"><div class="card"><h2>Research categories</h2><div class="wrap"><table id="topics"></table></div></div>
<div class="card"><h2>Failures and skips</h2><div class="wrap"><table id="reasons"></table></div><div class="wrap"><table id="failures"></table></div></div></div>
<div class="card" style="margin-top:12px"><h2>Recently added papers</h2><div class="wrap"><table id="recent"></table></div></div>
<div class="two" style="margin-top:12px"><div class="card"><h2>Index builds</h2><div class="wrap"><table id="bundles"></table></div></div>
<div class="card"><h2>Activity</h2><div class="wrap"><table id="events"></table></div></div></div></main>
<script>
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const rows=(el,head,data)=>{document.getElementById(el).innerHTML='<tr>'+head.map(h=>`<th class="${h[2]||''}">${h[0]}</th>`).join('')+'</tr>'+(data.length?data.map(r=>'<tr>'+head.map(h=>`<td class="${h[2]||''}">${h[1](r)}</td>`).join('')+'</tr>').join(''):`<tr><td colspan="${head.length}" class="muted">None yet</td></tr>`)};
async function load(){try{const s=await (await fetch('api/status',{cache:'no-store'})).json();const c=s.counts;
document.getElementById('sub').textContent=`Current index: ${s.current_bundle||'not built yet'} · refreshes every 10 s`;
const pct=Math.min(100,100*s.indexed/s.target);
document.getElementById('kpis').innerHTML=[['Indexed and searchable',s.indexed],['Extracted, awaiting index',c.extracted||0],['Candidates in queue',(c.discovered||0)+(c.failed||0)],['Skipped (no HTML / unreadable)',c.skipped||0],['Newer versions pending',c.update_available||0]].map(([k,v])=>`<div class="card"><div class="k">${k}</div><div class="v">${v}</div></div>`).join('');
document.getElementById('progress').innerHTML=`<div>${s.indexed} of ${s.target} papers indexed (${pct.toFixed(1)}%) · ${s.ready} ready including extracted · ${s.extracted_last_30_min} extracted in the last 30 min</div><div class="bar"><i style="width:${pct}%"></i></div>`;
rows('topics',[['Category',r=>esc(r.label)],['Indexed',r=>r.indexed,'num'],['Extracted',r=>r.extracted,'num'],['Discovered',r=>r.discovered,'num']],s.topics);
rows('reasons',[['Reason',r=>esc(r.reason)],['Papers',r=>r.n,'num']],s.failure_reasons);
rows('failures',[['Paper',r=>`<a href="https://arxiv.org/abs/${esc(r.arxiv_id)}" target="_blank" rel="noopener">${esc(r.arxiv_id)}</a>`],['Status',r=>`<span class="${r.status==='failed'?'warn':'muted'}">${esc(r.status)}</span>`],['Detail',r=>esc(r.last_error)]],s.failures);
rows('recent',[['Paper',r=>`<a href="https://arxiv.org/abs/${esc(r.arxiv_id)}" target="_blank" rel="noopener">${esc(r.title)}</a>`],['Category',r=>esc(r.topic)],['Passages',r=>r.parents,'num'],['Status',r=>`<span class="${r.status==='indexed'?'ok':'warn'}">${esc(r.status)}</span>`],['Extracted (UTC)',r=>esc((r.extracted_at||'').replace('T',' ').slice(0,16))]],s.recent);
rows('bundles',[['Build',r=>esc(r.bundle_id)],['Papers',r=>r.papers,'num'],['Embedded / reused',r=>`${r.embedded_papers} / ${r.reused_papers}`,'num'],['Seconds',r=>r.seconds,'num'],['Status',r=>esc(r.status)]],s.bundles);
rows('events',[['Time (UTC)',r=>esc(r.at.slice(11,19))],['Event',r=>esc(r.kind)],['Detail',r=>esc(r.detail||r.base_id||'')]],s.events);
}catch(e){document.getElementById('sub').textContent='Dashboard could not read library status: '+e}}
load();setInterval(load,10000);
</script></body></html>"""


def serve(root, *, port=8790, target=1000):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith('/api/status'):
                body, kind = json.dumps(status(root, target)).encode(), 'application/json'
            elif self.path in ('/', '/index.html'):
                body, kind = PAGE.encode(), 'text/html; charset=utf-8'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass
    with ThreadingHTTPServer(('127.0.0.1', port), Handler) as server:
        print(f'Research library dashboard: http://127.0.0.1:{server.server_port}/', flush=True)
        server.serve_forever()
