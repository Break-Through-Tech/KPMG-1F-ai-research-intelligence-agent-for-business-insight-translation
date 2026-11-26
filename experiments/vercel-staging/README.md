# KPMG protected staging

## Static package

Build with Python 3.11 or newer. Point --source at the Claude UI refresh checkout and --output at a new directory. The current snapshot came from the dirty ui-consult refresh at base 9994eed920d0afd9ee5f36769077a05137763d6e.

    python build.py --source <refresh-checkout> --output <new-site-directory>
    node smoke.cjs <site-directory> <installed-playwright-module> <chromium-executable>

Upload only the generated site directory. It contains plain HTML, JavaScript and CSS, vendored KaTeX, and curated JSON from two recorded public-arXiv cases. The library includes a CU-DPO draft and a Fin-RATE / MultiRAG evidence-insufficient result. Their claim text, citations, and source cells are retained. Business context, private database records, original reviewer metadata, local paths and provider metadata are omitted. Draft status is preserved. Table caption, row IDs, cell IDs and index fingerprints are preserved. An automatically inferred header remains labeled as such.

The staging-only fetch adapter serves the two recordings locally in the browser, disables writes, and refuses unknown table/index pairs. Research does not run. No provider keys or cloud environment variables are required. Navigation runs within the page at the root URL.

## Preview deployment

Sign in to Vercel CLI with an approved organization or course workspace. Use an existing protected staging project or create an empty eligible project before uploading. Verify Vercel Authentication and Preview protection in the dashboard. Prefer All Deployments if supported by the intended scope. Keep access limited to intended reviewers.

    pnpm dlx vercel whoami
    pnpm dlx vercel --cwd <site-directory> deploy --scope <team> --project <staging-project> --dry
    pnpm dlx vercel --cwd <site-directory> deploy --scope <team> --project <staging-project>

Submit the **preview** deploy only. Avoid Git import, production flags, temporary anonymous deployments and public aliases. Check that signed-out clients cannot retrieve / or /_recorded/briefs.json directly. Then sign in as an intended reviewer and verify both recordings, chart-to-cell navigation, the exact original citation URL, phone layout, and clean failure on missing evidence. Grant reviewer access through the approved project account.

Reference links for Vercel [Deployment Protection](https://vercel.com/docs/deployment-protection), [Preview sharing](https://vercel.com/docs/deployments/sharing-deployments), and [CLI deploy](https://vercel.com/docs/cli/deploy).

## Live Baseline/B2 handoff

Use the existing Python HTTP contract, with a warm Baseline/B2 process on one approved VM or managed container. The current launcher binds to loopback and checks Host and Origin. Place a private authenticated gateway beside it, or update a deployment wrapper to enforce trusted ingress deliberately. Keep the Python port private and keep browser requests same-origin through an allowlisted edge proxy. Set proxy timeouts against measured question latency. Use a health/readiness probe that returns ready after opening the index and loading both local models.

| Request | Initial live contract |
| --- | --- |
| GET /api/config | Require live=true and mode=indexed. Read context_id and optional capability flags. Drop internal paths and provider metadata from external responses while preserving index identity. |
| GET /api/saved-result | Return null for a fresh session. |
| POST /api/research | Send JSON with query, context_id from config, and interpret_context. The existing page also sends scenario=full. Read the envelope result, summary, evidence and library metadata as applicable. An evidence-insufficient summary is a normal research outcome. |
| GET /api/evidence-table?chunk_id=&index= | Optional read-only endpoint using the exact versioned row and index fingerprint. If unavailable or mismatched, keep retrieved rows and leave the complete-table chart unavailable. |
| GET/POST /api/briefs, GET/POST /api/briefs/{id}, POST /api/briefs/{id}/reviews | Enable only with authenticated per-user access and approved durable storage. Start with library disabled for a live research-only preview. |

Return sanitized errors. The existing handler returns 400 for invalid input, 409 for a stale context or busy synthesis, 502 for a synthesis/validation failure, and 503 for unavailable capabilities. Preserve abstention separately from errors. Expose a distinct overload/quota response at the gateway and avoid retrying generation automatically.

Mount an approved, versioned corpus, embeddings and CPU encoder/reranker files read-only. Keep model credentials in the host's secret store. Add identity, a small concurrency limit, request and token reservations with persistent usage, and a hard stop at the approved quota. Start with Baseline research and citations, then enable full tables, business translation and durable briefs only when their permissions and latency are tested. Keep the experimental agentic path unrouted.

The Vercel deployment is static. The current Python application maintains a loaded index and models across requests and expects persistent storage for saved briefs. A Vercel Function migration would require packaging, cold-start, memory, timeout, state and concurrency testing. No function migration has been attempted. [Vercel Functions limits](https://vercel.com/docs/functions/limitations)
