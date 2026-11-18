/* Applied before first paint. Same storage key and data attributes as ui/reading-preferences.js. */
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
    document.dispatchEvent(new Event('reading-preferences-applied'));
  }
  function persist(reset) {
    try {
      if (reset) localStorage.removeItem(key);
      else localStorage.setItem(key, JSON.stringify(preferences));
      storageUnavailable = false;
    } catch { storageUnavailable = true; }
  }
  apply();
  window.ReadingPrefs = {
    choices,
    get: name => preferences[name],
    set(name, value) {
      if (!choices[name]?.includes(value)) return;
      preferences[name] = value; apply(); persist(false);
    },
    reset() { preferences = {...defaults}; apply(); persist(true); },
    storageUnavailable: () => storageUnavailable,
  };
})();
