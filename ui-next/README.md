# Research workspace redesign — prototype

Frontend-only prototype of the redesigned 1F research workspace. It runs on mock
data in the browser; no retrieval, embedding, arXiv, business-translation or
regulatory code is imported or changed, and `ui/` and `src/` are untouched.

## Run

```
python ui-next/serve.py
```

Open <http://127.0.0.1:8814/> in Chrome. Pass another port as an argument if 8814 is taken.

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

To try the UI against a real backend later, serve these files from the demo
server and remove the `mock-api.js` script tag (or load the page with `?live=1`).

## Testing states

Research settings → Mock response switches the mock backend between a full
answer, a clarifying question, a partial answer, abstention, no evidence, a
provider error, a changed index context and an unreachable server.
