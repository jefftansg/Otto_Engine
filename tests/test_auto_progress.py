"""Synthetic sidebar progress, setup transition and source removal regressions."""
from copy import deepcopy
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest
from engine.auto import analyse
from engine.auto_progress import workflow_progress
from engine.bank_intake import analyse_documents
from engine.intake_review import upload_id
from test_bank_intake import package,document
from test_auto_multi import reviewed,sources

ROOT=Path(__file__).resolve().parents[1]

class ProgressTests(unittest.TestCase):
    def test_empty_and_upload_stages_are_read_only(self):
        p=package();p.config.update(company_name='',uen='',fy_confirmed=False)
        before=deepcopy(p.config)
        empty=workflow_progress(p,[])
        self.assertEqual(empty['completed'],0);self.assertEqual(empty['stages'][0]['status'],'Current')
        uploaded=workflow_progress(p,sources())
        self.assertEqual(uploaded['current'],'Confirm company');self.assertEqual(uploaded['completed'],1)
        self.assertEqual(p.config,before)

    def test_reviewed_sources_reconciliation_and_bundle_rollbacks(self):
        p,files=reviewed();a=analyse(files,p.config);b=analyse_documents(files,p.config)
        state=workflow_progress(p,files,a,b)
        self.assertEqual(state['completed'],4);self.assertEqual(state['current'],'Generate draft reports')
        self.assertEqual(workflow_progress(p,files,a,b,bundle_current=True)['completed'],5)
        missing=workflow_progress(p,files[:1],a,analyse_documents(files[:1],p.config),bundle_current=True)
        self.assertEqual(missing['current'],'Review bank accounts');self.assertEqual(missing['completed'],2)
        p.bank[0]['deposit']='501.00'
        broken=workflow_progress(p,files,a,b,bundle_current=True)
        self.assertEqual(broken['current'],'Reconcile records');self.assertFalse(broken['stages'][-1]['done'])

class SidebarUITests(unittest.TestCase):
    def app(self,p,files):
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        at.session_state['pkg']=p;at.session_state['guided_files']=files
        return at.run()

    def setup_fields(self,at,uen='202600001A',verified=True):
        values={'Company name':'ACME SERVICES PTE. LTD.','UEN':uen,'Reporting period starts (YYYY-MM-DD)':'2025-01-01','Reporting period ends (YYYY-MM-DD)':'2025-12-31'}
        for field in at.text_input:
            if field.label in values:field.set_value(values[field.label])
        next(c for c in at.checkbox if c.label=='I reviewed the company identity and reporting dates against its records').set_value(verified)
        next(b for b in at.button if b.label=='Confirm setup').click().run()

    def test_confirmation_advances_without_posting_and_sidebar_is_present(self):
        p=package();del p.config['bank_accounts'];p.config.update(fy_confirmed=False)
        at=self.app(p,sources());self.assertFalse(at.exception)
        self.assertTrue(any('Progress ·' in str(x.value) for x in at.sidebar.markdown))
        self.assertTrue(any(e.label=='Remove uploaded files' for e in at.sidebar.expander))
        self.setup_fields(at);self.assertFalse(at.exception)
        current=at.session_state['pkg'];self.assertTrue(current.config['fy_confirmed'])
        self.assertEqual(current.config['bank_accounts'],[]);self.assertEqual(current.bank,[]);self.assertEqual(current.journals,[])
        self.assertTrue(any('Company setup confirmed' in s.value for s in at.success))
        self.assertEqual(len([b for b in at.button if b.label=='Approve account identity and coverage']),2)
        self.assertTrue(any('Now: Review bank accounts' in str(x.value) for x in at.sidebar.markdown))

    def test_unverified_or_missing_identity_does_not_advance(self):
        for uen,verified in [('',True),('202600001A',False)]:
            p=package();del p.config['bank_accounts'];p.config.update(fy_confirmed=False)
            at=self.app(p,sources());before=deepcopy(at.session_state['pkg'].config)
            self.setup_fields(at,uen,verified);self.assertFalse(at.exception)
            self.assertTrue(at.error);self.assertEqual(at.session_state['pkg'].config,before)

    def test_sidebar_remove_before_setup_and_last_file_notice(self):
        p=package();del p.config['bank_accounts'];p.config['fy_confirmed']=False
        files=[document()];at=self.app(p,files)
        at.session_state['auto_report_bundle']={'revision':'old','data':b'old'}
        at.session_state['auto_ai_proposals']={'rows':{}}
        next(m for m in at.sidebar.multiselect if m.label=='Select uploaded files to remove').set_value([upload_id(files[0])])
        at.button(key='auto_remove_selected').click().run();self.assertFalse(at.exception)
        self.assertEqual(at.session_state['guided_files'],[])
        self.assertGreater(at.session_state['guided_upload_version'],0)
        self.assertNotIn('auto_report_bundle',at.session_state);self.assertNotIn('auto_ai_proposals',at.session_state)
        self.assertTrue(any('uploaded file(s) deleted' in s.value for s in at.sidebar.success))
        at.run();self.assertEqual(at.session_state['guided_files'],[])

    def test_same_named_source_removal_preserves_accounting_and_history(self):
        p,files=reviewed();files=[dict(f,name='same.csv') for f in files]
        at=self.app(p,files);before=deepcopy([p.bank,p.journals,p.evidence,p.config['bank_accounts']])
        next(m for m in at.sidebar.multiselect if m.label=='Select uploaded files to remove').set_value([upload_id(files[0])])
        at.button(key='auto_remove_selected').click().run();self.assertFalse(at.exception)
        saved=at.session_state['pkg'];self.assertEqual(at.session_state['guided_files'],files[1:])
        self.assertEqual(before,[saved.bank,saved.journals,saved.evidence,saved.config['bank_accounts']])
        self.assertTrue(any('Now: Review bank accounts' in str(x.value) for x in at.sidebar.markdown))

    def test_unchanged_legacy_setup_keeps_balance_confirmation(self):
        p=package();del p.config['bank_accounts'];p.config['bank_balances_confirmed']=True
        p.evidence=[{'evidence_ref':'synthetic-retained'}]
        at=self.app(p,sources());self.setup_fields(at);self.assertFalse(at.exception)
        self.assertTrue(at.session_state['pkg'].config['bank_balances_confirmed'])
        self.assertNotIn('bank_accounts',at.session_state['pkg'].config)
