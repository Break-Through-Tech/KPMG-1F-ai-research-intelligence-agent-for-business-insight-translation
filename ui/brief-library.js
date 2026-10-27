/* Saved snapshots are server-owned. Reopening never invokes research or changes its context. */
(() => {
  'use strict';
  let enabled = false, live = false, revision = null, offset = 0, loadSequence = 0, restoreFocus = true;
  const dialog = document.querySelector('#brief-library');
  const results = document.querySelector('#brief-list');
  const status = document.querySelector('#library-status');
  const search = document.querySelector('#brief-search');
  const archived = document.querySelector('#brief-archived');
  const banner = document.querySelector('#brief-revision');
  const trigger = document.querySelector('#library-open');
  function node(tag, text, className) {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (className) el.className = className;
    return el;
  }
  function button(text, action) {
    const el = node('button', text, 'quiet'); el.type = 'button';
    el.addEventListener('click', action); return el;
  }
  async function api(path, payload) {
    const response = await fetch(path, {signal: AbortSignal.timeout(15000),
      ...(payload === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Saved work is unavailable.');
    return data;
  }
  function openSnapshot(demo) {
    if (dialog.open) { restoreFocus = false; dialog.close(); }
    document.dispatchEvent(new CustomEvent('brief-open', {detail: demo}));
  }
  async function operation(control, message, action) {
    if (control.disabled) return;
    control.disabled = true;
    try { await action(); }
    catch (error) { message.textContent = error.message || 'Saved-work request failed. Your answer is unchanged.'; }
    finally { control.disabled = false; }
  }
  async function load() {
    const sequence = ++loadSequence;
    status.textContent = 'Loading saved briefs…';
    results.setAttribute('aria-busy', 'true');
    try {
      const params = new URLSearchParams({q: search.value, archived: archived.checked ? '1' : '0', offset});
      const data = await api(`/api/briefs?${params}`);
      if (sequence !== loadSequence) return;
      results.replaceChildren();
      for (const brief of data.briefs) {
        const item = node('li');
        const open = button(brief.title, () => operation(open, status, async () => {
          openSnapshot(await api(`/api/briefs/${brief.id}`));
        }));
        item.append(open, node('p', `Version ${brief.number} · ${brief.review_status} · ${brief.mode === 'fixture' ? 'Synthetic example' : 'Research snapshot'} · ${new Date(brief.updated_at).toLocaleString()}`, 'meta'));
        results.append(item);
      }
      document.querySelector('#brief-previous').disabled = offset === 0;
      document.querySelector('#brief-next').disabled = data.briefs.length < 30;
      status.textContent = data.briefs.length ? `Showing ${offset + 1}–${offset + data.briefs.length}. Reopening uses saved evidence; no model call.` : 'No saved briefs here. Generate an answer or import a result JSON file.';
    } catch (error) { if (sequence === loadSequence) status.textContent = error.message || 'Could not load saved briefs. Try Refresh.'; }
    finally { if (sequence === loadSequence) results.setAttribute('aria-busy', 'false'); }
  }
  trigger.addEventListener('click', () => { dialog.showModal(); search.focus(); offset = 0; load(); });
  document.querySelector('#library-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { if (restoreFocus) trigger.focus(); restoreFocus = true; });
  document.querySelector('#library-search-form').addEventListener('submit', event => { event.preventDefault(); offset = 0; load(); });
  archived.addEventListener('change', () => { offset = 0; load(); });
  document.querySelector('#brief-previous').addEventListener('click', () => { offset = Math.max(0, offset - 30); load(); });
  document.querySelector('#brief-next').addEventListener('click', () => { offset += 30; load(); });
  function importControl(label, target, onSaved, message) {
    const wrap = node('label', label, 'brief-import');
    const input = node('input'); input.type = 'file'; input.accept = '.json,application/json';
    input.addEventListener('change', () => operation(input, message, async () => {
      if (!input.files[0]) return;
      if (input.files[0].size > 8_000_000) throw new Error('Snapshot exceeds 8 MB.');
      const value = JSON.parse(await input.files[0].text());
      const envelope = value.result ? value : null;
      const saved = await api('/api/briefs', {...(envelope ? {envelope} : {result: value}), ...(target || {})});
      input.value = ''; await onSaved(saved);
    }));
    wrap.append(input); return wrap;
  }
  document.querySelector('#library-import').append(importControl('Import result JSON', null,
    async saved => { status.textContent = 'Snapshot imported. No model call.'; openSnapshot(saved); }, status));
  function reviewText(demo) {
    const latest = demo.library?.reviews.at(-1);
    if (!latest) return 'Draft · Not approved';
    return {approve: 'Saved version approved by human reviewer · Not source certification',
      revise: 'Changes requested · Not approved', reject: 'Rejected · Not approved'}[latest.decision];
  }
  function controls(demo, onChanged) {
    const root = node('details', undefined, 'brief-controls');
    root.append(node('summary', demo.library ? `Saved brief · Version ${demo.library.version.number}` : 'Save this answer'));
    const message = node('p', demo.library_error || '', 'meta'); message.setAttribute('role', 'status');
    root.append(message);
    if (demo.library_error) { root.open = true; message.className = 'error'; }
    root.append(button('Export snapshot JSON', () => {
      const url = URL.createObjectURL(new Blob([JSON.stringify(demo, null, 2)], {type: 'application/json'}));
      const link = node('a'); link.href = url; link.download = 'research-snapshot.json'; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }));
    if (!enabled) { root.append(node('p', 'Persistent library disabled for this session.', 'meta')); return root; }
    if (!demo.library) {
      const save = button('Save as separate brief', () => operation(save, message, async () => {
        const saved = await api('/api/briefs', {envelope: demo}); onChanged(saved);
      })); root.append(save); return root;
    }
    const {brief, version, versions, reviews} = demo.library;
    const current = !brief.archived && version.id === brief.current_version;
    root.append(node('p', `${brief.title} · ${demo.mode === 'fixture' ? 'Synthetic example, not live research' : 'Retained research snapshot'}`, 'meta'));
    root.append(node('p', 'Reviews belong to this exact snapshot, including its evidence and presentation. Original result JSON and existing HTML/Markdown exports remain pending drafts; library decisions are retained separately in snapshot JSON.', 'meta'));
    const versionLabel = node('label', 'Version history');
    const select = node('select');
    versions.forEach(v => { const option = node('option', `Version ${v.number} · ${v.audience} · ${new Date(v.created_at).toLocaleString()}`); option.value = v.id; select.append(option); });
    select.value = version.id;
    versionLabel.append(select); root.append(versionLabel);
    const view = button('Open selected version', () => operation(view, message, async () => {
      openSnapshot(await api(`/api/briefs/${brief.id}?version=${select.value}`));
    })); root.append(view);
    const titleLabel = node('label', 'Brief title');
    const title = node('input'); title.type = 'text'; title.maxLength = 200; title.value = brief.title;
    titleLabel.append(title); root.append(titleLabel);
    const rename = button('Rename brief', () => operation(rename, message, async () => {
      const saved = await api(`/api/briefs/${brief.id}`, {expected_version: version.id, title: title.value}); onChanged(saved);
    })); rename.disabled = version.id !== brief.current_version; root.append(rename);
    const archive = button(brief.archived ? 'Restore brief' : 'Archive brief', () => operation(archive, message, async () => {
      const saved = await api(`/api/briefs/${brief.id}`, {expected_version: version.id, archived: !brief.archived}); onChanged(saved);
    })); archive.disabled = version.id !== brief.current_version; root.append(archive);
    if (current) {
      root.append(importControl('Import a new version JSON', {brief_id: brief.id, expected_version: version.id}, onChanged, message));
      if (live) root.append(button('Revise with new research', () => {
        revision = {brief_id: brief.id, expected_version: version.id};
        banner.hidden = false; banner.querySelector('span').textContent = `Next accepted answer becomes a new version of “${brief.title}”. This reruns research using the current source configuration.`;
        const input = document.querySelector('#query'); input.value = demo.result.request.query; input.focus();
      }));
      const review = node('form', undefined, 'brief-review');
      const reviewerLabel = node('label', 'Reviewer name');
      const reviewer = node('input'); reviewer.type = 'text'; reviewer.required = true; reviewer.maxLength = 120; reviewer.autocomplete = 'name'; reviewerLabel.append(reviewer);
      const decisionLabel = node('label', 'Review decision');
      const decision = node('select');
      [['approve', 'Approve this version'], ['revise', 'Request changes'], ['reject', 'Reject this version']].forEach(([value, text]) => {
        const option = node('option', text); option.value = value; decision.append(option);
      }); decisionLabel.append(decision);
      const notesLabel = node('label', 'Review notes (required for changes)');
      const notes = node('textarea'); notes.maxLength = 4000; notes.rows = 2; notesLabel.append(notes);
      const send = node('button', 'Record review', 'quiet'); send.type = 'submit';
      review.append(reviewerLabel, decisionLabel, notesLabel, send);
      review.addEventListener('submit', event => { event.preventDefault(); operation(send, message, async () => {
        const saved = await api(`/api/briefs/${brief.id}/reviews`, {version_id: version.id, fingerprint: version.fingerprint,
          reviewer: reviewer.value, decision: decision.value, notes: notes.value || null}); onChanged(saved);
      }); }); root.append(review);
    } else root.append(node('p', brief.archived ? 'Restore this brief before adding versions or reviews.' : 'Historical version. Open the latest version before revising or reviewing.', 'meta'));
    const history = node('ul'); history.setAttribute('aria-label', 'Review history');
    for (const review of reviews) history.append(node('li', `${review.decision} · ${review.reviewer} · ${new Date(review.created_at).toLocaleString()}${review.notes ? ` — ${review.notes}` : ''}`));
    root.append(history); return root;
  }
  document.querySelector('#brief-revision-cancel').addEventListener('click', () => { revision = null; banner.hidden = true; });
  window.BriefLibrary = {controls, reviewText, configure(config) {
    enabled = config.library === true; live = config.live === true; trigger.hidden = !enabled;
  }, revision: () => revision && {...revision}, finishRevision() { revision = null; banner.hidden = true; }};
})();
