/* Execute the shipped presentation functions with a minimal DOM boundary.
 * No browser or real regulatory-provider behavior is claimed here. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('ui/app.js', 'utf8');
const extract = name => source.slice(source.indexOf('function ' + name + '(')).match(/^[\s\S]*?^}/m)[0];
test('regulatory outage retains business output in announcement and visible explanation', () => {
  const demo = {mode: 'indexed', scenario: 'partial', error: {stage: 'regulatory'}, result: {}};
  const paragraphs = [];
  const stop = new Error('render boundary');
  const context = {demo, BriefLibrary: {reviewText: () => 'Pending'},
    isReal: () => true, isSynthesis: () => true,
    STATES: {partial: ['Partial draft', 'No recommendation is shown.']},
    element: (tag, text) => { if (tag === 'p') paragraphs.push(text); return {append() {}}; },
    answerHeading() {}, renderDraft() { throw stop; }, stop,
    answer: {replaceChildren() {}, append() {}}};
  vm.createContext(context);
  vm.runInContext(extract('readyAnnouncement', '\nfunction rememberAcceptedTurn'), context);
  assert.match(context.readyAnnouncement(demo, 1), /business implications retained/);
  assert.doesNotMatch(context.readyAnnouncement(demo, 1), /no business recommendation/);
  vm.runInContext(extract('renderDemo', '\nfunction offerRetry'), context);
  assert.throws(() => context.renderDemo(demo, 1, context.answer), error => error === stop);
  assert.ok(paragraphs.some(text => /business implications are available.*assessment failed/.test(text)));
});
