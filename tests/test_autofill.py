import unittest
from pathlib import Path
from engine.importers import inspect_document
from engine.autofill import (extract_acra_profile, extract_bank_statement, consolidate_statement_balances,
                             suggested_start, propose_bank_rows)

PATH=Path(__file__).resolve().parents[1]/'example_imports'/'smart_intake_demo'

def load(n):
    f=PATH/n
    return inspect_document(f.name,f.read_bytes())

class AutofillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acra=load('DEMO_ACRA_Profile_NOT_OFFICIAL.pdf')
        cls.h1=load('DEMO_Bank_2025_H1.pdf')
        cls.h2=load('DEMO_Bank_2025_H2.pdf')

    def test_acra_values_and_year_end(self):
        d=extract_acra_profile(self.acra)
        self.assertEqual(d['fields']['company_name'],'MERIDIAN SERVICES PTE. LTD.')
        self.assertEqual(d['fields']['uen'],'201688888A')
        self.assertEqual(d['fields']['fy_end'],'2025-12-31')
        self.assertEqual(d['fields']['registered_address'],'100 DEMONSTRATION ROAD #01-01 SINGAPORE 123456')
        self.assertEqual(suggested_start(d['fields']['fy_end'],d['fields']['incorporation_date']),'2025-01-01')

    def test_acra_missing_fye_is_not_invented(self):
        from engine.importers import SourceDocument
        doc=SourceDocument('profile.pdf','sha',[],text_excerpt='ACRA Business Profile (Company) of XYZ PTE. LTD. (201688888A)')
        d=extract_acra_profile(doc)
        self.assertNotIn('fy_end',d['fields'])
        self.assertTrue(any('not explicitly found' in w for w in d['warnings']))

    def test_acra_multiline_title(self):
        from engine.importers import SourceDocument
        doc=SourceDocument('profile.pdf','sha',[],text_excerpt='ACRA\nBusiness Profile (Company) of\nABC PRIVATE PTE. LTD.\n(201688888A)')
        d=extract_acra_profile(doc)
        self.assertEqual(d['fields']['company_name'],'ABC PRIVATE PTE. LTD.')

    def test_bank_detects_labelled_balances_and_masks_id(self):
        b=extract_bank_statement(self.h1)
        self.assertEqual(b['opening'],'1000.00')
        self.assertEqual(b['closing'],'1800.00')
        self.assertEqual(b['masked_account'],'••••7890')
        self.assertNotIn('1234567890',str(b))

    def test_two_bank_statements_contiguous(self):
        b=[extract_bank_statement(x) for x in (self.h2,self.h1)]
        r=consolidate_statement_balances(b,'2025-01-01','2025-12-31')
        self.assertTrue(r['ready'],r['errors'])
        self.assertEqual((r['opening'],r['closing']),('1000.00','2000.00'))

    def test_reject_gap(self):
        a=extract_bank_statement(self.h1);b=extract_bank_statement(self.h2)
        b['period_start']='2025-08-01'
        self.assertFalse(consolidate_statement_balances([a,b],'2025-01-01','2025-12-31')['ready'])

    def test_reject_different_account(self):
        a=extract_bank_statement(self.h1);b=extract_bank_statement(self.h2)
        b['account_id']='different'
        self.assertFalse(consolidate_statement_balances([a,b],'2025-01-01','2025-12-31')['ready'])

    def test_reject_mismatched_balances(self):
        a=extract_bank_statement(self.h1);b=extract_bank_statement(self.h2)
        b['opening']='1777.00'
        self.assertFalse(consolidate_statement_balances([a,b],'2025-01-01','2025-12-31')['ready'])

    def test_reject_missing_first_half(self):
        b=extract_bank_statement(self.h2)
        self.assertFalse(consolidate_statement_balances([b],'2025-01-01','2025-12-31')['ready'])

    def test_reject_fye_boundary_mismatch(self):
        a=extract_bank_statement(self.h1);b=extract_bank_statement(self.h2)
        self.assertFalse(consolidate_statement_balances([a,b],'2025-04-01','2025-12-31')['ready'])

    def test_autodetect_pdf_bank_rows(self):
        r,w=propose_bank_rows(self.h1)
        self.assertFalse(w)
        self.assertEqual(len(r),2)
        self.assertEqual(r[0]['deposit'],'1000.00')
        self.assertEqual(r[1]['withdrawal'],'200.00')
        self.assertTrue(all(x['account_code']=='9999' for x in r))

    def test_acra_is_not_bank_statement(self):
        self.assertFalse(extract_bank_statement(self.acra)['detected'])

    def test_scan_or_unlabelled_balance_never_invented(self):
        from engine.importers import SourceDocument
        doc=SourceDocument('bank.pdf','sha',[],text_excerpt='Example Bank Statement\nAmount 123.45\nSome text\nAccount Number: 9999999')
        result=extract_bank_statement(doc)
        self.assertIsNone(result['opening']);self.assertIsNone(result['closing'])

if __name__=='__main__':unittest.main()
