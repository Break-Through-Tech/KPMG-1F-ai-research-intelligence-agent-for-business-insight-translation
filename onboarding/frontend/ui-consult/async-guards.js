/* Small, pure helpers for asynchronous UI state (audit fixes, 2026-11-17).
   No DOM and no network of their own: callers pass loaders and clocks in, so every rule here
   is covered by deterministic tests (tests/evidence.test.js, "async" group).

   - createNavGuard: a navigation token. A slow saved-brief response may only change the view
     if no newer navigation happened while it was in flight (audit M2).
   - createResultCache: in-flight de-duplication kept apart from a bounded-lifetime cache of
     successful results only, so a temporary failure is never remembered (audit L3).
   - writeFailure / reviewRecorded / briefChanged / importRecorded: after a write times out or
     the connection drops, the outcome is unknown, not "nothing changed" (audit M4). The page
     reloads the saved state; a match confirms the write, but a missing match proves nothing
     (the write may still commit), so the outcome then stays unknown (verification blocker 1). */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AsyncGuards = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  function createNavGuard() {
    let epoch = 0;
    return {
      begin() { epoch += 1; return epoch; },
      bump() { epoch += 1; },
      peek() { return epoch; },
      isCurrent(token) { return token === epoch; },
    };
  }

  function createResultCache({ttlMs = 10 * 60 * 1000, now = () => Date.now()} = {}) {
    const inflight = new Map();
    const settled = new Map();
    return {
      get(key, loader) {
        const hit = settled.get(key);
        if (hit && now() - hit.at < ttlMs) return Promise.resolve(hit.value);
        if (hit) settled.delete(key);
        if (inflight.has(key)) return inflight.get(key);
        const pending = Promise.resolve().then(loader).then(value => {
          inflight.delete(key);
          if (value && value.ok === true) settled.set(key, {value, at: now()});
          return value;
        }, error => { inflight.delete(key); throw error; });
        inflight.set(key, pending);
        return pending;
      },
      has(key) { const hit = settled.get(key); return Boolean(hit && now() - hit.at < ttlMs); },
      clear() { inflight.clear(); settled.clear(); },
      get size() { return settled.size; },
    };
  }

  /* What a failed request means. `write` is true for requests that change saved work. */
  /* What a failed request means. `write` is true for requests that change saved work.
     Only two answers are conclusive for a write: a 4xx refusal (the backend or proxy answered
     and declined, so nothing was stored) and a proxy report that the request was never sent
     (`write_outcome: "not_sent"`, i.e. the backend connection never opened). A browser timeout,
     a dropped connection, a 408 or any 5xx (including the proxy's 504 after it forwarded the
     write) leaves the outcome unknown: the write may already be stored, or may still commit. */
  function writeFailure(error, {write}) {
    const timeout = ['TimeoutError', 'AbortError'].includes(error && error.name);
    const status = error && error.status;
    if (Number.isInteger(status)) {
      if (!write) return {kind: 'rejected', status};
      if (status >= 400 && status < 500 && status !== 408) return {kind: 'rejected', status};
      if (error.writeOutcome === 'not_sent') return {kind: 'not_applied', status, timeout: status === 504};
      return {kind: 'unknown', status, timeout: status === 504 || status === 408};
    }
    if (!timeout && !(error instanceof TypeError)) return {kind: 'failed'};
    // A read that never answered changed nothing. A write may have committed before its response was lost.
    return {kind: write ? 'unknown' : 'not_applied', timeout};
  }

  /* JSON equality that ignores object key order (stored envelopes may reorder keys). */
  const canonical = value => Array.isArray(value) ? value.map(canonical)
    : value && typeof value === 'object' ? Object.keys(value).sort().map(key => [key, canonical(value[key])]) : value;
  const sameJson = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));

  /* Version import: confirmed only when the brief's current version is a NEW version whose
     stored result is exactly the imported result. Any other newer version (someone else's
     import or revision) proves nothing about this import. */
  function importRecorded(latest, expectedVersion, importedResult) {
    const library = latest && latest.library;
    if (!library || !library.version || library.version.id === expectedVersion) return false;
    if (library.brief && library.brief.current_version !== library.version.id) return false;
    return Boolean(importedResult) && sameJson(latest.result, importedResult);
  }

  const norm = value => (typeof value === 'string' ? value.trim() : value ?? null) || null;
  const sameReview = (review, sent) => review && norm(review.reviewer) === norm(sent.reviewer)
    && review.decision === sent.decision && norm(review.notes) === norm(sent.notes);
  /* True when the reloaded history holds more matching reviews than before the write. */
  function reviewRecorded(before, after, sent) {
    const count = list => (Array.isArray(list) ? list : []).filter(review => sameReview(review, sent)).length;
    return count(after) > count(before);
  }
  /* For rename / archive: does the reloaded brief already carry the requested values? */
  function briefChanged(brief, sent) {
    if (!brief) return false;
    return Object.entries(sent).every(([key, value]) => key === 'expected_version'
      || (key === 'title' ? norm(brief.title) === norm(value) : brief[key] === value));
  }

  return {createNavGuard, createResultCache, writeFailure, reviewRecorded, briefChanged, importRecorded, sameJson};
});
