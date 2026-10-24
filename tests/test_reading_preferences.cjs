/* Dependency-free behavior checks: node --test tests/test_reading_preferences.cjs */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(`${__dirname}/../ui/reading-preferences.js`, 'utf8');

function boot(saved, failure) {
  const nodes = {};
  const values = new Map(saved === undefined ? [] : [['1f.reading-preferences.v1', saved]]);
  const storage = {
    getItem: key => { if (failure === 'read') throw Error('Blocked'); return values.get(key) ?? null; },
    setItem: (key, value) => { if (failure) throw Error('Quota'); values.set(key, value); },
    removeItem: key => { if (failure) throw Error('Blocked'); values.delete(key); },
  };
  const document = {documentElement: {dataset: {}},
    querySelector: id => nodes[id] ||= {addEventListener(type, callback) { this[type] = callback; }},
    addEventListener(type, callback) { this[type] = callback; }};
  vm.runInNewContext(source, {document, localStorage: storage});
  document.DOMContentLoaded();
  return {nodes, values, root: document.documentElement.dataset,
    change(name, value) { nodes[`#reading-${name}`].change({target: {value}}); },
    reset() { nodes['#reading-reset'].click(); }};
}

test('first visit follows system; independent preferences persist and reset removes only own key', () => {
  const app = boot();
  assert.equal(app.root.theme, 'system');
  app.values.set('other.feature', 'keep');
  app.change('theme', 'dark'); app.change('size', '200'); app.change('spacing', 'wide');
  const saved = app.values.get('1f.reading-preferences.v1');
  assert.deepEqual(JSON.parse(saved), {theme: 'dark', size: '200', spacing: 'wide'});
  assert.equal(boot(saved).root.readingSize, '200');
  app.reset();
  assert.equal(app.root.theme, 'system');
  assert.equal(app.root.readingSize, '100');
  assert.equal(app.root.readingSpacing, 'standard');
  assert.equal(app.values.has('1f.reading-preferences.v1'), false);
  assert.equal(app.values.get('other.feature'), 'keep');
});

test('malformed, wrong-type and out-of-range saved values keep usable defaults', () => {
  for (const value of ['{', 'null', '[]', 'true', '42', '"text"',
    '{"theme":"unknown","size":"9000","spacing":"invalid"}']) {
    const app = boot(value);
    assert.equal(app.root.theme, 'system');
    assert.equal(app.root.readingSize, '100');
    assert.equal(app.root.readingSpacing, 'standard');
  }
  const app = boot('{"theme":"dark","size":"invalid","extra":"ignored"}');
  assert.equal(app.root.theme, 'dark'); assert.equal(app.root.readingSize, '100');
});

test('blocked reads and failed writes/removals leave changes and reset usable in memory', () => {
  for (const failure of ['read', 'write']) {
    const app = boot(undefined, failure);
    app.change('size', '200'); assert.equal(app.root.readingSize, '200');
    assert.match(app.nodes['#reading-storage-status'].textContent, /storage is unavailable/);
    app.change('theme', 'dark'); assert.equal(app.root.theme, 'dark');
    app.reset(); assert.equal(app.root.theme, 'system'); assert.equal(app.root.readingSize, '100');
  }
});
