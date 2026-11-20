"""Tests for generated questions, client exports and saved answers."""
from pathlib import Path
import sys
import unittest
try: import streamlit
except ImportError:
    import types
    sys.modules['streamlit']=types.ModuleType('streamlit')

from engine.clarifications import build_questions, outstanding, questions_pdf, questions_csv
from engine.core import Package
from engine.importers import empty_company, inspect_document
from engine.autofill import extract_acra_profile, extract_bank_statement
from guided import _bank_batch

ROOT=Path(__file__).resolve().parents[1]/'example_imports'/'guided_demo'

class ClarificationTests(unittest.TestCase):
    def setUp(self):
        self.cfg=empty_company()
        self.pkg=Package(self.cfg)
        self.parsed=[]
        for file in sorted(ROOT.glob('*.pdf')):
            doc=inspect_document(file.name,file.read_bytes())
            self.parsed.append((doc,extract_acra_profile(doc),extract_bank_statement(doc)))

    def test_empty_client_asks_for_acra_year_bank_and_other_records(self):
        qs=build_questions(self.pkg,[])
        keys=[q['id'].split('-')[0] for q in qs]
        self.assertGreaterEqual(len(qs),9)
        combined=' '.join(q['question'] for q in qs).lower()
        self.assertIn('uen',combined)
        self.assertIn('financial year',combined)
        self.assertIn('bank statements',combined)
        self.assertIn('personal money',combined)

    def test_acra_and_bank_remove_unnecessary_requests(self):
        self.pkg.config.update(company_name='GUIDED DEMO PTE. LTD.',uen='202588888A',fy_start='2025-01-01',fy_end='2025-12-31',fy_confirmed=True,
                        bank_balances_confirmed=True,bank_statement_opening='0.00',bank_statement_closing='1230.00',acra_source={'filename':'demo.pdf'})
        qs=build_questions(self.pkg,self.parsed,_bank_batch(self.parsed,self.pkg.config,[]))
        combined=' '.join(q['question'] for q in qs)
        self.assertNotIn('UEN?',combined)
        self.assertNotIn('financial year start',combined)
        self.assertNotIn('bank statements for the financial year?',combined)
        self.assertTrue(any('customer' in q['question'].lower() for q in qs))

    def test_missing_rows_ask_source_specific_question(self):
        self.pkg.bank=[dict(date='2025-01-03',description='Customer ABC payment',deposit='350.00',withdrawal='',account_code='9999',reference='SGT10001')]
        qs=build_questions(self.pkg)
        self.assertTrue(any('money received' in q['question'] for q in qs))
        self.assertTrue(any(q['priority']=='Required' for q in qs))

    def test_resolved_question_not_shown_on_client_pdf(self):
        qs=build_questions(self.pkg)
        self.assertTrue(qs)
        response={qs[0]['id']:{'status':'Answered','answer':'ACRA pdf reviewed'}}
        open_q=outstanding(qs,response)
        self.assertEqual(len(open_q),len(qs)-1)
        pdf=questions_pdf('TEST SAMPLE PTE. LTD.',qs,response)
        self.assertTrue(pdf.startswith(b'%PDF-'))
        data=questions_csv(qs,response,only_open=False)
        self.assertIn(b'ACRA pdf reviewed',data)
        self.assertEqual(len(data.decode('utf-8-sig').splitlines()),len(qs)+1)

    def test_status_answers_survive_workspace_zip(self):
        qs=build_questions(self.pkg)
        self.pkg.config['clarification_answers']={qs[0]['id']:{'status':'Answered','answer':'From director email'}}
        restored=Package.from_zip(self.pkg.to_zip())
        self.assertEqual(restored.config['clarification_answers'][qs[0]['id']]['answer'],'From director email')

    def test_gap_and_mismatch_generate_questions(self):
        self.pkg.config.update(company_name='TEST PTE LTD',uen='202600000A',fy_confirmed=True,fy_start='2025-01-01',fy_end='2025-12-31')
        r=_bank_batch(self.parsed,self.pkg.config,[])
        r['mismatches']=['Test statement: S$3.00 difference']
        qs=build_questions(self.pkg,self.parsed,r)
        self.assertTrue(any('not agree' in q['question'] for q in qs))

if __name__=='__main__':unittest.main()
