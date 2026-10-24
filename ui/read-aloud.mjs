/* Optional supplementary audio. Never loaded by the research app until #137/#138 integration. */
const owners = new WeakMap();
let panelNumber = 0;
const active = state => ['starting', 'playing', 'paused'].includes(state);

export function speechChunks(text, size = 200) {
  const chars = Array.from(text.trim());
  const chunks = [];
  while (chars.length) {
    let end = Math.min(size, chars.length);
    if (end < chars.length) {
      const space = chars.slice(0, end).join('').lastIndexOf(' ');
      if (space > size / 2) end = Array.from(chars.slice(0, end).join('').slice(0, space)).length;
    }
    chunks.push(chars.splice(0, end).join('').trim());
  }
  return chunks.filter(Boolean);
}

export class ReadAloud {
  constructor({synth = globalThis.speechSynthesis, Utterance = globalThis.SpeechSynthesisUtterance,
    onChange = () => {}, startTimeout = 10000} = {}) {
    Object.assign(this, {synth, Utterance, onChange, startTimeout});
    this.state = 'idle';
    this.message = 'Ready. Choose text, then press Play.';
    this.items = [];
    this.selected = '';
    this.rate = 1;
    this.token = 0;
    this.voices = [];
    this.refreshVoices = () => {
      try { this.voices = this.supported ? this.synth.getVoices().filter(v => v.localService === true) : []; }
      catch { this.voices = []; }
      if (active(this.state) && !this.voices.some(v => v === this.voice || v.voiceURI === this.voice?.voiceURI)) {
        this.stop('Local voice became unavailable. Text remains available.');
      }
      this.emit();
    };
    this.synth?.addEventListener?.('voiceschanged', this.refreshVoices);
    this.refreshVoices();
  }
  get supported() {
    return !!(this.synth && this.Utterance && ['speak', 'cancel', 'pause', 'resume', 'getVoices']
      .every(method => typeof this.synth[method] === 'function'));
  }
  emit() { this.onChange(this); }
  setItems(items) {
    const old = this.items.find(item => item.id === this.selected);
    this.items = items.filter(item => item.id && item.label && item.text?.trim()).map(item => ({...item}));
    const current = this.items.find(item => item.id === this.selected);
    if (old && (!current || old.text !== current.text || old.label !== current.label)) {
      this.stop('Stopped: selected text changed or was removed.');
    }
    if (!current) this.selected = this.items[0]?.id || '';
    this.emit();
  }
  select(id) {
    if (id === this.selected || !this.items.some(item => item.id === id)) return;
    this.stop('Stopped: selected text changed. Press Play to read the new selection.');
    this.selected = id;
    this.emit();
  }
  setRate(rate) {
    if (![0.75, 1, 1.25, 1.5, 2].includes(Number(rate))) return;
    if (active(this.state)) this.stop('Stopped: speed changed. Press Play to restart.');
    this.rate = Number(rate);
    this.emit();
  }
  stop(message = 'Stopped.') {
    ++this.token;
    clearTimeout(this.timer);
    this.pendingNext = null;
    const owned = this.synth && owners.get(this.synth) === this;
    // Invalidate callbacks before cancel(), which may synchronously fire onerror.
    if (owned) {
      owners.delete(this.synth);
      try { this.synth.cancel(); } catch { message = 'Speech could not be stopped by the browser. Use browser or system audio controls.'; }
    }
    this.utterance = null;
    this.state = 'idle';
    this.message = message;
    this.emit();
  }
  fail(message) {
    this.stop(message);
    this.state = 'error';
    this.emit();
  }
  play() {
    if (this.destroyed || active(this.state)) return;
    this.refreshVoices();
    const item = this.items.find(item => item.id === this.selected);
    if (!this.supported) return this.fail('Read-aloud is unavailable in this browser. Text remains available.');
    if (!this.voices.length) return this.fail('No local speech voice is available. Text remains available.');
    if (!item) return this.fail('No text selected. Text remains available.');
    const previous = owners.get(this.synth);
    previous?.stop('Stopped: another read-aloud selection started.');
    const token = ++this.token;
    owners.set(this.synth, this);
    this.voice = this.voices[0];
    const chunks = speechChunks(item.text);
    let index = 0;
    const next = () => {
      if (token !== this.token) return;
      if (index === chunks.length) {
        owners.delete(this.synth);
        this.utterance = null;
        this.state = 'idle';
        this.message = 'Finished.';
        this.emit();
        return;
      }
      try {
        const utterance = new this.Utterance(chunks[index++]);
        this.utterance = utterance; // Keep a strong reference until completion.
        utterance.voice = this.voice;
        utterance.lang = this.voice.lang;
        utterance.rate = this.rate;
        utterance.onstart = () => {
          if (token !== this.token || this.utterance !== utterance) return;
          clearTimeout(this.timer);
          utterance.started = true;
          if (this.state === 'paused') return;
          this.state = 'playing';
          this.message = `Reading: ${item.label}`;
          this.emit();
        };
        utterance.onend = () => {
          if (token !== this.token || this.utterance !== utterance) return;
          clearTimeout(this.timer);
          this.utterance = null;
          if (this.state === 'paused') {
            this.pendingNext = next;
            return;
          }
          next();
        };
        utterance.onerror = () => {
          if (token === this.token && this.utterance === utterance) this.fail('Speech playback failed. Text remains available. Try Play again or use your screen reader.');
        };
        this.state = 'starting';
        this.message = `Starting: ${item.label}`;
        this.emit();
        this.timer = setTimeout(() => {
          if (token === this.token) this.fail('Speech did not start. Text remains available. Try Play again.');
        }, this.startTimeout);
        this.synth.cancel(); // Clear the document speech queue; never enqueue overlapping utterances.
        this.synth.resume(); // Some engines retain a paused flag after cancellation.
        this.synth.speak(utterance);
      } catch { this.fail('Speech playback failed. Text remains available.'); }
    };
    next();
  }
  pause() {
    if (!['starting', 'playing'].includes(this.state)) return;
    try {
      this.synth.pause();
      clearTimeout(this.timer);
      this.state = 'paused';
      this.message = 'Paused.';
      this.emit();
    } catch { this.fail('Speech could not pause. Playback stopped.'); }
  }
  resume() {
    if (this.state !== 'paused') return;
    if (this.pendingNext) {
      const next = this.pendingNext;
      this.pendingNext = null;
      next();
      return;
    }
    try {
      this.synth.resume();
      if (!this.utterance?.started) {
        this.timer = setTimeout(() => this.fail('Speech did not start. Text remains available.'), this.startTimeout);
      }
      this.state = 'playing';
      this.message = `Reading: ${this.items.find(item => item.id === this.selected)?.label || 'selected text'}`;
      this.emit();
    } catch { this.fail('Speech could not resume. Playback stopped.'); }
  }
  destroy() {
    this.stop();
    this.destroyed = true;
    this.synth?.removeEventListener?.('voiceschanged', this.refreshVoices);
  }
}

/** Caller supplies exact plain text, including provenance/limitations. Updates never start speech. */
export function mountReadAloud(root, options = {}) {
  const doc = root.ownerDocument;
  const make = (tag, text) => {
    const node = doc.createElement(tag);
    if (text) node.textContent = text;
    return node;
  };
  const group = make('fieldset');
  group.className = 'read-aloud';
  group.append(make('legend', 'Optional read-aloud'));
  const note = make('p', 'Audio is optional. Only browser-advertised local voices are used. Text and citations remain available.');
  const prefix = `read-aloud-${++panelNumber}`;
  const label = make('label', 'Read');
  const choice = make('select');
  choice.id = `${prefix}-text`;
  label.htmlFor = choice.id;
  const speedLabel = make('label', 'Speed');
  const speed = make('select');
  speed.id = `${prefix}-speed`;
  speedLabel.htmlFor = speed.id;
  for (const value of [0.75, 1, 1.25, 1.5, 2]) {
    const option = make('option', `${value}×`);
    option.value = String(value);
    option.selected = value === 1;
    speed.append(option);
  }
  const controls = make('div');
  controls.className = 'read-aloud-controls';
  const play = make('button', 'Play');
  const pause = make('button', 'Pause');
  const stop = make('button', 'Stop');
  for (const button of [play, pause, stop]) button.type = 'button';
  const status = make('p');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'off');
  status.setAttribute('aria-atomic', 'true');
  // Do not announce speech start/completion over the optional audio. Announce short
  // user-requested pause/stop/error states only, never the selected passage itself.
  const controller = new ReadAloud({...options, onChange(reader) {
    const signature = JSON.stringify(reader.items.map(({id, label}) => [id, label]));
    if (choice.dataset.items !== signature) {
      choice.replaceChildren(...reader.items.map(item => {
        const option = make('option', item.label);
        option.value = item.id;
        return option;
      }));
      choice.dataset.items = signature;
    }
    choice.value = reader.selected;
    choice.disabled = !reader.items.length;
    speed.value = String(reader.rate);
    play.disabled = active(reader.state) || !reader.supported || !reader.voices.length || !reader.items.length;
    pause.textContent = reader.state === 'paused' ? 'Resume' : 'Pause';
    // Keep the focused Pause/Resume button enabled when changing its label.
    pause.disabled = !active(reader.state);
    stop.disabled = !active(reader.state);
    status.setAttribute('aria-live', active(reader.state) && reader.state !== 'paused' ? 'off' : 'polite');
    const message = !reader.supported ? 'Read-aloud unavailable in this browser. Text remains available.' :
      !reader.voices.length ? 'No local voice available. You can still read all text and citations.' : reader.message;
    if (status.textContent !== message) status.textContent = message;
    options.onChange?.(reader);
  }});
  play.addEventListener('click', () => controller.play());
  pause.addEventListener('click', () => controller.state === 'paused' ? controller.resume() : controller.pause());
  stop.addEventListener('click', () => controller.stop());
  choice.addEventListener('change', () => controller.select(choice.value));
  speed.addEventListener('change', () => controller.setRate(speed.value));
  controls.append(play, pause, stop);
  group.append(note, label, choice, speedLabel, speed, controls, status);
  root.append(group);
  const onHide = () => controller.stop('Stopped: page hidden.');
  doc.defaultView.addEventListener('pagehide', onHide);
  const visibility = () => { if (doc.hidden) onHide(); };
  doc.addEventListener('visibilitychange', visibility);
  const observer = new doc.defaultView.MutationObserver(() => {
    if (!root.isConnected) destroy();
  });
  observer.observe(doc.documentElement, {childList: true, subtree: true});
  function destroy() {
    observer.disconnect();
    doc.defaultView.removeEventListener('pagehide', onHide);
    doc.removeEventListener('visibilitychange', visibility);
    controller.destroy();
    group.remove();
  }
  return {setItems: items => controller.setItems(items), stop: () => controller.stop(), destroy};
}
