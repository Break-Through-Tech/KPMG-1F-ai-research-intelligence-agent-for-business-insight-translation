r"""S3 tests: retrieval R, synthesis C, validator and lead-guard safety fixtures, V2 replay identity, frozen-file
integrity and an end-to-end engine run with fake model calls. 0 live model calls.

    D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -X utf8 -m unittest test_s3   (from this folder)
"""
import json
from pathlib import Path

import tempfile
import unittest
from unittest import mock

import s3_env
import evidence as ev
import s3_answer as sa
import s3_evidence as se
from components import components, named_terms

SAVED_S2 = s3_env.ROOT / 'data/processed/fresh-v3-S2-consolidated-v2-standard'


# ---------------------------------------------------------------- fixtures

def row(cid, text='alpha beta gamma delta', section='results', paper=None):
    return {'chunk_id': cid, 'arxiv_id': paper or cid.split('_')[0], 'text': text, 'title': 'T', 'section': section}


def count(p):
    return len(p['text'].split())


class NoTables:
    tables = {}

    def siblings(self, _cid):
        return []


def fake_ranked(rankings):
    def ranked(query, n):
        if query not in rankings:
            raise RuntimeError('search failed')
        return rankings[query][:n]
    return ranked


# ---------------------------------------------------------------- components

def test_components_split_asks_and_carry_names():
    q = 'A retailer is evaluating forecasting. What does FooNet propose, how accurate was it on M5, and what limits apply?'
    got = components(q)
    assert len(got) == 3 and all(c.endswith('?') for c in got)
    assert got[1].startswith('FooNet') and got[2].startswith('FooNet')
    assert 'retailer' not in ' '.join(got)            # business preamble is not added
    assert components('What is FooNet?') == []


def test_components_leading_context_and_prepositions():
    got = components('In the BarNet study, what data was used, on what hardware was it trained, and which baseline won?')
    assert got[0].startswith('In the BarNet study,')
    assert any('on what hardware' in c for c in got)


def test_components_cap_and_generic_names():
    q = 'What is A1x, what is B2y, what is C3z, what is D4w, what is E5v, what is F6u, what is G7t?'
    assert len(components(q)) == 6
    assert 'LLM' not in named_terms('Do LLMs and LLM-based RAG systems with GPT-4 work?')
    assert 'GPT-4' in named_terms('Do LLMs and LLM-based RAG systems with GPT-4 work?')


# ---------------------------------------------------------------- retrieval R

def test_packet_budget_protection_scoping_and_failed_search():
    q = 'What does FooNet do, and what limits apply?'
    comps = components(q)
    original = [row(f'P1_c{i:04d}', 'w ' * 300) for i in range(40)]
    rankings = {q: original,
                comps[0]: [row('P2_c0000', 'w ' * 50)] + original[30:35],   # other paper: filtered out
                }  # comps[1] missing: its search fails
    packet = se.s3_packet(q, fake_ranked(rankings), count, NoTables(), parallel=False)
    ids = [p['chunk_id'] for p in packet['passages']]
    assert ids[:4] == [p['chunk_id'] for p in original[:4]]            # original top-4 first
    assert 'P2_c0000' not in ids                                        # paper scoping
    assert packet['base_tokens'] <= se.S3_TOKENS
    errors = [s for s in packet['searches'] if s['error']]
    assert len(errors) == 1 and errors[0]['role'] == 'component'      # failure recorded, answer not blocked
    assert any(c in ids for c in ('P1_c0030', 'P1_c0031'))              # component evidence promoted


def test_packet_original_search_failure_propagates():
    with unittest.TestCase().assertRaises(RuntimeError):
        se.s3_packet('What is X, and why?', fake_ranked({}), count, NoTables(), parallel=False)


def test_packet_deterministic_parallel_equals_sequential():
    q = 'What does FooNet do, how fast is it, and what limits apply?'
    comps = components(q)
    base = [row(f'P1_c{i:04d}', 'w ' * 200) for i in range(60)]
    rankings = {q: base, **{c: list(reversed(base))[i:] for i, c in enumerate(comps)}}
    a = se.s3_packet(q, fake_ranked(rankings), count, NoTables(), parallel=True)
    b = se.s3_packet(q, fake_ranked(rankings), count, NoTables(), parallel=False)
    assert [p['chunk_id'] for p in a['passages']] == [p['chunk_id'] for p in b['passages']]


def test_packet_request_guard_trims_from_end_only():
    q = 'What does FooNet do, and what limits apply?'
    base = [row(f'P1_c{i:04d}', 'w ' * 100) for i in range(30)]
    rankings = {q: base, **{c: base for c in components(q)}}
    with mock.patch.object(ev, 'DEEP_EVIDENCE_EST', ev.serialized_estimate(base[:6])):
        packet = se.s3_packet(q, fake_ranked(rankings), count, NoTables(), parallel=False)
        limit = ev.DEEP_EVIDENCE_EST
    assert [p['chunk_id'] for p in packet['passages'][:4]] == [p['chunk_id'] for p in base[:4]]
    assert packet['trimmed_for_request_size']
    assert ev.serialized_estimate(packet['passages']) <= limit


# ---------------------------------------------------------------- lead guard (safety fixtures)

CASES_test_absence_claims_about_papers_are_caught = [
    'The paper does not report inference cost.',
    'The authors did not evaluate pediatric cases.',
    'Neither study reports a production success rate.',
    'Cost is not reported in the paper.',
    'The study lacks a deployment baseline.',
    'These papers do not include ablations; the retrieved evidence shows only totals.',
]


def test_absence_claims_about_papers_are_caught():
  for text in CASES_test_absence_claims_about_papers_are_caught:
    assert sa.asserts_paper_absence(text)
    out = sa.guard_lead({'answer_lead': text, 'answer_lead_check': None})
    assert out['answer_lead'] == sa.NEUTRAL_LEAD and 'S3' in out['answer_lead_check']


CASES_test_scoped_gaps_are_kept = [
    'The supplied passages do not establish performance on the client database.',
    'The retrieved evidence does not quantify inference cost on the target hardware.',
    'Some requested details are not established by the verified answer.',
    '',
]


def test_scoped_gaps_are_kept():
  for text in CASES_test_scoped_gaps_are_kept:
    assert not sa.asserts_paper_absence(text)
    assert sa.guard_lead({'answer_lead': text})['answer_lead'] == text


def test_saved_v2_leads_are_not_false_positives():
    leads = [json.loads((d / 'result.json').read_text(encoding='utf-8'))['summary'].get('answer_lead', '')
             for d in sorted(SAVED_S2.glob('J0?'))]
    assert len(leads) == 8 and not any(sa.asserts_paper_absence(l) for l in leads)


# ---------------------------------------------------------------- validator (safety fixtures)

def summary_with(n):
    return {'claims': [{'text': f'c{i}', 'kind': 'finding', 'draft_index': i + 10} for i in range(n)]}


def test_validator_requires_reviewer_confirmation_and_publication():
    comps = ['a?', 'b?', 'c?', 'd?']
    summary = summary_with(3)
    review = {'limitations': [{'text': 'Scope: only GPT-3.5.'}, {'text': 'Dropped limitation.'}],
              'component_checks': {
                  0: {'verdict': 'answered', 'claim_indices': [0], 'limitation_index': -1},   # published -> answered
                  1: {'verdict': 'answered', 'claim_indices': [1], 'limitation_index': -1},   # held -> downgraded
                  2: {'verdict': 'not_established', 'claim_indices': [], 'limitation_index': 1},  # not published
                  3: {'verdict': 'not_established', 'claim_indices': [], 'limitation_index': 0}}}
    published = {'claims': [{'draft_index': 10, 'kind': 'finding'}, {'draft_index': 12, 'kind': 'interpretation'}],
                 'limitation_support': [{'text': 'Scope: only GPT-3.5.'}]}
    cov = sa.coverage(comps, summary, review, published)
    assert [c['status'] for c in cov] == ['answered', 'not_retrieved', 'not_retrieved', 'not_established']
    assert cov[0]['finding_draft_indices'] == [10]
    assert cov[3]['limitation'] == 'Scope: only GPT-3.5.'


def test_drafter_map_alone_never_counts_and_interpretations_do_not_answer():
    comps = ['a?', 'b?']
    summary = {**summary_with(2), 'component_map': {0: {'status': 'answered', 'claim_indices': [10]}}}
    review = {'limitations': [], 'component_checks': {
        1: {'verdict': 'answered', 'claim_indices': [1], 'limitation_index': -1}}}
    published = {'claims': [{'draft_index': 10, 'kind': 'finding'}, {'draft_index': 11, 'kind': 'interpretation'}],
                 'limitation_support': []}
    assert [c['status'] for c in sa.coverage(comps, summary, review, published)] == ['not_retrieved', 'not_retrieved']


def test_not_retrieved_note_is_template_about_retrieval_not_the_paper():
    cov = sa.coverage(['What did it cost?'], summary_with(0), {'limitations': [], 'component_checks': {}},
                      {'claims': [], 'limitation_support': []})
    note = cov[0]['note']
    assert note.startswith('Not found in the retrieved evidence') and 'does not mean the paper' in note
    assert not sa.asserts_paper_absence(note.split(': ', 1)[0])


# ---------------------------------------------------------------- synthesis/review parsing

def test_split_reply_and_v2_parser_identity():
    import synthesis as syn
    passages = [row('P1_c0000', 'GPT-4 reached 82% stability on the benchmark.')]
    v2_reply = {'status': 'ok', 'claims': [{'text': 'GPT-4 reached 82% stability.', 'kind': 'finding',
                                            'support': [{'chunk_id': 'P1_c0000', 'quote': 'GPT-4 reached 82% stability'}]}],
                'limitations': []}
    s3_reply = {**v2_reply, 'component_map': [{'component': 0, 'status': 'answered', 'claim_indices': [0],
                                               'limitation_indices': []}]}
    cleaned, cmap = sa.split_reply(json.dumps(s3_reply), 'component_map')
    assert syn.parse(cleaned, passages) == syn.parse(json.dumps(v2_reply), passages)
    assert cmap[0]['status'] == 'answered'


def test_component_map_invalid_and_duplicate_entries_dropped():
    item = sa.component_map_schema(2)['items']
    report = []
    entries = [{'component': 0, 'status': 'answered', 'claim_indices': [0], 'limitation_indices': []},
               {'component': 0, 'status': 'not_retrieved', 'claim_indices': [], 'limitation_indices': []},
               {'component': 1, 'status': 'maybe', 'claim_indices': [], 'limitation_indices': []}]
    assert sa.parse_entries(entries, 2, item, report, 'component_map') == {}
    assert len(report) == 2


def test_synthesis_prompt_and_schema_extend_v2_only():
    import synthesis as syn
    passages = [row('P1_c0000')]
    base = syn.build_prompt('Q?', passages, [])
    assert sa.build_synthesis_prompt('Q?', passages, [], []) == base
    ext = sa.build_synthesis_prompt('Q?', passages, [], ['a?', 'b?'])
    assert ext.startswith(base) and 'REQUESTED COMPONENTS' in ext
    schema = sa.synthesis_schema(['P1_c0000'], 2)
    v2 = syn.synthesis_schema(['P1_c0000'])
    assert {k: v for k, v in schema['properties'].items() if k != 'component_map'} == v2['properties']


# ---------------------------------------------------------------- replay identity (C3) and frozen files (C1)

def test_replay_saved_s2_through_s3_publish_is_identical():
  for qid in [f'J0{i}' for i in range(1, 9)]:
    folder = SAVED_S2 / qid
    load = lambda n: json.loads((folder / 'stages' / f'{n}.json').read_text(encoding='utf-8'))  # noqa: E731
    syn_stage, rev_stage, evidence = load('synthesis'), load('review'), load('evidence')
    saved = json.loads((folder / 'result.json').read_text(encoding='utf-8'))['summary']
    review = {**rev_stage['review'], 'decisions': {int(k): v for k, v in rev_stage['review']['decisions'].items()}}
    out = sa.publish(syn_stage['summary'], review, evidence['passages'], evidence['notes'], [],
                     v2=s3_env.v2env.load_v2(), gate=s3_env.v2env.load_gate())
    out.pop('component_coverage')
    assert json.loads(json.dumps(out)) == saved


def test_frozen_v2_files_unchanged():
    import seal_v3
    assert seal_v3.verify() == 'verified'


# ---------------------------------------------------------------- end to end (fake calls)

def test_engine_end_to_end_two_calls_and_resume():
    tmp_path = Path(tempfile.mkdtemp())
    from s3_engine import S3Research
    q = 'What does FooNet report, and what limits apply?'
    comps = components(q)
    passages = [row('P1_c0000', 'FooNet reports 82% accuracy on M5.'),
                row('P1_c0001', 'Experiments use only the M5 dataset.', section='limitations')]
    rankings = {q: passages, **{c: passages for c in comps}}
    calls = []

    def generate(prompt, response_schema):
        calls.append(prompt)
        if len(calls) == 1:
            assert 'REQUESTED COMPONENTS' in prompt
            return json.dumps({'status': 'ok', 'claims': [{'text': 'FooNet reports 82% accuracy on M5.', 'kind': 'finding',
                               'support': [{'chunk_id': 'P1_c0000', 'quote': 'FooNet reports 82% accuracy on M5'}]}],
                               'limitations': [], 'component_map': [
                                   {'component': 0, 'status': 'answered', 'claim_indices': [0], 'limitation_indices': []},
                                   {'component': 1, 'status': 'not_retrieved', 'claim_indices': [], 'limitation_indices': []}]})
        assert 'COMPONENT CHECK' in prompt
        return json.dumps({'coverage': 'partial', 'gap': 'The paper does not report deployment limits.',
                           'decisions': [{'index': 0, 'supported': True, 'relevant': True, 'quotes_entail': True,
                                          'reason': 'ok', 'supported_text': '', 'reduced_entailed': False,
                                          'related': False, 'added_support': [], 'flag_resolutions': []}],
                           'limitations': [{'text': 'Experiments use only the M5 dataset.',
                                            'support': [{'chunk_id': 'P1_c0001',
                                                         'quote': 'Experiments use only the M5 dataset.'}]}],
                           'component_checks': [
                               {'component': 0, 'verdict': 'answered', 'claim_indices': [0], 'limitation_index': -1,
                                'reason': 'states accuracy'},
                               {'component': 1, 'verdict': 'not_established', 'claim_indices': [],
                                'limitation_index': 0, 'reason': 'scope'}]})

    engine = S3Research(ranked=fake_ranked(rankings), count=count, tables=NoTables(), generate=generate,
                        v2=s3_env.v2env.load_v2(), gate=s3_env.v2env.load_gate(), parallel_search=False)
    result = engine.run(q, tmp_path / 'q')
    summary = result['summary']
    assert len(calls) == 2
    assert [c['status'] for c in summary['component_coverage']] == ['answered', 'not_established']
    assert summary['answer_lead'] == sa.NEUTRAL_LEAD                       # unscoped absence lead replaced
    assert [l['text'] for l in summary['limitation_support']] == ['Experiments use only the M5 dataset.']
    again = engine.run(q, tmp_path / 'q')                                  # resume: all stages checkpointed
    assert len(calls) == 2 and again['summary'] == summary


# ---------------------------------------------------------------- fresh-v4 runner (fake objects, 0 calls)

def test_runner_combined_cap_and_resume_limit():
    import sqlite3
    import run_fresh4 as rf
    root = Path(tempfile.mkdtemp())
    for arm, n in (('S3', 20), ('S2', 6)):
        d = root / rf.ARM_DIRS[arm]
        d.mkdir(parents=True)
        with sqlite3.connect(d / 'calls.sqlite3') as db:
            db.execute('CREATE TABLE calls (id INTEGER)')
            db.executemany('INSERT INTO calls VALUES (?)', [(i,) for i in range(n)])
        db.close()
    assert rf.combined_check('S3', root)['combined_used'] == 26          # 26 + 5 remaining <= 50
    with sqlite3.connect(root / rf.ARM_DIRS['S2'] / 'calls.sqlite3') as db:
        db.executemany('INSERT INTO calls VALUES (?)', [(i,) for i in range(20)])
    db.close()
    with unittest.TestCase().assertRaises(SystemExit):                    # 46 + 5 > 50: refuses
        rf.combined_check('S3', root)

    class Budget:
        def used(self):
            return 0

    class Calls:
        budget, fatal, question = Budget(), None, None

    class Guard:
        records = []

    class Engine:
        def __init__(self):
            self.seen = []

        def run(self, question, folder):
            self.seen.append(question)
            folder.mkdir(parents=True, exist_ok=True)
            att = folder / 'attempts.json'
            prior = json.loads(att.read_text()) if att.is_file() else []
            att.write_text(json.dumps(prior + [{'status': 'failed'}]))
            raise ValueError('boom')
    engine = Engine()
    qs = [{'id': 'Q1', 'question': 'q1?'}]
    out = Path(tempfile.mkdtemp())
    for _ in range(3):
        status = rf.run('S3', engine=engine, calls=Calls(), guard=Guard(), receipts=[], out_root=out, questions=qs)
    assert len(engine.seen) == 2 and status['Q1']['state'] == 'failed'   # at most one resume

class S3Tests(unittest.TestCase):
    pass


for _name, _fn in list(globals().items()):
    if _name.startswith('test_') and callable(_fn):
        setattr(S3Tests, _name, staticmethod(_fn))

if __name__ == '__main__':
    unittest.main()
