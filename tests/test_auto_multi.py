"""Combined Auto/multi-bank acceptance; all sources and approvals are synthetic."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import json
import unittest
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest
from engine.core import generate,Package
from engine.auto import analyse,approve_bank,bank_proposal
from engine.auto_classification import bank_revision,apply_categories,revert_categories,validate_proposals
from engine.auto_reports import frozen_report,export_bundle
from engine.auto_multi import source_readiness
from engine.bank_intake import analyse_documents,approve_account,staged_rows,approve_import,suggest_transfers,approve_transfer
from test_bank_intake import package,document
from test_multi_bank import fixture

ROOT=Path(__file__).resolve().parents[1]


def sources():
    return [document(name='bank-a.csv',number='1111110001',transactions=[['2025-06-01','Customer receipt','R1','500.00',''],['2025-06-01','Own account transfer','T1','','300.00']]),
            document(name='bank-b.csv',number='2222220001',opening='500.00',closing='600.00',transactions=[['2025-06-01','Own account transfer','T2','300.00',''],['2025-06-01','Rental','P1','','200.00']])]


def reviewed():
    p=package();files=sources();b=analyse_documents(files,p.config)
    for group in b['groups']:
        code='1000' if group['sources'][0]['name']=='bank-a.csv' else '1001'
        assert approve_account(p,b,group['key'],code,group['revision'],'Synthetic reviewer','Original archive',True)
        proposed=staged_rows(p,b,group['key']);assert approve_import(p,b,group['key'],proposed['revision'],'Synthetic reviewer','Original archive',True)
    p.journals=fixture().journals
    choice=suggest_transfers(p)[0];assert approve_transfer(p,choice['id'],'Synthetic reviewer','Both originals',True)
    codes=['TRANSFER' if r.get('transfer_id') else '4000' if r['deposit'] else '5200' for r in p.bank]
    assert apply_categories(p,bank_revision(p.bank),codes)
    p.config['other_records_confirmed']=True
    return p,files


class AutoMultiEngineTests(unittest.TestCase):
    def test_combined_ledger_snapshot_reports_and_restore(self):
        p,files=reviewed();a=analyse(files,p.config);a['bank_intake']=analyse_documents(files,p.config)
        self.assertTrue(source_readiness(p.config,a['bank_intake']))
        result,meta=frozen_report(p,a,[]);self.assertEqual(result['errors'],[])
        self.assertEqual(meta['status'],'DRAFT - REVIEW REQUIRED');self.assertFalse(meta['authorised'])
        self.assertEqual(result['ledger_end'],1800);self.assertEqual(result['profit'],300)
        self.assertEqual(result['cashflows']['Operating'],300)
        restored=Package.from_zip(p.to_zip());again,meta2=frozen_report(restored,a,[])
        self.assertEqual(meta['snapshot'],meta2['snapshot'])
        self.assertEqual(result['entries'],again['entries'])
        p.bank[0]['description']='Changed after frozen snapshot'
        with ZipFile(BytesIO(export_bundle(result,meta))) as archive:
            manifest=json.loads(archive.read('Report_manifest.json'))
            self.assertEqual(manifest['snapshot'],meta['snapshot']);self.assertFalse(manifest['authorised'])
            workbook=load_workbook(BytesIO(archive.read('Financial_Workpapers_PROVISIONAL.xlsx')),data_only=True)
            self.assertEqual(workbook['Cash Flows']['B7'].value,1800)
            self.assertIn('Bank Accounts',workbook.sheetnames);self.assertIn('Internal Transfers',workbook.sheetnames)
            self.assertIn('Report snapshot',workbook.sheetnames)
            self.assertNotIn('Changed after frozen snapshot',str(list(workbook['Source Bank'].values)))

    def test_legacy_import_cannot_bypass_multi_bank_controls(self):
        p=package();files=sources();a=analyse(files,p.config);proposal=bank_proposal(a,p.config,[])
        before=deepcopy(p.config)
        self.assertTrue(any('legacy import is blocked' in e for e in proposal['errors']))
        self.assertFalse(approve_bank(p,a,proposal['id'],True));self.assertEqual(p.bank,[]);self.assertEqual(before,p.config)
        legacy=package();del legacy.config['bank_accounts']
        foreign=analyse([document(bank='CIMB',currency='USD')],legacy.config)
        self.assertTrue(any('only SGD statement currency' in e for e in bank_proposal(foreign,legacy.config,[])['errors']))

    def test_account_source_and_transfer_links_bound_to_category_approval(self):
        p,files=reviewed();revision=bank_revision(p.bank);before=deepcopy(p.bank)
        codes=[r['account_code'] for r in p.bank]
        idx=next(i for i,r in enumerate(p.bank) if r.get('transfer_id'));codes[idx]='4000'
        self.assertFalse(apply_categories(p,revision,codes));self.assertEqual(p.bank,before)
        row=p.bank[0];row['bank_account_code']='1099'
        self.assertNotEqual(revision,bank_revision(p.bank))
        self.assertFalse(revert_categories(p,p.config['auto_category_history'][-1]['id']))
        p.bank=before;idx=next(i for i,r in enumerate(p.bank) if r.get('transfer_id'))
        with self.assertRaises(ValueError):validate_proposals(p.bank,dict(ledger_revision=bank_revision(p.bank),suggestions=[dict(row=idx,account_code='4000',confidence=1,reason='Not evidence',source_ref=p.bank[idx]['evidence_ref'])]))

    def test_missing_sources_or_extra_account_do_not_clear_readiness_and_errors_block_export(self):
        p,files=reviewed();a=analyse(files,p.config);a['bank_intake']=analyse_documents(files,p.config)
        missing=deepcopy(a);missing['bank_intake']=analyse_documents(files[:1],p.config)
        self.assertFalse(source_readiness(p.config,missing['bank_intake']))
        _,meta=frozen_report(p,missing,[]);self.assertEqual(meta['status'],'PROVISIONAL - INCOMPLETE RECORDS')
        p.config['bank_accounts'][0]['closing']='1300.00'
        result,meta=frozen_report(p,a,[]);self.assertTrue(result['errors'])
        with self.assertRaises(ValueError):export_bundle(result,meta)


class AutoMultiUITests(unittest.TestCase):
    def app(self,p=None,files=None):
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        if p is not None:at.session_state['pkg']=p
        if files is not None:at.session_state['guided_files']=files
        return at.run()

    def test_new_sources_enter_account_review_without_posting(self):
        p=package();del p.config['bank_accounts']
        at=self.app(p,sources());self.assertFalse(at.exception)
        self.assertEqual(at.session_state['app_mode'],'Auto')
        self.assertEqual(at.session_state['pkg'].bank,[])
        at.button(key='auto_enable_multi').click().run();self.assertFalse(at.exception)
        self.assertTrue(any(h.value=='Otto Auto' for h in at.header))
        self.assertEqual(at.session_state['pkg'].config['bank_accounts'],[])
        self.assertEqual(at.session_state['pkg'].bank,[])
        self.assertFalse(any(b.key=='auto_import' for b in at.button))
        self.assertEqual(len([b for b in at.button if b.label=='Approve account identity and coverage']),2)
        self.assertTrue(at.button(key='auto_generate').disabled)

    def test_auto_and_detailed_views_share_restored_accounts_without_source_loss(self):
        p,files=reviewed();at=self.app(Package.from_zip(p.to_zip()),files)
        self.assertFalse(at.exception);self.assertEqual(at.session_state['app_mode'],'Auto')
        before=deepcopy(at.session_state['pkg'].bank)
        self.assertFalse(at.button(key='auto_generate').disabled)
        at.button(key='auto_generate').click().run();self.assertFalse(at.exception)
        self.assertIn('auto_report_bundle',at.session_state)
        at.selectbox(key='workspace_view').select('Advanced').run();self.assertFalse(at.exception)
        self.assertEqual(at.session_state['pkg'].bank,before)
        at.selectbox(key='workspace_view').select('Auto').run();self.assertFalse(at.exception)
        self.assertTrue(any(h.value=='Otto Auto' for h in at.header));self.assertEqual(at.session_state['pkg'].bank,before)
        self.assertTrue(any('1.3.1' in str(m.value) for m in at.markdown))

    def test_saved_manual_pilot_opens_in_auto_and_stale_edits_block_bundle(self):
        p=fixture();at=self.app(Package.from_zip(p.to_zip()))
        self.assertFalse(at.exception);self.assertTrue(any(h.value=='Otto Auto' for h in at.header))
        self.assertTrue(any('re-upload' in str(i.value).lower() or 'current originals' in str(i.value).lower() for i in list(at.info)+list(at.warning)) or any('Recheck current bank sources' in str(d.value) for d in at.dataframe))
        at.session_state['pkg'].bank[0]['deposit']='501'
        at.run();self.assertFalse(at.exception);self.assertTrue(at.button(key='auto_generate').disabled)


    def test_new_company_clears_staged_ai_and_frozen_bundle(self):
        at=self.app();at.session_state['auto_ai_proposals']={'revision':'old','rows':{}}
        at.session_state['auto_report_bundle']={'revision':'old','data':b'old client'}
        next(b for b in at.button if b.label=='＋ Start a new company').click().run()
        self.assertFalse(at.exception)
        self.assertNotIn('auto_ai_proposals',at.session_state)
        self.assertNotIn('auto_report_bundle',at.session_state)
        self.assertEqual(at.session_state['app_mode'],'Auto')


    def test_unsupported_bank_never_falls_back_to_legacy_auto_posting(self):
        p=package();del p.config['bank_accounts']
        at=self.app(p,[document(bank='CIMB',currency='USD')])
        self.assertFalse(at.exception)
        self.assertTrue(any(b.key=='auto_enable_multi' for b in at.button))
        self.assertFalse(any(b.key=='auto_import' for b in at.button))
        at.button(key='auto_enable_multi').click().run()
        self.assertFalse(at.exception);self.assertEqual(at.session_state['pkg'].bank,[])
        self.assertTrue(at.button(key='auto_generate').disabled)


    def test_source_approval_checkbox_resets_when_reporting_context_changes(self):
        at=self.app(package(),sources());self.assertFalse(at.exception)
        checkbox=next(c for c in at.checkbox if c.label.startswith('I checked the originals'))
        checkbox.check().run();self.assertFalse(at.exception)
        self.assertTrue(any(c.value for c in at.checkbox if c.label.startswith('I checked the originals')))
        at.session_state['pkg'].config['fy_end']='2025-11-30'
        at.run();self.assertFalse(at.exception)
        self.assertTrue(all(not c.value for c in at.checkbox if c.label.startswith('I checked the originals')))
        self.assertEqual(at.session_state['pkg'].bank,[])


    def test_document_drop_box_is_in_sidebar_not_the_main_review_page(self):
        at=self.app();self.assertFalse(at.exception)
        sidebar=[w for w in at.sidebar.get('file_uploader') if w.label=='Drop bank statements, bookkeeping records and report references here']
        main=[w for w in at.main.get('file_uploader') if w.label=='Drop bank statements, bookkeeping records and report references here']
        self.assertEqual(len(sidebar),1);self.assertEqual(main,[])
        p,files=reviewed();at=self.app(p,files);self.assertFalse(at.exception)
        self.assertEqual(len([w for w in at.sidebar.get('file_uploader') if w.label=='Drop bank statements, bookkeeping records and report references here']),1)
        self.assertFalse(any('Bank statements — PDF' in w.label for w in at.main.get('file_uploader')))
        self.assertEqual(generate(at.session_state['pkg'])['ledger_end'],1800)
