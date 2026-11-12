# Research workspace redesign — prototype

Frontend-only prototype of the redesigned 1F research workspace. It runs on mock
data in the browser; no retrieval, embedding, arXiv, business-translation or
regulatory code is imported or changed, and `ui/` and `src/` are untouched.

## Run

Mock data (UI development, no backend needed):

```
python ui-next/serve.py
```

Open <http://127.0.0.1:8814/>.

Live data (reuses a Research Desk backend that is already running on this machine):

```
python ui-next/serve.py --backend http://127.0.0.1:8801
```

Open <http://127.0.0.1:8814/?live=1>. `serve.py` never starts a backend. With
`--backend` it forwards only `/api/config`, `/api/saved-result`, `/api/research`,
`/api/demo` and `/api/briefs...` to that loopback address, accepts requests only
from its own page origin, and loads the shared reader/export/read-aloud modules
from the backend so they match its API. Without `?live=1` the page stays on mock data.

## How it is put together

| File | Role |
| --- | --- |
| `index.html`, `workspace.css`, `workspace.js` | New shell, styling and interaction layer |
| `prefs.js` | Reading preferences; same storage key and `data-*` attributes as `ui/reading-preferences.js` |
| `mock-api.js` | Prototype only. Answers `/api/*` in the browser with envelopes shaped like the real ones |
| `serve.py` | Prototype only. Serves `ui-next/` first, then falls back to `ui/`, with the production CSP |

Reused unmodified from `ui/`: `source-reader.js` (source passage, structured
reader, table/formula navigation), `math.js` + KaTeX, `answer-export.js`,
`research-speech.js` + `read-aloud.mjs`.

`workspace.js` calls the same endpoints with the same payloads as `ui/app.js`
and `ui/brief-library.js`: `GET /api/config`, `GET /api/saved-result`,
`POST /api/research` / `/api/demo`, and the `/api/briefs` family. The one
addition is sending the optional `industry` field (already accepted by
`IndexedResearch.prepare_request`) when the Industry context setting is filled.

Live-mode behaviour that differs from the mock:

- Answers are saved automatically by the backend; the Brief panel opens on that saved version.
- Review status in lists arrives as `pending`, `approve`, `revise` or `reject`.
- HTTP 409 on a brief means the snapshot is stale; the panel offers to reopen the latest version.
- The backend refuses approval while a requested risk & compliance check is unresolved, so the
  Approve option is disabled for those answers.
- A failed business or risk & compliance stage arrives as `result` plus `error`; findings stay visible.
- `provenance.arxiv_search` reports the arXiv fallback outcome and the papers examined.

## Testing states

Research settings → Mock response switches the mock backend between a full
answer, a clarifying question, a partial answer, abstention, no evidence, a
provider error, a changed index context and an unreachable server.
