"""Additional synthetic review regressions for PR #21."""
from copy import deepcopy
from decimal import Decimal
import unittest
from engine.core import COA_MAP,generate,money
from test_multi_bank import fixture


class MultiBankReviewTests(unittest.TestCase):
    def test_result_chart_is_deeply_isolated_from_global_chart(self):
        original=deepcopy(COA_MAP)
        try:
            result=generate(fixture());result['coa']['4000']['name']='Changed locally'
            self.assertEqual(COA_MAP,original)
        finally:
            COA_MAP.clear();COA_MAP.update(original)

    def test_transfer_journal_identity_survives_source_row_order(self):
        p=fixture();first={e['journal_id'] for e in generate(p)['entries'] if e['source'] in ('Bank','Bank transfer')}
        p.bank=list(reversed(p.bank))
        second={e['journal_id'] for e in generate(p)['entries'] if e['source'] in ('Bank','Bank transfer')}
        self.assertEqual(first,second)

    def test_decimal_nonfinite_is_rejected_before_accounting(self):
        for value in ('NaN','Infinity','1E100'):
            with self.subTest(value=value),self.assertRaises(ValueError):money(Decimal(value))

    def test_duplicated_pair_evidence_cannot_post_one_leg(self):
        p=fixture();p.bank.append(dict(p.bank[1],transfer_id='',account_code='5200'))
        result=generate(p)
        self.assertTrue(result['errors'])
        self.assertFalse(any(e['source']=='Bank transfer' for e in result['entries']))
