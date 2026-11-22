"""Synthetic acceptance tests for the multi-bank SGD pilot.

These do not demonstrate PDF account detection or professional sign-off.
"""
import unittest
from decimal import Decimal as D
from engine.core import Package, generate, COA_MAP
from engine.reports import management_pdf, financial_statements_pdf, xlsx_report


def fixture():
    cfg=dict(company_name='Fictional Two Banks Pte Ltd',uen='TEST123',
        fy_start='2025-01-01',fy_end='2025-12-31',currency='SGD',
        entity_type='Private limited company',reporting_framework='FRS',
        bank_accounts=[
            dict(code='1000',name='Bank A',currency='SGD',opening='1000',closing='1200',confirmed=True,coverage_confirmed=True),
            dict(code='1001',name='Bank B',currency='SGD',opening='500',closing='600',confirmed=True,coverage_confirmed=True)])
    def bank(code,ref,dep,wd,counter,tid=''):
        return dict(date='2025-06-01',bank_account_code=code,reference=ref,
            deposit=dep,withdrawal=wd,account_code=counter,transfer_id=tid,evidence_ref='E-'+code)
    rows=[bank('1000','same','500','','4000'),bank('1000','T1','','300','TRANSFER','T'),
          bank('1001','T1','300','','TRANSFER','T'),bank('1001','same','','200','5200')]
    journals=[dict(journal_id='OPEN',date='2024-12-31',account_code=c,debit=d,credit=cr)
              for c,d,cr in [('1000','1000',''),('1001','500',''),('3100','','1500')]]
    evidence=[dict(evidence_ref='E-'+c,review_status='reviewed') for c in ('1000','1001')]
    return Package(cfg, bank=rows, journals=journals, evidence=evidence)


class MultiBankTests(unittest.TestCase):
    def test_reconciliation_transfer_and_reporting(self):
        p=fixture()
        r=generate(p)
        self.assertEqual(r['errors'],[])
        self.assertEqual(r['ledger_open'],D('1500'))
        self.assertEqual(r['ledger_end'],D('1800'))
        self.assertEqual(r['profit'],D('300'))
        self.assertEqual(r['cashflows']['Operating'],D('300'))
        self.assertEqual(r['cashflows']['Investing'],D('0'))
        self.assertEqual(r['cashflows']['Financing'],D('0'))
        self.assertEqual(r['balances']['1000'],D('1200'))
        self.assertEqual(r['balances']['1001'],D('600'))
        self.assertEqual([b['difference'] for b in r['bank_reconciliations']],[D('0'),D('0')])
        t=[e for e in r['entries'] if e['source']=='Bank transfer']
        self.assertEqual(len(t),2)
        self.assertEqual(len({e['journal_id'] for e in t}),1)
        self.assertEqual(sum(e['debit']-e['credit'] for e in t),D('0'))
        self.assertNotIn('1001',COA_MAP)
        self.assertTrue(management_pdf(r).startswith(b'%PDF'))
        self.assertTrue(financial_statements_pdf(r).startswith(b'%PDF'))
        self.assertTrue(xlsx_report(r).startswith(b'PK'))
        restored=Package.from_zip(p.to_zip())
        self.assertEqual(restored.bank[1]['transfer_id'],'T')
        self.assertEqual(generate(restored)['balances'],r['balances'])

    def test_offsetting_reconciliation_errors_do_not_cancel(self):
        p=fixture()
        p.config['bank_accounts'][0]['closing']='1300'
        p.config['bank_accounts'][1]['closing']='500'
        r=generate(p)
        self.assertEqual(r['bank_close'],r['ledger_end'])
        self.assertTrue(any('Bank 1000: closing statement' in e for e in r['errors']))
        self.assertTrue(any('Bank 1001: closing statement' in e for e in r['errors']))

    def test_unmatched_and_mismatched_transfers_block(self):
        for change in ('missing','amount','date','same_account','no_evidence'):
            with self.subTest(change=change):
                p=fixture()
                if change=='missing': p.bank.pop(2)
                elif change=='amount': p.bank[2]['deposit']='299'
                elif change=='date': p.bank[2]['date']='2025-06-02'
                elif change=='same_account': p.bank[2]['bank_account_code']='1000'
                elif change=='no_evidence': p.bank[2]['evidence_ref']=''
                r=generate(p)
                self.assertTrue(r['errors'])
                self.assertFalse(any(e['source']=='Bank transfer' for e in r['entries']))
                self.assertEqual(r['profit'],D('300'))

    def test_duplicate_reference_blocks_pair(self):
        p=fixture()
        p.bank.append(dict(p.bank[1]))
        r=generate(p)
        self.assertTrue(any('duplicate reference' in e for e in r['errors']))
        self.assertFalse(any(e['source']=='Bank transfer' for e in r['entries']))

    def test_unknown_account_and_unconfirmed_coverage(self):
        p=fixture()
        p.bank[0]['bank_account_code']='1099'
        p.config['bank_accounts'][0]['coverage_confirmed']=False
        r=generate(p)
        self.assertTrue(any('unregistered bank account' in e for e in r['errors']))
        self.assertTrue(any('full period coverage' in e for e in r['errors']))

    def test_missing_balance_and_foreign_currency(self):
        p=fixture()
        p.config['bank_accounts'][0]['opening']=''
        p.config['bank_accounts'][1]['currency']='USD'
        r=generate(p)
        self.assertTrue(r['bank_open_missing'])
        self.assertTrue(any('only SGD' in e for e in r['errors']))
        self.assertTrue(any('missing statement opening' in e for e in r['errors']))

    def test_manual_cash_and_missing_registry_block(self):
        p=fixture()
        p.journals.extend([dict(journal_id='BAD',date='2025-06-01',account_code=c,debit=d,credit=cr)
                    for c,d,cr in [('1000','10',''),('4000','','10')]])
        self.assertTrue(any('current-period cash' in e for e in generate(p)['errors']))
        p=fixture()
        del p.config['bank_accounts']
        self.assertTrue(any('explicit registry' in e for e in generate(p)['errors']))


if __name__ == '__main__':
    unittest.main()
