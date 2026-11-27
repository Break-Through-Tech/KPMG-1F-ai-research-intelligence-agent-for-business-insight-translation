"""Offline validation of consolidated-v2 (ported from v1; changes marked "v2:"). 0 model calls.

Three kinds of evidence, labelled in each test name:
  replay_*     saved combined-v1 artefacts (real model drafts, real evidence) run through the new deterministic code;
               any review decision a replay needs is SIMULATED and says so.
  sim_*        simulated provider replies (scripted JSON) through the real engine, checkpoints and budgets.
  unit_*       deterministic components on constructed inputs.
None of this measures live model behaviour. The combined-v1 questions are used only as regression cases for the
documented failures, never as validation of answer quality.

    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -m unittest test_consolidated   (from this folder)
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import env  # noqa: F401  (path setup)
import evidence as ev
import publication
import review as rv
import synthesis as syn
from engine import ConsolidatedResearch, CheckpointStore

DATA = env.ROOT / 'data/processed'
B1 = DATA / 'combined-v1-baseline-skipfit6k'
M1 = DATA / 'combined-v1-multiagent-skipfit6k-v2'
V2, GATE = env.load_v2(), env.load_gate()
ROWS = env.bundle_rows()
TABLES = ev.TableIndex(ROWS)
BY_ID = {r['chunk_id']: r for r in ROWS}


def count(passage):
    return max(1, round(len(passage['text'].split()) * 1.3))


def clean(claim):
    return {'text': claim['text'], 'kind': claim.get('kind', 'finding'), 'support': deepcopy(claim['support']),
            'chunk_ids': list(dict.fromkeys(s['chunk_id'] for s in claim['support']))}


def saved(folder, qid):
    return json.loads((folder / qid / 'result.json').read_text(encoding='utf-8'))['envelope']['result']


def decision(index, *, entail=True, supported=True, relevant=True, text='', added=(), resolutions=(),
             reduced_entailed=None, related=False):
    # v2: the reviewer must confirm a reduction (reduced_entailed) and may mark a same-study variant (related).
    return {'index': index, 'supported': supported, 'relevant': relevant, 'quotes_entail': entail,
            'reason': 'SIMULATED review decision', 'supported_text': text, 'added_support': list(added),
            'flag_resolutions': list(resolutions),
            'reduced_entailed': bool(text) if reduced_entailed is None else reduced_entailed, 'related': related}


def review_of(decisions, coverage='full', gap='', limitations=()):
    return {'coverage': coverage, 'gap': gap, 'decisions': {d['index']: d for d in decisions},
            'limitations': list(limitations)}


def publish(claims, passages, decisions, **kw):
    summary = {'status': 'ok', 'claims': claims, 'limitation_support': [], 'limitations': []}
    return publication.publish(summary, review_of(decisions, **kw), passages, [], v2=V2, gate=GATE)


# ------------------------------------------------------------------ fake provider for the engine
class Provider:
    """Scripted replies by stage. Each value is a JSON-able object, a raw string, or an exception to raise."""
    supports_response_schema = True

    def __init__(self, plan=None, synthesis=None, review=None):
        self.replies = {'plan': plan, 'synthesis': synthesis, 'review': review}
        self.calls = []

    def __call__(self, prompt, *, response_schema=None):
        stage = ('synthesis' if prompt.startswith(syn.PROMPT_HEAD) else 'review'
                 if prompt.startswith('ANSWER QUALITY REVIEW') else 'plan')
        self.calls.append(stage)
        reply = self.replies[stage]
        if isinstance(reply, list):
            reply = reply.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if callable(reply):
            reply = reply(prompt)
        return reply if isinstance(reply, str) else json.dumps(reply)


def passage(cid, text, **extra):
    return {'chunk_id': cid, 'text': text, 'arxiv_id': cid.split('_')[0], 'title': 'Paper ' + cid.split('_')[0],
            'source_url': 'https://arxiv.org/abs/' + cid.split('_')[0], **extra}


P1 = passage('1111.00001v1_c0001', 'Model A reached 71.5% accuracy on the benchmark test set. Model B reached 64.0% '
                                     'accuracy on the same test set.')
P2 = passage('1111.00001v1_c0002', 'The authors note that the evaluation used only English questions and was not '
                                     'tested in deployment.')
P3 = passage('2222.00002v1_c0003', 'A second study found latency of 120 ms per query on a single GPU.')


def ranked_from(mapping, default):
    def ranked(query, n):
        return [deepcopy(p) for p in mapping.get(query, default)][:n]
    return ranked


GOOD_SYNTHESIS = {'status': 'ok', 'claims': [
    {'text': 'Model A reached 71.5% accuracy on the benchmark test set.', 'kind': 'finding',
     'support': [{'chunk_id': P1['chunk_id'], 'quote': 'Model A reached 71.5% accuracy on the benchmark test set.'}]},
    {'text': 'Model B reached 64.0% accuracy on the same test set.', 'kind': 'finding',
     'support': [{'chunk_id': P1['chunk_id'], 'quote': 'Model B reached 64.0% accuracy on the same test set.'}]}],
    'limitations': [{'text': 'Only English questions were evaluated.', 'support': [
        {'chunk_id': P2['chunk_id'], 'quote': 'the evaluation used only English questions'}]}]}
GOOD_REVIEW = {'coverage': 'full', 'gap': '', 'limitations': GOOD_SYNTHESIS['limitations'],
               'decisions': [decision(0), decision(1)]}
PLAN = {'question_type': 'multi_part', 'subquestions': [{'query': 'latency per query', 'purpose': 'speed'}],
        'business': {'delegate': False, 'industry_in_question': '', 'reason': 'none'},
        'chart': {'delegate': False, 'reason': 'none'}, 'notes': ''}


class EvidenceTests(unittest.TestCase):
    def test_unit_standard_packet_is_bounded_ordered_and_keeps_metadata(self):
        ranked = ranked_from({}, [P1, P2, P3])
        packet = ev.standard_packet('q', ranked, count, TABLES, budget=60)
        self.assertLessEqual(packet['tokens'], 60)
        self.assertEqual([p['chunk_id'] for p in packet['passages']], packet['protected_ids'])
        self.assertEqual(packet['passages'][0]['source_url'], P1['source_url'])

    def test_replay_table_pair_completed_from_bundle(self):
        # combined-v1 G07.2/G07.3: one row of a FinStat2SQL table pair was retrieved without its sibling.
        row = BY_ID['2506.23273v2_table_d472857c5172bfd0_1']
        packet = ev.standard_packet('q', ranked_from({}, [row]), count, TABLES)
        ids = {p['chunk_id'] for p in packet['passages']}
        self.assertIn('2506.23273v2_table_d472857c5172bfd0_4', ids)
        self.assertEqual(packet['notes'], [])

    def test_unit_table_too_large_for_budget_is_marked_incomplete(self):
        row = BY_ID['2506.23273v2_table_d472857c5172bfd0_1']
        packet = ev.standard_packet('q', ranked_from({}, [row]), count, TABLES, budget=count(row))
        self.assertEqual([p['chunk_id'] for p in packet['passages']], [row['chunk_id']])
        self.assertEqual(packet['notes'][0]['kind'], 'incomplete_table')
        self.assertIn('may be incomplete', packet['notes'][0]['text'])

    def test_unit_deep_packet_protects_original_and_dedupes(self):
        big = passage('3333.00003v1_c0009', 'word ' * 400)
        ranked = ranked_from({'q': [P1, P2], 'sub one': [P2, big, P3], 'sub two': [P3]}, [])
        packet = ev.deep_packet('q', [{'query': 'sub one', 'purpose': 'x'}, {'query': 'sub two', 'purpose': 'y'}],
                                ranked, count, TABLES, budget=200)
        ids = [p['chunk_id'] for p in packet['passages']]
        self.assertEqual(ids[:2], [P1['chunk_id'], P2['chunk_id']])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn(P3['chunk_id'], ids)
        self.assertNotIn(big['chunk_id'], ids)  # does not fit; skipped, nothing displaced
        self.assertLessEqual(packet['tokens'], 200)

    def test_unit_deep_packet_trimmed_to_request_guard_estimate(self):
        # v2: compact serialization drops unknown fields, so the filler bulk sits in a field that is sent.
        filler = [passage(f'4444.0000{i}v1_c000{i}', 'evidence ' * 30, paragraph_heading='x' * 30000) for i in range(6)]
        ranked = ranked_from({'q': [P1, P2], 'sub': filler}, [])
        packet = ev.deep_packet('q', [{'query': 'sub', 'purpose': 'x'}], ranked, count, TABLES)
        self.assertLessEqual(ev.serialized_estimate(packet['passages']), ev.DEEP_EVIDENCE_EST)
        self.assertTrue(packet['trimmed_for_request_size'])
        self.assertEqual([p['chunk_id'] for p in packet['passages'][:2]], [P1['chunk_id'], P2['chunk_id']])

    def test_unit_failed_supplementary_search_is_recorded_not_fatal(self):
        def ranked(query, n):
            if query == 'bad':
                raise ValueError('Query would truncate')
            return [deepcopy(P1)]
        packet = ev.deep_packet('q', [{'query': 'bad', 'purpose': 'x'}], ranked, count, TABLES)
        self.assertIn('ValueError', packet['searches'][1]['error'])
        self.assertEqual([p['chunk_id'] for p in packet['passages']], [P1['chunk_id']])


class SynthesisContractTests(unittest.TestCase):
    def test_replay_g10_status_contract_failure_recovers_validated_claims(self):
        # combined-v1 M1 G10: status 'insufficient_evidence' with claims -> whole answer discarded.
        raw = json.loads((M1 / 'G10' / '2-synthesis.reply.json').read_text(encoding='utf-8'))['provider_text']
        passages = json.loads((M1 / 'G10' / '2-synthesis.evidence.json').read_text(encoding='utf-8'))
        self.assertEqual(json.loads(raw)['status'], 'insufficient_evidence')
        summary, report = syn.parse(raw, passages)
        self.assertEqual(summary['status'], 'ok')
        self.assertTrue(summary['claims'])
        self.assertTrue(report['contract_repairs'])
        # SIMULATED review accepting every claim: publication still applies every deterministic gate.
        out = publish(summary['claims'], passages, [decision(i) for i in range(len(summary['claims']))])
        self.assertEqual(out['status'], 'ok')
        for claim in out['claims']:
            self.assertFalse(publication.number_recall(claim, ' '.join(BY_ID[c]['text'] for c in claim['chunk_ids'])))

    def test_unit_one_bad_quote_drops_only_that_claim(self):
        reply = deepcopy(GOOD_SYNTHESIS)
        reply['claims'][1]['support'][0]['quote'] = 'Model B reached 99.9% accuracy on the same test set.'
        summary, report = syn.parse(json.dumps(reply), [P1, P2])
        self.assertEqual([c['text'] for c in summary['claims']], [reply['claims'][0]['text']])
        self.assertEqual(report['dropped'][0]['reason'], 'quote not found verbatim in its cited passage')

    def test_unit_duplicate_json_keys_fail_closed(self):
        with self.assertRaises(ValueError):
            syn.parse('{"status": "ok", "status": "ok", "claims": [], "limitations": []}', [P1])

    def test_unit_prompt_states_attached_quote_rule_and_notes(self):
        prompt = syn.build_prompt('q', [P1], [{'text': 'Only 1 of 2 rows of Table 4 are in the evidence.'}])
        self.assertIn("must be stated in that claim's OWN attached quotes", prompt)
        self.assertIn('Only 1 of 2 rows of Table 4', prompt)


class CitationGroundingTests(unittest.TestCase):
    def setUp(self):
        result = saved(B1, 'G03')
        self.passages = result['evidence']
        self.claim = clean(result['summary']['claims'][2])  # the Table 7 claim Codex scored as G03-B F2

    def test_replay_g03_b_f2_extra_figures_withheld(self):
        # SIMULATED review that (like the original) accepts it: P4 withholds it, 59.4/59.5/78.0/81.4 are not quoted.
        out = publish([self.claim], self.passages, [decision(0)])
        self.assertEqual(out['claims'], [])
        self.assertTrue(out['held_claims'][0]['reasons'][0].startswith('P4'))
        for figure in ('59.4', '59.5', '78.0', '81.4'):
            self.assertIn(figure, out['held_claims'][0]['reasons'][0])

    def test_replay_g03_b_f2_published_once_rows_are_attached(self):
        # SIMULATED reviewer attaches the 3-shot and 4-shot Table 7 rows (already in B1's evidence) as added_support.
        added, res = [], []
        for n in (2, 3):
            text = syn.norm(BY_ID[f'2505.15753v1_table_1cb85a8157eb0710_{n}']['text'])
            span = text[text.index('SCR ('):]  # must include the '(3 shot)' / '(4 shot)' labels too
            added.append({'chunk_id': f'2505.15753v1_table_1cb85a8157eb0710_{n}', 'quote': span})
        quotes = [syn.norm(s['quote']) for s in self.claim['support']] + [a['quote'] for a in added]
        for raw, _value in publication.reported_numbers(self.claim['text'], ''):
            span = next(q for q in quotes if raw in q)
            res.append({'number': raw, 'quote': span, 'reason': 'SIMULATED'})
        out = publish([self.claim], self.passages, [decision(0, added=added, resolutions=res)])
        # Number recall (P4) is now satisfied, but the bundled 14-figure paragraph ('59.3/59.4/59.5 ... 2/3/4')
        # still carries attribution flags the simulated spans do not clear: it stays withheld. Atomic claims are the fix.
        self.assertTrue(out['held_claims'][0]['reasons'][0].startswith('P5'), out['held_claims'])
        row = syn.norm(BY_ID['2505.15753v1_table_1cb85a8157eb0710_2']['text'])
        atomic = {'text': 'In the MMLU overhead evaluation, SCR with 3 retrieved examples (3 shot) used 59.4 GB total GPU '
                          'memory, versus 30.3 GB with no defense.', 'kind': 'finding',
                  'support': [{'chunk_id': '2505.15753v1_table_1cb85a8157eb0710_2', 'quote': row[row.index('Metric'):]},
                              {'chunk_id': '2505.15753v1_c0022', 'quote': 'We evaluated the computational overhead of '
                               'SCR in terms of GPU memory usage and inference time for the MMLU dataset'}]}
        atomic['chunk_ids'] = [s['chunk_id'] for s in atomic['support']]  # 'MMLU' is only in c0022, so both are attached
        grounding = V2.ground_claim(atomic, BY_ID)
        res = [{'number': m['number'], 'quote': row[row.index('Metric'):], 'reason': 'SIMULATED'}
               for m in grounding['mentions'] if m['status'] == 'contradicted']
        out = publish([atomic], self.passages + [BY_ID['2505.15753v1_table_1cb85a8157eb0710_2']],
                      [decision(0, resolutions=res)])
        self.assertEqual(len(out['claims']), 1, out['held_claims'])

    def test_replay_g03_b_f2_reduced_to_supported_part(self):
        reduced = ('Its inference overhead was measurable: in the MMLU evaluation, total GPU memory was 30.3 GB without '
                   'defense versus 59.3 GB with 2 retrieved examples, and total inference time was 48.9 seconds versus '
                   '74.1 seconds.')
        # numeric_checks_v2 misreads the serialized table row ('No defense' header, '(s)' unit): flags stay
        # until the SIMULATED reviewer anchors each flagged number to an exact span of the attached row quote.
        held = publish([self.claim], self.passages, [decision(0, entail=False, text=reduced)])
        self.assertTrue(held['held_claims'][0]['reasons'][0].startswith('P5'))
        spans = {'59.3': 'GPU Memory (GB) / Total / 30.3: 59.3', '48.9': 'Inference time (s) / Generation / 48.9: 61.2',
                 '74.1': 'Inference time (s) / Total / 48.9: 74.1', '30.3': 'GPU Memory (GB) / Total / 30.3: 59.3'}
        res = [{'number': n, 'quote': s, 'reason': 'SIMULATED'} for n, s in spans.items()]
        out = publish([self.claim], self.passages, [decision(0, entail=False, text=reduced, resolutions=res)])
        self.assertEqual([c['text'] for c in out['claims']], [reduced], out['held_claims'])
        self.assertEqual(out['claims'][0]['reduced_from'], self.claim['text'])

    def test_unit_reduction_may_not_add_numbers(self):
        out = publish([self.claim], self.passages, [decision(0, entail=False, text='Memory was 99.9 GB.')])
        self.assertTrue(out['held_claims'][0]['reasons'][0].startswith('P3'))

    def test_replay_g03_c_f1_withheld_or_reduced_by_quote_entailment(self):
        # M1 G03 C1: "transfer across model sizes without regenerating" is in cited c0027 but not in its quotes.
        result = saved(M1, 'G03')
        claim = clean(result['summary']['claims'][1])
        # Deterministic gates alone cannot see a non-numeric over-claim: with a (wrong) entailing review it passes.
        self.assertEqual(len(publish([claim], result['evidence'], [decision(0)])['claims']), 1)
        # The review now judges the ATTACHED quotes: SIMULATED decisions for the two correct outcomes.
        held = publish([claim], result['evidence'], [decision(0, entail=False)])
        self.assertEqual(held['claims'], [])
        reduced = claim['text'].split('; the authors also report')[0] + '.'
        kept = publish([claim], result['evidence'], [decision(0, entail=False, text=reduced)])
        self.assertNotIn('model sizes', kept['claims'][0]['text'])
        c0027 = BY_ID['2406.06622v1_c0027']['text']
        sentence = 'our framework exhibits transferability, enhancing defense capabilities across different model sizes'
        self.assertIn(sentence, syn.norm(c0027))
        attached = publish([claim], result['evidence'],
                           [decision(0, added=[{'chunk_id': '2406.06622v1_c0027', 'quote': sentence}])])
        self.assertEqual(len(attached['claims']), 1)

    def test_unit_review_prompt_judges_attached_quotes(self):
        prompt = rv.build_prompt('q', {'claims': [dict(GOOD_SYNTHESIS['claims'][0], kind='finding')],
                                       'limitation_support': []}, [P1], [], {})
        self.assertIn("ATTACHED quotes", prompt)
        self.assertIn('not a substitute for them', prompt)

    def test_unit_added_quote_not_in_passage_withholds(self):
        claim = clean(GOOD_SYNTHESIS['claims'][0])
        out = publish([claim], [P1], [decision(0, added=[{'chunk_id': P1['chunk_id'], 'quote': 'invented words here!!'}])])
        self.assertTrue(out['held_claims'][0]['reasons'][0].startswith('P2'))


class NumberAttributionTests(unittest.TestCase):
    """combined-v1 M1 false rejections and true attribution errors."""

    def held(self, qid, index=0):
        result = saved(M1, qid)
        return clean(result['summary']['held_claims'][index]), result['evidence']

    def test_replay_g07_sub_4_second_cleared_deterministically(self):
        claim, passages = self.held('G07')
        out = publish([claim], passages, [decision(0)])
        self.assertEqual(len(out['claims']), 1, out['held_claims'])

    def test_replay_g04_pandora_flag_kept_without_resolution(self):
        claim, passages = self.held('G04')
        out = publish([claim], passages, [decision(0)])
        self.assertEqual(out['claims'], [])
        self.assertTrue(out['held_claims'][0]['reasons'][0].startswith('P5'))

    def test_replay_g04_pandora_published_with_quote_anchored_resolution(self):
        claim, passages = self.held('G04')
        span = ('Pandora demonstrates an average success rate of 64.3% and 34.8% on the four prohibited senarios over '
                'the GPT-3.5 and GPT-4 version of GPT instances, respectively.')
        cond = 'naive malicious question only achieve 3.0% and 1.0% of success rates over ChatGPT powered by the same models.'
        res = [{'number': n, 'quote': span, 'reason': 'SIMULATED'} for n in ('64.3', '34.8')]
        res += [{'number': '3.0', 'quote': cond, 'reason': 'SIMULATED'}]
        out = publish([claim], passages, [decision(0, resolutions=res)])
        self.assertEqual(len(out['claims']), 1, out['held_claims'])

    def test_unit_swapped_respectively_mapping_is_not_resolvable(self):
        claim, passages = self.held('G04')
        swapped = dict(claim, text='Across four prohibited scenarios, Pandora achieved 64.3% jailbreak success on '
                                   'GPT-4 and 34.8% on GPT-3.5.')
        span = ('Pandora demonstrates an average success rate of 64.3% and 34.8% on the four prohibited senarios over '
                'the GPT-3.5 and GPT-4 version of GPT instances, respectively.')
        self.assertFalse(publication.respectively_consistent(swapped['text'], span))
        self.assertTrue(publication.respectively_consistent(claim['text'], span))
        res = [{'number': n, 'quote': span, 'reason': 'SIMULATED wrong resolution'} for n in ('64.3', '34.8')]
        grounding = V2.ground_claim(swapped, {p['chunk_id']: p for p in passages})
        flags = publication.unresolved_flags(swapped, grounding, res, presence_ok=True)
        flagged = {f['number'] for f in flags}
        mention_flags = {m['number'] for m in grounding['mentions'] if m['status'] == 'contradicted'}
        self.assertEqual(flagged & {'64.3', '34.8'}, mention_flags & {'64.3', '34.8'})

    def test_replay_g03_scr_flags_need_resolution_then_publish(self):
        claim, passages = self.held('G03')
        self.assertEqual(publish([claim], passages, [decision(0)])['claims'], [])
        quote = ' '.join(s['quote'] for s in claim['support'])
        span1 = 'For GCG-T, SCR reduces the average ASR from 34.9% (no defense) to 2.5%'
        span2 = 'for ICA, SCR lowers the average ASR from 45.4% to 7.4%'
        self.assertIn(span1, quote)
        self.assertIn(span2, quote)
        res = ([{'number': n, 'quote': span1, 'reason': 'SIMULATED'} for n in ('34.9', '2.5')]
               + [{'number': n, 'quote': span2, 'reason': 'SIMULATED'} for n in ('45.4', '7.4')])
        # v2: the source qualifies 34.9% as "(no defense)"; a claim that drops that qualifier next to the number stays
        # withheld (negation/qualifier protection), while the same claim with the qualifier publishes.
        self.assertEqual(publish([claim], passages, [decision(0, resolutions=res)])['claims'], [])
        kept = dict(claim, text=claim['text'].replace('from 34.9% to 2.5% for GCG-T',
                                                      'from 34.9% (no defense) to 2.5% for GCG-T'))
        out = publish([kept], passages, [decision(0, resolutions=res)])
        self.assertEqual(len(out['claims']), 1, out['held_claims'])

    def test_unit_unsupported_number_withheld(self):
        claim = clean(GOOD_SYNTHESIS['claims'][0])
        claim['text'] = 'Model A reached 75.5% accuracy on the benchmark test set.'
        out = publish([claim], [P1], [decision(0)])
        self.assertIn('75.5', out['held_claims'][0]['reasons'][0])

    def test_unit_wrong_subject_flagged_by_v2(self):
        source = passage('1111.00009v1_c0001', 'GPT-4 reached 71.5% accuracy on the test set. Llama-2 reached '
                                               '64.0% accuracy on the test set.')
        claim = {'text': 'Llama-2 reached 71.5% accuracy on the test set.', 'kind': 'finding', 'chunk_ids': [source['chunk_id']],
                 'support': [{'chunk_id': source['chunk_id'], 'quote': 'GPT-4 reached 71.5% accuracy on the test set.'}]}
        grounding = V2.ground_claim(claim, {source['chunk_id']: source})
        self.assertEqual(grounding['status'], 'contradicted')
        out = publish([claim], [source], [decision(0)])
        self.assertEqual(out['claims'], [])
        # A resolution must be an exact span that contains the clause's entities: 'Llama-2' is not in the quote.
        res = [{'number': '71.5', 'quote': 'GPT-4 reached 71.5% accuracy', 'reason': 'SIMULATED wrong resolution'}]
        self.assertEqual(publish([claim], [source], [decision(0, resolutions=res)])['claims'], [])

    def test_unit_name_digits_are_not_reported_numbers(self):
        cited = 'We fine-tune Llama-2-7B-chat and GPT-4 under a sub-4-second budget.'
        values = {raw for raw, _ in publication.reported_numbers('Llama-2-7B-chat and GPT-4 answered in 4 seconds.', cited)}
        self.assertEqual(values, {'4'})


class PreservationTests(unittest.TestCase):
    def test_unit_one_unsupported_claim_does_not_sink_the_others(self):
        claims = [clean(c) for c in GOOD_SYNTHESIS['claims']]
        claims.append(clean({'text': 'Model C reached 50% accuracy.', 'kind': 'finding', 'support': claims[0]['support']}))
        out = publish(claims, [P1], [decision(i) for i in range(3)])
        self.assertEqual(len(out['claims']), 2)
        self.assertEqual(len(out['held_claims']), 1)
        self.assertEqual(out['status'], 'ok')
        self.assertEqual(out['answer_scope'], 'partial')
        self.assertIn('withheld', out['answer_lead'])

    def test_unit_interpretation_gate(self):
        finding = clean(GOOD_SYNTHESIS['claims'][0])
        good = clean({'text': 'For a client choosing a model, these results support testing Model A accuracy on the '
                              'benchmark test set before wider use.', 'kind': 'interpretation',
                      'support': finding['support']})
        bad = clean({'text': 'For a client, Model A guarantees accurate answers and is production-ready.',
                     'kind': 'interpretation', 'support': finding['support']})
        out = publish([finding, good, bad], [P1], [decision(0), decision(1), decision(2)])
        labels = [c.get('label') for c in out['claims']]
        self.assertEqual(labels, [None, publication.LABEL])
        self.assertTrue(any('interpretation gate' in r for h in out['held_claims'] for r in h['reasons']))


class ReviewContractTests(unittest.TestCase):
    summary = {'status': 'ok', 'claims': [clean(c) for c in GOOD_SYNTHESIS['claims']], 'limitation_support': []}

    def test_unit_missing_and_duplicate_decisions_withhold_only_those_claims(self):
        reply = dict(GOOD_REVIEW, decisions=[decision(0), decision(0)])
        parsed, report = rv.parse(json.dumps(reply), self.summary, [P1, P2])
        self.assertEqual(parsed['decisions'], {})
        self.assertEqual(report['duplicate_decisions'], [0])
        reply = dict(GOOD_REVIEW, decisions=[decision(1)])
        parsed, report = rv.parse(json.dumps(reply), self.summary, [P1, P2])
        self.assertEqual(report['withheld_no_decision'], [0])
        out = publication.publish(self.summary, parsed, [P1, P2], [], v2=V2, gate=GATE)
        self.assertEqual([c['text'] for c in out['claims']], [self.summary['claims'][1]['text']])

    def test_unit_inconsistent_coverage_is_repaired_not_fatal(self):
        reply = dict(GOOD_REVIEW, coverage='full', gap='something missing')
        parsed, report = rv.parse(json.dumps(reply), self.summary, [P1, P2])
        self.assertEqual(parsed['coverage'], 'partial')
        self.assertTrue(report['repairs'])

    def test_unit_non_object_review_fails_stage(self):
        with self.assertRaises(ValueError):
            rv.parse('[1, 2]', self.summary, [P1])


class EngineTests(unittest.TestCase):
    def engine(self, mode, provider, mapping=None, planner=None):
        kwargs = {} if planner is None else {'planner': planner}
        ranked = ranked_from(mapping or {'q': [P1, P2], 'latency per query': [P3]}, [])
        return ConsolidatedResearch(mode, ranked=ranked, count=count, tables=TABLES, generate=provider, v2=V2,
                                    gate=GATE, **kwargs)

    def test_sim_standard_two_calls_end_to_end(self):
        provider = Provider(synthesis=GOOD_SYNTHESIS, review=GOOD_REVIEW)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.engine('standard', provider).run('q', tmp)
            self.assertEqual(provider.calls, ['synthesis', 'review'])
            self.assertEqual(result['summary']['status'], 'ok')
            self.assertEqual(len(result['summary']['claims']), 2)
            self.assertEqual(len(result['summary']['limitations']), 1)
            self.assertEqual(sorted(p.stem for p in (Path(tmp) / 'stages').glob('*.json')),
                             ['base', 'evidence', 'review', 'synthesis'])  # v2: Baseline retrieval is its own stage

    def test_sim_deep_three_calls_protected_plus_supplementary(self):
        provider = Provider(plan=PLAN, synthesis=GOOD_SYNTHESIS, review=GOOD_REVIEW)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.engine('deep', provider).run('q', tmp)
            self.assertEqual(provider.calls, ['plan', 'synthesis', 'review'])
            em = result['evidence_management']
            self.assertEqual(em['protected_ids'], [P1['chunk_id'], P2['chunk_id']])
            self.assertEqual(em['supplementary_ids'], [P3['chunk_id']])

    def test_sim_planner_invalid_falls_back_to_standard_evidence(self):
        provider = Provider(plan='{"not": "a plan"}', synthesis=GOOD_SYNTHESIS, review=GOOD_REVIEW)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.engine('deep', provider).run('q', tmp)
            self.assertEqual(result['plan']['source'], 'fallback')
            self.assertIn('planner failed', result['plan']['fallback'])
            self.assertEqual(result['evidence_management']['supplementary_ids'], [])
            self.assertEqual(result['summary']['status'], 'ok')

    def test_sim_planner_timeout_falls_back(self):
        provider = Provider(plan=TimeoutError('300 s'), synthesis=GOOD_SYNTHESIS, review=GOOD_REVIEW)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.engine('deep', provider).run('q', tmp)
            self.assertIn('TimeoutError', result['plan']['fallback'])

    def test_sim_budget_exhaustion_is_never_a_fallback(self):
        from codex_paired import BudgetExhausted
        provider = Provider(plan=BudgetExhausted('cap'))
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(BudgetExhausted):
            self.engine('deep', provider).run('q', tmp)

    def test_sim_review_timeout_then_resume_repeats_only_review(self):
        provider = Provider(plan=PLAN, synthesis=GOOD_SYNTHESIS, review=[TimeoutError('300 s'), GOOD_REVIEW])
        with tempfile.TemporaryDirectory() as tmp:
            engine = self.engine('deep', provider)
            with self.assertRaises(TimeoutError):
                engine.run('q', tmp)
            attempts = CheckpointStore(tmp).attempts()
            self.assertEqual((attempts[0]['status'], attempts[0]['failed_stage']), ('failed', 'review'))
            result = engine.run('q', tmp)
            self.assertEqual(provider.calls, ['plan', 'synthesis', 'review', 'review'])
            self.assertEqual(result['attempts'][1]['resumed_from'], ['base', 'plan', 'evidence', 'synthesis'])
            self.assertEqual(result['attempts'][1]['timings']['synthesis'], 'checkpoint')

    def test_sim_synthesis_timeout_then_resume_keeps_plan(self):
        provider = Provider(plan=PLAN, synthesis=[TimeoutError('300 s'), GOOD_SYNTHESIS], review=GOOD_REVIEW)
        with tempfile.TemporaryDirectory() as tmp:
            engine = self.engine('deep', provider)
            with self.assertRaises(TimeoutError):
                engine.run('q', tmp)
            engine.run('q', tmp)
            self.assertEqual(provider.calls, ['plan', 'synthesis', 'synthesis', 'review'])

    def test_sim_no_evidence_makes_no_calls(self):
        provider = Provider()
        with tempfile.TemporaryDirectory() as tmp:
            result = self.engine('standard', provider, mapping={'q': []}).run('q', tmp)
            self.assertEqual(provider.calls, [])
            self.assertEqual(result['summary']['status'], 'insufficient_evidence')

    def test_sim_g10_style_reply_through_engine(self):
        reply = dict(GOOD_SYNTHESIS, status='insufficient_evidence')
        provider = Provider(synthesis=reply, review=GOOD_REVIEW)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.engine('standard', provider).run('q', tmp)
            self.assertEqual(result['summary']['status'], 'ok')
            self.assertTrue(result['synthesis_report']['contract_repairs'])


class BudgetTests(unittest.TestCase):
    def test_sim_persistent_call_cap_and_request_guard(self):
        from codex_paired import Budget, BudgetExhausted, CodexCalls
        from request_guard import RequestGuard, RequestTooLarge
        receipts = []

        def fake_generate(prompt, *, response_schema=None):
            receipts.append({'status': 'ok', 'usage': [{'input_tokens': 10}]})
            return json.dumps(GOOD_SYNTHESIS)
        with tempfile.TemporaryDirectory() as tmp:
            budget = Budget(Path(tmp) / 'calls.sqlite3', cap=1)
            guard = RequestGuard(CodexCalls(fake_generate, receipts, budget), request_cap=20_000)
            guard('{"question": "q", "paper_passages": []}', response_schema={})
            with self.assertRaises(BudgetExhausted):
                guard('{"question": "q", "paper_passages": []}', response_schema={})
            self.assertEqual(Budget(Path(tmp) / 'calls.sqlite3', cap=1).used(), 1)  # persists across instances
            budget2 = Budget(Path(tmp) / 'other.sqlite3', cap=5)
            with self.assertRaises(RequestTooLarge):
                RequestGuard(CodexCalls(fake_generate, receipts, budget2), request_cap=100)('x' * 2000, response_schema={})
            self.assertEqual(budget2.used(), 0)  # refused before any call was reserved


if __name__ == '__main__':
    unittest.main()
