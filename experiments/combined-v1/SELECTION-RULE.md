# Evidence-budget selection rule (frozen BEFORE the offline coverage run on fresh-business-v1)

Written 2026-11-24, before any packet for the fresh questions was computed. Development data (C01–C15) showed top-16 31/41 and 6k skip-fit 34/41.

**Measured offline (0 model calls)** on the 10 sealed fresh questions, using the Baseline route (B2, table comparisons off) and the frozen packet policies:

- exact anchored required points (a point counts when any of its anchor groups is fully inside the packet; evidence-absent points are excluded);
- fully anchored questions;
- passages per packet;
- evidence tokens (MiniLM passage text);
- the bounded estimate of the full synthesis request (`request_guard.estimate`);
- split all-or-none table pairs.

**Rule:**

1. Choose **6k skip-fit** only if it covers **at least 2 more anchored points** than top-16. Its estimated synthesis request must also be within the per-call request cap on every question, and it must split no anchor table pair that top-16 keeps whole.
2. Otherwise choose **top-16**: it is simpler, within the existing API limit, and has a deterministic size.
3. The same selected budget is used as Multi-Agent's initial evidence. The Multi-Agent route (table comparisons on) is reported, but it does not change the choice.
4. Top-8 (current) and the 8k prefix are reported as references only.

**Caveat:** this is a small-sample configuration choice made offline on the evaluation questions themselves. This is why the live evaluation is labelled preliminary.
