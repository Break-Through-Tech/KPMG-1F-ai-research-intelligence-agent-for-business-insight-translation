import test from 'node:test';
import assert from 'node:assert/strict';
import {ReadAloud, speechChunks} from '../../ui/read-aloud.mjs';

const items = [{id: 'answer', label: 'Draft answer · Not approved', text: 'Finding. Citation 1. Limitations: fixture only.'},
  {id: 'source', label: 'Source passage 1 · Page 2', text: 'A source quotation.'}];
function setup(overrides = {}) {
  const voice = {voiceURI: 'local', localService: true, lang: 'en-US'};
  const synth = {
    voices: [voice], spoken: [], canceled: 0, pauses: 0, resumes: 0, listeners: new Set(),
    getVoices() { return this.voices; },
    speak(u) { this.spoken.push(u); },
    cancel() { this.canceled++; }, pause() { this.pauses++; }, resume() { this.resumes++; },
    addEventListener(_, fn) { this.listeners.add(fn); }, removeEventListener(_, fn) { this.listeners.delete(fn); },
    ...overrides,
  };
  class Utterance { constructor(text) { this.text = text; } }
  const reader = new ReadAloud({synth, Utterance});
  reader.setItems(items);
  return {synth, reader, Utterance};
}

test('mount/update/select/rate/voice refresh never initiate speech', () => {
  const {reader, synth} = setup();
  reader.select('source'); reader.setRate(1.5); reader.refreshVoices();
  reader.setItems([...items]); reader.pause(); reader.resume();
  assert.equal(synth.spoken.length, 0);
  reader.destroy();
});
test('explicit Play uses exact selected plain text, a local voice and chosen speed', () => {
  const {reader, synth} = setup();
  reader.select('source'); reader.setRate(1.25); reader.play();
  const u = synth.spoken[0];
  assert.equal(u.text, items[1].text); assert.equal(u.rate, 1.25); assert.equal(u.voice.localService, true);
  u.onstart(); assert.equal(reader.state, 'playing');
  reader.pause(); assert.equal(reader.state, 'paused');
  reader.resume(); assert.equal(reader.state, 'playing');
  u.onend(); assert.equal(reader.message, 'Finished.');
  reader.destroy();
});
test('repeated Play cannot queue overlap; another reader cancels owner', () => {
  const {reader, synth, Utterance} = setup();
  reader.play(); reader.play(); assert.equal(synth.spoken.length, 1);
  const old = synth.spoken[0];
  const second = new ReadAloud({synth, Utterance}); second.setItems(items); second.play();
  assert.equal(reader.state, 'idle'); assert.equal(synth.spoken.length, 2);
  old.onstart(); old.onerror(); old.onend();
  assert.equal(reader.state, 'idle'); assert.equal(second.state, 'starting');
  reader.destroy(); second.destroy();
});
test('changing/removing selected content and selection stops; unrelated changes do not', () => {
  const {reader, synth} = setup(); reader.play();
  reader.setItems([items[0], {...items[1], text: 'Changed unselected passage'}]);
  assert.equal(reader.state, 'starting');
  reader.setItems([{...items[0], text: 'Revised draft'}, items[1]]);
  assert.equal(reader.state, 'idle'); assert.match(reader.message, /changed/);
  reader.play(); reader.select('source'); assert.equal(reader.state, 'idle');
  reader.play(); reader.setItems([]); assert.equal(reader.state, 'idle');
  assert.equal(reader.selected, ''); assert.equal(synth.spoken.length, 3);
  reader.destroy();
});
test('stop invalidates synchronous cancel errors and late callbacks', () => {
  const {reader, synth} = setup(); reader.play(); const u = synth.spoken[0];
  synth.cancel = () => u.onerror();
  reader.stop(); u.onend(); u.onstart();
  assert.equal(reader.state, 'idle'); assert.equal(reader.message, 'Stopped.');
  reader.destroy();
});
test('long passages progress one chunk at a time, retaining all characters', () => {
  const {reader, synth} = setup();
  const text = '😀 evidence citation and limitations. '.repeat(40).trim();
  reader.setItems([{id: 'long', label: 'Long source', text}]); reader.play();
  const first = synth.spoken[0]; first.onstart(); first.onend();
  const count = synth.spoken.length; first.onend(); first.onerror();
  assert.equal(synth.spoken.length, count); // obsolete chunk cannot advance/fail current playback
  assert.equal(reader.state, 'starting');
  while (reader.state !== 'idle') { const u = synth.spoken.at(-1); u.onstart(); u.onend(); }
  assert.equal(synth.spoken.map(u => u.text).join(' '), text);
  assert.ok(speechChunks(text).every(chunk => Array.from(chunk).length <= 200));
  reader.destroy();
});
test('paused chunk handoff waits for explicit Resume and deferred speech is cancellable', () => {
  for (const cancel of ['stop', 'replace', 'destroy']) {
    const {reader, synth} = setup();
    reader.setItems([{id: 'long', label: 'Long source', text: 'Evidence. '.repeat(60)}]);
    reader.play(); const first = synth.spoken[0]; first.onstart(); reader.pause();
    const resumes = synth.resumes;
    first.onend(); first.onend(); first.onstart();
    assert.equal(reader.state, 'paused');
    assert.equal(synth.spoken.length, 1);
    assert.equal(synth.resumes, resumes);
    reader.resume();
    assert.equal(synth.spoken.length, 2);
    assert.equal(synth.resumes, resumes + 1);
    while (reader.state !== 'idle') {
      const u = synth.spoken.at(-1); u.onstart(); u.onend();
    }
    assert.equal(reader.message, 'Finished.');
    reader.play(); const u = synth.spoken.at(-1); u.onstart(); reader.pause(); u.onend();
    const count = synth.spoken.length;
    if (cancel === 'replace') reader.setItems([]);
    else reader[cancel]();
    reader.resume(); u.onend();
    assert.equal(synth.spoken.length, count);
    reader.destroy();
  }
});
test('unsupported engine, empty voices, remote-only voices and thrown playback fail gracefully', () => {
  const unsupported = new ReadAloud({synth: {}, Utterance: null}); unsupported.setItems(items); unsupported.play();
  assert.equal(unsupported.state, 'error'); unsupported.destroy();
  for (const voices of [[], [{localService: false}]]) {
    const {reader, synth} = setup({voices}); reader.play();
    assert.equal(reader.state, 'error'); assert.equal(synth.spoken.length, 0); reader.destroy();
  }
  const {reader} = setup({speak() { throw Error('engine'); }}); reader.play();
  assert.equal(reader.state, 'error'); assert.match(reader.message, /Text remains/); reader.destroy();
});
test('voices can arrive late; losing voice stops active playback', () => {
  const {reader, synth} = setup({voices: []});
  assert.equal(reader.voices.length, 0);
  synth.voices = [{localService: true, voiceURI: 'late'}]; reader.refreshVoices();
  assert.equal(synth.spoken.length, 0); reader.play();
  synth.voices = []; reader.refreshVoices(); assert.equal(reader.state, 'idle'); reader.destroy();
});
test('error callbacks, startup timeout and paused startup timeout recover', async () => {
  const {reader, synth} = setup(); reader.startTimeout = 5;
  reader.play(); synth.spoken[0].onerror(); assert.equal(reader.state, 'error');
  reader.play(); await new Promise(resolve => setTimeout(resolve, 15)); assert.equal(reader.state, 'error');
  reader.play(); reader.pause(); await new Promise(resolve => setTimeout(resolve, 15));
  assert.equal(reader.state, 'paused'); reader.resume();
  await new Promise(resolve => setTimeout(resolve, 15)); assert.equal(reader.state, 'error');
  reader.destroy(); assert.equal(synth.listeners.size, 0);
});
test('speed changes stop without restarting; destroyed readers cannot play', () => {
  const {reader, synth} = setup(); reader.play(); reader.setRate(2);
  assert.equal(reader.state, 'idle'); assert.equal(synth.spoken.length, 1);
  reader.destroy(); reader.play(); assert.equal(synth.spoken.length, 1);
});
