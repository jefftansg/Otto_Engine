"""Backend safety tests for the five-step guided workflow (UI needs Mac smoke test)."""
from pathlib import Path
import sys
import types
import unittest

try:
    import streamlit
except ImportError:
    sys.modules['streamlit']=types.ModuleType('streamlit')

from guided import _bank_batch
from engine.importers import inspect_document, empty_company
from engine.autofill import extract_acra_profile, extract_bank_statement
from engine.core import Package, generate

ROOT=Path(__file__).resolve().parents[1]/'example_imports'/'guided_demo'

def parsed_demo():
    results=[]
    for f in sorted(ROOT.glob('*.pdf')):
        doc=inspect_document(f.name,f.read_bytes())
        results.append((doc,extract_acra_profile(doc),extract_bank_statement(doc)))
    return results

class GuidedModeTests(unittest.TestCase):
    def setUp(self):
        self.parsed=parsed_demo()
        self.cfg=empty_company()
        self.cfg.update(company_name='GUIDED DEMO PTE. LTD.',uen='202588888A',
            fy_start='2025-01-01',fy_end='2025-12-31',fy_confirmed=True,
            bank_statement_opening='0.00',bank_statement_closing='1230.00',bank_balances_confirmed=True)

    def test_demo_ACRA_profile_detected(self):
        profile=[a for d,a,b in self.parsed if a.get('fields')][0]['fields']
        self.assertEqual(profile['company_name'],'GUIDED DEMO PTE. LTD.')
        self.assertEqual(profile['fy_end'],'2025-12-31')

    def test_safe_demo_bank_batch(self):
        r=_bank_batch(self.parsed,self.cfg,[])
        self.assertTrue(r['balances']['ready'],r['balances']['errors'])
        self.assertEqual(len(r['rows']),4)
        self.assertEqual((r['balances']['opening'],r['balances']['closing']),('0.00','1230.00'))
        self.assertFalse(r['issues']+r['mismatches']+r['duplicates']+r['outside'])

    def test_existing_transactions_block_import(self):
        r=_bank_batch(self.parsed,self.cfg,[])
        repeat=_bank_batch(self.parsed,self.cfg,r['rows'])
        self.assertEqual(len(repeat['duplicates']),4)

    def test_changed_year_disables_batch(self):
        self.cfg['fy_start']='2025-05-01'
        r=_bank_batch(self.parsed,self.cfg,[])
        self.assertFalse(r['balances']['ready'])
        self.assertTrue(r['outside'])

    def test_demonstration_reports_balance_after_review(self):
        r=_bank_batch(self.parsed,self.cfg,[])
        for row,code in zip(r['rows'],['3100','4000','5400','5100']):
            row['account_code']=code
        report=generate(Package(self.cfg,bank=r['rows']))
        self.assertEqual(report['errors'],[])
        self.assertEqual(str(report['profit']),'230.00')
        self.assertEqual(str(report['ledger_end']),'1230.00')

if __name__=='__main__': unittest.main()
