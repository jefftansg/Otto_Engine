"""Synthetic uploaded-source review, actionable validation and saved preparation notes."""
from copy import deepcopy
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest
from engine.bank_intake import (analyse_documents,approve_account,account_approval_errors,uploaded_review_sources,
    staged_rows,approve_import,save_account_review_draft,review_recorded_rows,validate_managed_account)
from engine.core import Package
from test_bank_intake import package,document
from test_ocbc_daily import source

ROOT=Path(__file__).resolve().parents[1]

class SourceEvidenceTests(unittest.TestCase):
    def setup_review(self):
        p=package();f=document();a=analyse_documents([f],p.config);return p,f,a,a['groups'][0]

    def test_uploaded_originals_supply_evidence_for_account_and_transaction_review(self):
        p,f,a,g=self.setup_review()
        self.assertTrue(approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','',True))
        meta=p.config['bank_accounts'][0];record=meta['coverage_review']
        self.assertIn(f['name'],record['evidence']);self.assertIn(f['sha256'],record['evidence'])
        self.assertEqual(record['sources'],[dict(name=f['name'],sha256=f['sha256'])])
        self.assertEqual(p.bank,[])
        proposed=staged_rows(p,a,g['key'])
        self.assertTrue(approve_import(p,a,g['key'],proposed['revision'],'Reviewer','',True))
        self.assertIn(f['sha256'],p.config['bank_accounts'][0]['transactions_review']['evidence'])
        restored=Package.from_zip(p.to_zip());self.assertEqual(validate_managed_account(restored.config['bank_accounts'][0],restored.config),[])
        self.assertEqual(restored.config['bank_accounts'][0]['coverage_review'],record)
        self.assertFalse(approve_import(p,a,g['key'],proposed['revision'],'Reviewer','',True))

    def test_missing_or_wrong_originals_cannot_supply_automatic_evidence(self):
        for wrong in (False,True):
            p,f,a,g=self.setup_review()
            if wrong:a['documents'][f['sha256']].sha256='0'*64
            else:a['documents']={}
            before=deepcopy(p.config);self.assertEqual(uploaded_review_sources(a,g['key']),[])
            reasons=account_approval_errors(p,a,g['key'],'1000',g['revision'],'Reviewer','',True)
            self.assertTrue(any('Original statements are unavailable' in r for r in reasons))
            self.assertFalse(approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','',True));self.assertEqual(p.config,before)

    def test_explicit_manual_evidence_remains_supported(self):
        p,f,a,g=self.setup_review();a['documents']={}
        self.assertTrue(approve_account(p,a,g['key'],'1000',g['revision'],'Reviewer','Archive and manually checked source',True))
        self.assertFalse(review_recorded_rows(p,'1000','Reviewer','',True))

    def test_specific_setup_reviewer_checkbox_stale_and_mapping_rejections_do_not_mutate(self):
        p,f,a,g=self.setup_review();before=deepcopy(p.config)
        reasons=account_approval_errors(p,a,g['key'],'999','stale','','',False)
        self.assertTrue(any('reviewer name' in e for e in reasons));self.assertTrue(any('Confirm that' in e for e in reasons))
        self.assertTrue(any('statement set changed' in e for e in reasons));self.assertTrue(any('1000 to 1099' in e for e in reasons))
        self.assertEqual(p.config,before)
        p.config['fy_confirmed']=False
        self.assertTrue(any('reporting dates' in e for e in account_approval_errors(p,a,g['key'],'1000',g['revision'],'R','',True)))
        p,f,a,g=self.setup_review();p.config['bank_accounts']=[dict(code='1000',account_key='other')]
        self.assertTrue(any('different bank account' in e for e in account_approval_errors(p,a,g['key'],'1000',g['revision'],'R','',True)))

    def test_save_incomplete_review_notes_restores_without_approval_or_posting(self):
        p,f,a,g=self.setup_review();p.config['bank_accounts']=[]
        self.assertTrue(save_account_review_draft(p,a,g['key'],'1000','','Waiting for missing month'))
        restored=Package.from_zip(p.to_zip())
        self.assertEqual(restored.config['bank_review_drafts'][g['key']]['note'],'Waiting for missing month')
        self.assertEqual(restored.config['bank_accounts'],[]);self.assertEqual(restored.bank,[])
        self.assertEqual(restored.journals,[])
        before=deepcopy(p.config);p.config['uen']='CHANGED';changed=deepcopy(p.config)
        self.assertFalse(save_account_review_draft(p,a,g['key'],'1000','','stale'));self.assertEqual(p.config,changed)

    def test_late_posting_is_allowed_inside_the_confirmed_financial_year(self):
        f,doc=source();doc.text_excerpt=doc.text_excerpt.replace('31 Jan 2026 REF3','01 Feb 2026 REF3')
        p=package();p.config.update(company_name='EXAMPLE WORKS PTE. LTD.',fy_start='2026-01-01',fy_end='2026-01-31')
        a=analyse_documents([f],p.config,lambda n,b:doc);g=a['groups'][0]
        self.assertTrue(approve_account(p,a,g['key'],'1000',g['revision'],'R','',True))
        proposed=staged_rows(p,a,g['key'])
        self.assertEqual(len(proposed['rows']),3)
        self.assertTrue(any('outside the confirmed financial year' in e for e in proposed['errors']))
        self.assertFalse(approve_import(p,a,g['key'],proposed['revision'],'R','',True))
        self.assertEqual(p.bank,[])


class SourceReviewUITests(unittest.TestCase):
    def app(self):
        p=package();at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        at.session_state['pkg']=p;at.session_state['guided_files']=[document()];return at.run()

    def test_empty_optional_note_allows_explicit_account_approval(self):
        at=self.app();next(x for x in at.text_input if x.label=='Reviewer name').set_value('Reviewer')
        next(x for x in at.checkbox if x.label.startswith('I checked the originals:')).check()
        next(x for x in at.button if x.label=='Approve account identity and coverage').click().run()
        self.assertFalse(at.exception);self.assertEqual(len(at.session_state['pkg'].config['bank_accounts']),1)
        self.assertEqual(at.session_state['pkg'].bank,[])
        self.assertTrue(any(x.label=='Transaction review note (optional for uploaded statements)' for x in at.text_input))

    def test_missing_reviewer_has_one_specific_error_and_notes_can_be_saved(self):
        at=self.app();next(x for x in at.checkbox if x.label.startswith('I checked the originals:')).check()
        next(x for x in at.button if x.label=='Approve account identity and coverage').click().run()
        self.assertFalse(at.exception)
        self.assertIn('Enter the reviewer name.',[e.value for e in at.error])
        self.assertFalse(any('Confirm company/reporting dates first' in e.value for e in at.error))
        next(x for x in at.text_input if x.label=='Review note (optional for uploaded statements)').set_value('Will review later')
        next(x for x in at.button if x.label=='Save review notes and continue').click().run()
        self.assertFalse(at.exception);self.assertEqual(at.session_state['pkg'].config['bank_accounts'],[])
        self.assertTrue(at.session_state['pkg'].config['bank_review_drafts'])
