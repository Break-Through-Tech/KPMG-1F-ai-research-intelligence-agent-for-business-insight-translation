/* Browser runner (CSP forbids inline scripts). Results are also exposed as window.testResults. */
window.runEvidenceTests().then(results => {
  window.testResults = results;
  const list = document.getElementById('results');
  for (const r of results) {
    const item = document.createElement('li');
    item.className = r.ok ? 'pass' : 'fail';
    item.textContent = `${r.ok ? 'PASS' : 'FAIL'} — ${r.name}${r.ok ? '' : ` — ${r.error}`}`;
    list.append(item);
  }
  const failed = results.filter(r => !r.ok).length;
  document.getElementById('summary').textContent = `${results.length - failed} of ${results.length} passed`;
});
