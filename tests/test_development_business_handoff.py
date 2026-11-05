"""The frozen-evidence comparison must retain accepted caveat sources."""
import unittest
from unittest.mock import Mock, patch

from evaluation import check_answer_quality_dev as comparison
from tests.test_business_evidence_handoff import sources, item, business


class DevelopmentBusinessHandoffTests(unittest.TestCase):
    def test_retains_caveat_source_and_excludes_rejected_audit(self):
        p1,p2,p3,p4=sources()
        summary={'status':'ok','claims':[item('The pilot improved completion.',p1)],
                 'limitation_support':[item('Deployment remains untested.',p2)],
                 'quality_review':{'original_claims':[item('Rejected draft.',p3)]}}
        generate=Mock()
        with patch.object(comparison,'translate',return_value=business()) as translate:
            result=comparison.translate_accepted_summary(summary,[p2,p3,p1,p4],
                industry='banking',generate=generate,compact=True)
        passed_summary,evidence=translate.call_args.args
        self.assertEqual([p['chunk_id'] for p in evidence],['p2','p1'])
        self.assertEqual(passed_summary['limitation_support'],summary['limitation_support'])
        self.assertNotIn('quality_review',passed_summary)
        self.assertEqual(translate.call_args.kwargs,
                         {'industry':'banking','generate':generate,'compact':True})
        self.assertEqual(result,business())
        generate.assert_not_called()

    def test_missing_accepted_source_fails_before_translation(self):
        p1,p2,p3,p4=sources()
        summary={'status':'ok','claims':[item('The pilot improved completion.',p1)],
                 'limitation_support':[item('Deployment remains untested.',{**p2,'chunk_id':'missing'})]}
        with patch.object(comparison,'translate') as translate:
            with self.assertRaisesRegex(ValueError,'accepted summary source'):
                comparison.translate_accepted_summary(summary,[p1,p2,p3,p4],
                    industry='banking',generate=Mock())
        translate.assert_not_called()

if __name__=='__main__':unittest.main()
