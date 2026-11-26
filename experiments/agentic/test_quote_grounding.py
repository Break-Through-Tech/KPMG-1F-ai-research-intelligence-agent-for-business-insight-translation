"""Development cases for opt-in quote grounding. Model-free; scripted replies only.

Passage texts are copied verbatim from the saved F01 (MultiFinRAG, 2506.20821v1) and F03 (2405.17602v1)
evidence packets and were checked against those packets by hand. These are development cases, separate from
the frozen F01-F10 references and scoring. Passing them says nothing about live accuracy.
"""
import json
import sys
import unittest
import unittest.mock
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE), str(HERE.parent / 'agentic-handoff')]
from quote_grounding import enable, ground_draft, locate  # noqa: E402
from test_agentic import Provider, Retriever, claim, passage, plan, verdicts, CORPUS  # noqa: E402
from agents import OrchestratorAgent  # noqa: E402

ROW = 'Derived source table row (HTML cell serialization, not verbatim prose).\n'
CORA = passage('cora', ROW + 'Domain: Citation; Dataset: Cora ( Yang et al., 2016 ; Chen et al., 2023 ); # Nodes: 2,708; '
               '# Edges: 5,429; # Instances ( \\mathcal{S}^{\\text{Full}}/\\mathcal{S}^{\\text{Partial}} ): 2,522/186; '
               'Splitting: Random', '2405.17602v1')
ARXIV = passage('arxiv', ROW + 'Domain: Citation; Dataset: Arxiv ( Hu et al., 2020 ; Chen et al., 2023 ); # Nodes: 16,316; '
                '# Edges: 53,519; # Instances ( \\mathcal{S}^{\\text{Full}}/\\mathcal{S}^{\\text{Partial}} ): 14,791/1,525; '
                'Splitting: Time', '2405.17602v1')
IMAGE = passage('image', ROW + 'Question / Type: 2. Image-based; Number of / Questions: 42; Baseline / with Llama: 0%; '
                'Baseline / with Gemma: 0%; MultiFinRAG / with Llama: 42.9%; MultiFinRAG / with Gemma: 66.7%; '
                'ChatGPT-4o / (Free Tier): 23.8%', '2506.20821v1')
PROSE = passage('prose', 'Additionally, the transition from the Baseline to the MultiFinRAG framework notably improves the '
                'accuracy rate. For instance, accuracy increases from 0% with the Baseline framework using Gemma 3 to 40% '
                'with MultiFinRAG using Gemma 3. This improvement underscores the MultiFinRAG framework�s ability to '
                'retrieve relevant trunks and integrate information effectively to generate accurate final answers.',
                '2506.20821v1')
PACKET = [CORA, ARXIV, IMAGE, PROSE]

NODES = claim('Cora has 2,708 nodes.', 'cora', 'Dataset: Cora ( Yang et al., 2016 ; Chen et al., 2023 ); # Nodes: 2,708')
SPLIT = {'text': 'Cora uses a random split, whereas Arxiv uses a time-based split.', 'kind': 'finding', 'support': [
    {'chunk_id': 'cora', 'quote': 'Dataset: Cora ( Yang et al., 2016 ; Chen et al., 2023 ); ... Splitting: Random'},
    {'chunk_id': 'arxiv', 'quote': 'Dataset: Arxiv ( Hu et al., 2020 ; Chen et al., 2023 ); ... Splitting: Time'}]}
LIMIT = {'text': 'Only two datasets are compared.', 'support': [{'chunk_id': 'cora', 'quote': 'Domain: Citation; Dataset: Cora'}]}


def reply(*claims, status='ok', limits=(LIMIT,)):
    return json.dumps({'status': status, 'claims': list(claims), 'limitations': list(limits)})


def grounded(*claims, **kwargs):
    raw, notes = ground_draft(reply(*claims, **kwargs), PACKET)
    return json.loads(raw), notes


class Locate(unittest.TestCase):
    def test_valid_exact_quote_is_returned_unchanged_and_draft_bytes_untouched(self):
        raw = reply(NODES)
        self.assertEqual(ground_draft(raw, PACKET), (raw, []))

    def test_elided_table_cells_become_the_contiguous_source_span(self):
        answer, notes = grounded(SPLIT)
        quote = answer['claims'][0]['support'][0]['quote']
        self.assertTrue(quote.startswith('Dataset: Cora') and quote.endswith('Splitting: Random'))
        self.assertIn('# Nodes: 2,708; # Edges: 5,429', quote)  # elided words restored, nothing hidden
        self.assertEqual([n['action'] for n in notes], ['restored_elided_text'] * 2)
        self.assertEqual((notes[0]['original'], notes[0]['recovered']), (SPLIT['support'][0]['quote'], quote))

    def test_spaced_dots_and_ellipsis_character_are_both_recognized(self):
        text = ' '.join(PROSE['text'].split())
        for mark in ('. . .', '…', '...'):
            q = f'notably improves the accuracy rate{mark} This improvement underscores the MultiFinRAG'
            self.assertTrue(locate(q, text).startswith('notably improves the accuracy rate. For instance'), mark)

    def test_out_of_order_pieces_and_short_pieces_are_not_grounded(self):
        text = ' '.join(CORA['text'].split())
        self.assertIsNone(locate('Splitting: Random ... Dataset: Cora ( Yang et al.', text))
        self.assertIsNone(locate('Dataset: Cora ( Yang et al., 2016 ... Random', text))

    def test_overlong_restored_span_is_rejected(self):
        text = 'Alpha opening sentence here. ' + 'filler words ' * 120 + 'Omega closing sentence here.'
        self.assertIsNone(locate('Alpha opening sentence here. ... Omega closing sentence here.', text))

    def test_shortest_span_is_chosen_when_first_piece_repeats(self):
        text = 'the model improved accuracy. noise. the model improved accuracy. by 4 points on the test set.'
        self.assertEqual(locate('the model improved accuracy. ... on the test set.', text),
                         'the model improved accuracy. by 4 points on the test set.')


class Draft(unittest.TestCase):
    def test_paraphrased_quote_drops_only_its_claim(self):
        para = claim('Arxiv has 16,316 nodes.', 'arxiv', 'The Arxiv dataset contains 16,316 nodes in total')
        answer, notes = grounded(NODES, para)
        self.assertEqual([c['text'] for c in answer['claims']], [NODES['text']])
        self.assertEqual(notes, [{'field': 'claims', 'index': 1, 'action': 'dropped', 'chunk_id': 'arxiv',
                                  'reason': 'quote not found in the cited passage', 'original': para['support'][0]['quote']}])

    def test_invented_quote_and_unknown_id_are_dropped(self):
        invented = claim('Cora was split by time.', 'cora', 'Splitting: Time-based for Cora')
        unknown = claim('Cora has 2,708 nodes.', 'nope', 'quote that appears nowhere in the packet')
        answer, notes = grounded(invented, unknown, NODES)
        self.assertEqual(answer['claims'], [json.loads(reply(NODES))['claims'][0]])
        self.assertEqual([n['reason'] for n in notes], ['quote not found in the cited passage', 'unknown chunk ID'])

    def test_wrong_citation_id_drops_the_claim_rather_than_guessing(self):
        # The quote is real, but from the Arxiv row; re-citing would let a mismatched claim pass the number check.
        wrong = claim('Cora has 16,316 nodes.', 'cora', 'Dataset: Arxiv ( Hu et al., 2020 ; Chen et al., 2023 ); # Nodes: 16,316')
        answer, notes = grounded(NODES, wrong)
        self.assertEqual([c['text'] for c in answer['claims']], [NODES['text']])
        self.assertEqual(notes[0]['reason'], 'quote not found in the cited passage')

    def test_conflicting_sources_keep_their_own_citations(self):
        # Conflicting values are for the verifier and number checks; grounding must not merge or re-cite them.
        other = {**IMAGE, 'chunk_id': 'image-v2', 'text': IMAGE['text'].replace('66.7%', '61.9%')}
        a = claim('MultiFinRAG with Gemma scored 66.7%.', 'image', 'MultiFinRAG / with Gemma: 66.7%')
        b = claim('MultiFinRAG with Gemma scored 61.9%.', 'image-v2', 'MultiFinRAG / with Gemma: 61.9%')
        raw = reply(a, b)
        self.assertEqual(ground_draft(raw, PACKET + [other]), (raw, []))

    def test_numbers_and_configuration_are_preserved_in_the_restored_quote(self):
        c = claim('MultiFinRAG with Gemma scored 66.7% on 42 image questions.', 'image',
                  'Number of / Questions: 42; ... MultiFinRAG / with Gemma: 66.7%')
        quote = grounded(c)[0]['claims'][0]['support'][0]['quote']
        self.assertIn('Baseline / with Gemma: 0%; MultiFinRAG / with Llama: 42.9%; MultiFinRAG / with Gemma: 66.7%', quote)

    def test_bad_limitation_is_dropped_but_findings_stay(self):
        bad = {'text': 'Results may not transfer.', 'support': [{'chunk_id': 'cora', 'quote': 'results may not transfer to other graphs'}]}
        answer, _ = grounded(NODES, limits=(bad, LIMIT))
        self.assertEqual((len(answer['claims']), answer['limitations']), (1, [LIMIT]))


class Malformed(unittest.TestCase):
    def test_non_json_and_non_object_replies_pass_through(self):
        for raw in ('not json', '[1, 2]', '', None):
            self.assertEqual(ground_draft(raw, PACKET), (raw, []))

    def test_structurally_malformed_claim_is_left_for_the_schema_to_reject(self):
        broken = {'text': 'No support field.', 'kind': 'finding'}
        raw = reply(broken, NODES)
        self.assertEqual(ground_draft(raw, PACKET), (raw, []))

    def test_all_claims_dropped_turns_into_a_cited_abstention_only_if_a_limitation_survives(self):
        bad = claim('Invented.', 'cora', 'this sentence is not in the source')
        answer, _ = grounded(bad)
        self.assertEqual((answer['status'], answer['claims'], len(answer['limitations'])), ('insufficient_evidence', [], 1))
        answer, _ = grounded(bad, limits=())
        self.assertEqual((answer['status'], answer['limitations']), ('insufficient_evidence', []))  # synthesis rejects


TQ = 'For Cora and Arxiv, how many nodes did each have, and which used a random split?'


def orchestrate(research, verify, *, quote_grounding, packet=PACKET):
    p = Provider(plan=[plan()], research=[research], verify=verify)
    corpus = {x['chunk_id']: x for x in packet}
    with unittest.mock.patch.dict(CORPUS, corpus):
        engine = OrchestratorAgent(generate=p, retrieve=Retriever({'Cora': list(corpus)}), top_k=8, research_only=True)
        r = (enable(engine) if quote_grounding else engine).run(TQ)
    return r, p


class EndToEnd(unittest.TestCase):
    """Real synthesis validation, number checks, gate and envelope; scripted model replies only."""

    def test_f03_shaped_draft_was_a_false_abstention_and_now_publishes(self):
        draft = json.loads(reply(NODES, SPLIT))
        before, p0 = orchestrate(draft, [], quote_grounding=False)
        self.assertEqual((before['status'], p0.calls), ('insufficient_evidence', ['plan', 'research']))
        after, p1 = orchestrate(draft, [verdicts(('supported', []), ('supported', []))], quote_grounding=True)
        self.assertEqual((after['status'], p1.calls), ('ok', ['plan', 'research', 'verify']))
        self.assertEqual(len(after['summary']['claims']), 2)
        research = next(e for e in after['trace'] if e['type'] == 'reply' and e['from'] == 'research_agent')
        self.assertEqual([n['action'] for n in research['output']['quote_grounding']], ['restored_elided_text'] * 2)

    def test_invented_claim_is_dropped_and_valid_claims_reach_the_verifier(self):
        invented = claim('Arxiv used a random split.', 'arxiv', 'Splitting: Random for Arxiv as well')
        r, p = orchestrate(json.loads(reply(NODES, invented)), [verdicts(('supported', []))], quote_grounding=True)
        verify_prompt = next(prompt for role, prompt in p.prompts if role == 'verify')
        self.assertNotIn('Arxiv used a random split', verify_prompt)
        self.assertEqual([c['text'] for c in r['summary']['claims']], [NODES['text']])

    def test_numerical_contradiction_with_exact_quote_is_still_held(self):
        wrong = claim('MultiFinRAG with Gemma scored 42.9% on image questions.', 'image', 'MultiFinRAG / with Gemma: 66.7%')
        r, _ = orchestrate(json.loads(reply(NODES, wrong)), [verdicts(('supported', []), ('supported', []))],
                           quote_grounding=True)
        self.assertEqual([c['text'] for c in r['summary']['claims']], [NODES['text']])
        self.assertIn('numbers_and_qualifiers', r['summary']['held_claims'][0]['verification']['held_reason'])

    def test_partial_answer_keeps_supported_part_and_reports_scope(self):
        para = claim('Arxiv used a time-based split.', 'arxiv', 'Arxiv was split by publication time')
        r, _ = orchestrate(json.loads(reply(NODES, para)),
                           [verdicts(('supported', []), coverage='partial')], quote_grounding=True)
        self.assertEqual((r['status'], r['summary']['answer_scope']), ('ok', 'partial'))

    def test_malformed_reply_still_fails_closed(self):
        r, p = orchestrate('{"status": "ok", "claims": [', [], quote_grounding=True)
        self.assertEqual((r['status'], p.calls), ('insufficient_evidence', ['plan', 'research']))


class MultiRound(unittest.TestCase):
    def test_handoff_revision_with_elision_no_longer_discards_the_verified_first_round(self):
        from handoff import EvidenceHandoffOrchestrator
        from test_handoff import ReplayProvider

        def retriever(query, cap):
            return [deepcopy(ARXIV)] if 'second method' in query else [deepcopy(CORA)]
        results = {}
        for flag in (False, True):
            provider = ReplayProvider(NODES, SPLIT, LIMIT)
            engine = EvidenceHandoffOrchestrator(generate=provider, retrieve=retriever, top_k=8, index_sha256='fixture')
            results[flag] = (enable(engine) if flag else engine).run(TQ)
        # Before: the rejected revision also discards the first round's verified claim.
        self.assertEqual((results[False]['status'], results[False]['summary']['claims']), ('insufficient_evidence', []))
        self.assertEqual(sorted(c['text'] for c in results[True]['summary']['claims']), sorted([NODES['text'], SPLIT['text']]))


class RecordedGemini(unittest.TestCase):
    """Saved simplified-v2 replies under their identical saved packets. Skipped when the run data is absent."""

    def test_recorded_false_abstentions_now_pass_and_complete_answers_are_unchanged(self):
        from replay_quote_grounding import RUN, replay
        if not RUN.exists():
            self.skipTest('recorded run not present in this checkout')
        rows = {r['case']: r for r in replay()}
        for case in ('F01/current', 'F01/handoff', 'F03/current'):
            self.assertEqual(rows[case]['before']['status'], 'rejected')
            self.assertEqual(rows[case]['after']['status'], 'ok')
            self.assertTrue(all(n['action'] == 'restored_elided_text' for n in rows[case]['grounding']))
        for case in ('F02/current', 'F02/handoff'):
            self.assertEqual(rows[case]['before'], rows[case]['after'])
            self.assertEqual(rows[case]['grounding'], [])


if __name__ == '__main__':
    unittest.main()
