/* Apply before first paint; storage contains display preferences only, never research. */
(() => {
  const key = '1f.reading-preferences.v1';
  const defaults = {theme: 'system', size: '100', spacing: 'standard', explanation: 'technical'};
  const choices = {theme: ['system', 'light', 'dark', 'contrast-light', 'contrast-dark'], size: ['100', '125', '150', '200'],
    spacing: ['standard', 'relaxed', 'wide'], explanation: ['technical', 'plain']};
  let preferences = {...defaults};
  let storageUnavailable = false;
  try {
    const saved = JSON.parse(localStorage.getItem(key));
    for (const name of Object.keys(defaults)) {
      if (choices[name].includes(saved?.[name])) preferences[name] = saved[name];
    }
  } catch { /* Invalid or unavailable storage must not prevent reading. */ }

  function apply() {
    const root = document.documentElement;
    root.dataset.theme = preferences.theme;
    root.dataset.readingSize = preferences.size;
    root.dataset.readingSpacing = preferences.spacing;
    const explanationChanged = root.dataset.readingExplanation !== preferences.explanation;
    root.dataset.readingExplanation = preferences.explanation;
    if (explanationChanged) document.dispatchEvent(new Event('reading-preferences-change'));
  }
  apply();

  document.addEventListener('DOMContentLoaded', () => {
    const status = document.querySelector('#reading-storage-status');
    function persist(reset = false) {
      try {
        if (reset) localStorage.removeItem(key);
        else localStorage.setItem(key, JSON.stringify(preferences));
        storageUnavailable = false;
      } catch { storageUnavailable = true; }
      status.textContent = storageUnavailable
        ? 'Preferences apply for this page. Browser storage is unavailable.' : '';
    }
    function sync() {
      for (const name of Object.keys(defaults)) {
        document.querySelector(`#reading-${name}`).value = preferences[name];
      }
      apply();
    }
    for (const name of Object.keys(defaults)) {
      document.querySelector(`#reading-${name}`).addEventListener('change', event => {
        if (!choices[name].includes(event.target.value)) return;
        preferences[name] = event.target.value;
        apply();
        persist();
      });
    }
    document.querySelector('#reading-reset').addEventListener('click', () => {
      preferences = {...defaults};
      sync();
      persist(true);
    });
    sync();
    // Keep a usable reading pane when enlarged controls exhaust desktop height.
    // Measure controls, not the pane, so changing layout cannot oscillate.
    const header = document.querySelector('.masthead');
    const composer = document.querySelector('.composer-area');
    const tools = document.querySelector('#conversation-tools');
    const reflow = () => {
      const controls = [header, composer, tools].reduce((height, node) =>
        height + (node?.getBoundingClientRect().height || 0), 0);
      const minimumReadingHeight = 12 * parseFloat(getComputedStyle(document.documentElement).fontSize) + 56;
      document.body.classList.toggle('reading-document-flow', controls + minimumReadingHeight > innerHeight);
    };
    const observer = new ResizeObserver(reflow);
    [header, composer, tools].filter(Boolean).forEach(node => observer.observe(node));
    window.addEventListener('resize', reflow);
    reflow();
  });
})();
