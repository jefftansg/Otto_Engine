"""Next-action routes, safeguards, and same-ledger behaviour for Version 1.2.3."""
from pathlib import Path
import unittest
import sys
import types
try: import streamlit
except ImportError: sys.modules['streamlit']=types.ModuleType('streamlit')
from engine.attention import build_attention, counts, ADVANCED_PAGES
from engine.clarifications import build_questions, outstanding
from engine.core import Package, generate
from engine.importers import empty_company, inspect_document
from engine.autofill import extract_acra_profile, extract_bank_statement
from guided import _bank_batch

ROOT=Path(__file__).resolve().parents[1]/'example_imports'/'guided_demo'


def config():
    c=empty_company()
    c.update(company_name='GUIDED DEMO PTE. LTD.',uen='202588888A',
             fy_start='2025-01-01',fy_end='2025-12-31',fy_confirmed=True,
             bank_statement_opening='0.00',bank_statement_closing='1230.00',
             bank_balances_confirmed=True)
    return c


def parsed():
    files=[]
    for file in sorted(ROOT.glob('*.pdf')):
        doc=inspect_document(file.name,file.read_bytes())
        files.append((doc,extract_acra_profile(doc),extract_bank_statement(doc)))
    return files


class AttentionTests(unittest.TestCase):
    def test_blank_company_routes_to_guided_setup(self):
        p=Package(empty_company())
        items=build_attention(p)
        issue=next(x for x in items if x['id']=='company-setup')
        self.assertEqual(issue['guided_stage'],0)
        self.assertEqual(issue['advanced_page'],0)
        self.assertEqual(issue['severity'],'Required')

    def test_uncoded_receipts_and_payments_routes_to_bank_review(self):
        p=Package(config(), bank=[
            dict(date='2025-01-08',description='CLIENT TRANSFER',reference='A',deposit='100',withdrawal='',account_code='9999'),
            dict(date='2025-01-09',description='SUBSCRIPTION',reference='B',deposit='',withdrawal='15',account_code=''),
            dict(date='2025-01-10',description='BANK FEE',reference='C',deposit='',withdrawal='5',account_code='5100')])
        items=build_attention(p)
        issue=next(x for x in items if x['id']=='bank-uncoded')
        self.assertEqual((issue['affected'],issue['guided_stage'],issue['advanced_page']),(2,2,2))
        self.assertEqual(counts(items)['transactions'],2)

    def test_director_claims_and_receivables_issue_routes(self):
        c=config();c['simple_questions']={'director_expenses':'Yes','receivables':'Yes'}
        items=build_attention(Package(c))
        dest={x['id']:x['advanced_page'] for x in items}
        self.assertEqual(dest['director-records'],3)
        self.assertEqual(dest['unpaid-customer-invoices'],5)

    def test_balanced_manual_journal_error_is_routed_to_editor(self):
        p=Package(config(),journals=[
            dict(journal_id='FIX01',date='2025-01-01',account_code='5600',debit='123',credit='',description='Testing',evidence_ref='')])
        r=generate(p)
        items=build_attention(p,result=r)
        self.assertTrue(any(x['advanced_page']==4 and 'journal' in x['title'] for x in items))

    def test_saved_answers_do_not_erase_real_ledger_errors(self):
        c=config();p=Package(c,bank=[dict(date='2025-01-02',description='CLIENT RECEIPT',
                         reference='REF0001',deposit='100',withdrawal='',account_code='9999')])
        all_q=build_questions(p)
        c['clarification_answers']={q['id']:{'status':'Answered','answer':'Director replied'} for q in all_q}
        pending=outstanding(all_q,c['clarification_answers'])
        self.assertEqual(pending,[])
        items=build_attention(p,pending,generate(p))
        self.assertTrue(any(x['id']=='bank-uncoded' for x in items))

    def test_bank_rows_already_imported_not_suggested_again(self):
        c=config();d=parsed();batch=_bank_batch(d,c,[])
        imported=_bank_batch(d,c,batch['rows'])
        self.assertTrue(imported['already_imported'])
        self.assertEqual(len(imported['duplicates']),len(batch['rows']))
        p=Package(c,bank=batch['rows'])
        qs=build_questions(p,d,imported)
        self.assertFalse(any('duplicates or separate' in q['question'] for q in qs))

    def test_both_modes_work_with_exactly_same_workspace(self):
        c=config();d=parsed();batch=_bank_batch(d,c,[])
        for row,code in zip(batch['rows'],['3100','4000','5400','5100']):row['account_code']=code
        p=Package(c,bank=batch['rows'])
        before=generate(p)
        self.assertFalse(before['errors'])
        # An advanced correction changes the existing package, not a copy.
        p.bank[2]['account_code']='5600'
        after=generate(p)
        self.assertFalse(after['errors'])
        self.assertEqual(str(after['profit']),str(before['profit']))
        self.assertEqual(len(after['entries']),len(before['entries']))
        saved=Package.from_zip(p.to_zip())
        self.assertEqual(saved.bank[2]['account_code'],'5600')

    def test_advanced_destination_exists(self):
        for page in (0,2,3,4,5,7):self.assertIsInstance(ADVANCED_PAGES[page],str)

if __name__=='__main__':unittest.main()
