"""Synthetic acceptance cases for local Otto Auto; no client files or data."""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import unittest
from zipfile import ZipFile
from streamlit.testing.v1 import AppTest
from engine.auto import analyse,coverage,bank_proposal,approve_bank,digest
from engine.auto_classification import validate_proposals,bank_revision
from engine.auto_reports import frozen_report,export_bundle
from engine.importers import SourceDocument,SourceTable,empty_company
from engine.core import Package,generate

ROOT=Path(__file__).resolve().parents[1]
CFG=dict(company_name='EXAMPLE WORKS PTE. LTD.',uen='202600001A',fy_start='2025-12-01',fy_end='2026-11-30',fy_confirmed=True)


def source(name='statement.pdf',text=None,start='1 DEC 2025',end='30 NOV 2026',opening='0.00',closing='100.00'):
    text=text or f'OCBC Bank\nSTATEMENT OF ACCOUNT\nCompany Name: EXAMPLE WORKS PTE. LTD.\nAccount No. 1234567890\nBUSINESS GROWTH ACCOUNT {start} TO {end}\nBALANCE B/F {opening}\nBALANCE C/F {closing}'
    payload=text.encode()
    item=dict(name=name,bytes=payload,sha256=sha256(payload).hexdigest())
    table=SourceTable('Transactions',[['Date','Description','Deposit','Withdrawal'],['2025-12-02','Owner funding','100.00','']])
    doc=SourceDocument(name,item['sha256'],[table],text)
    return item,doc


def analysis(pairs,cfg=None):
    mapping={i['name']:d for i,d in pairs}
    return analyse([i for i,d in pairs],cfg or CFG,lambda name,payload:mapping[name])


class AutoEngineTests(unittest.TestCase):
    def test_analysis_is_order_independent_deduplicates_and_never_posts(self):
        item,doc=source()
        copy=dict(item,name='copy.pdf');copied=deepcopy(doc);copied.name='copy.pdf'
        cfg=deepcopy(CFG)
        a=analysis([(item,doc),(copy,copied)],cfg)
        self.assertEqual(len(a['accounts']),1)
        self.assertEqual(a['inventory'][1]['status'],'Excluded duplicate')
        self.assertEqual(a['accounts'][0]['coverage']['covered'],12)
        self.assertEqual(cfg,CFG)
        self.assertEqual(a['proposals']['company_name']['sha256'],item['sha256'])

    def test_missing_fields_remain_unknown_not_guessed_from_filename(self):
        item,doc=source('Company_2026_UEN999.pdf',text='Unlabelled record')
        a=analysis([(item,doc)])
        self.assertEqual(a['proposals'],{})
        self.assertEqual(a['accounts'],[])

    def test_eleven_months_and_previous_period_opening(self):
        prior,doc=source('prior.pdf',start='1 NOV 2025',end='30 NOV 2025',opening='80.00',closing='90.00')
        current,doc2=source('current.pdf',start='1 DEC 2025',end='31 OCT 2026',opening='90.00',closing='190.00')
        a=analysis([(current,doc2),(prior,doc)])
        c=a['accounts'][0]['coverage']
        self.assertEqual((c['covered'],c['expected']),(11,12))
        self.assertEqual(c['months'][-1]['status'],'Missing / incomplete')
        self.assertEqual(c['opening'],'90.00')
        self.assertEqual(len(c['opening_sources']),2)
        self.assertFalse(c['balances']['ready'])
        self.assertEqual(c['latest_closing']['date'],'2026-10-31')

    def test_fictional_statement_cannot_complete_coverage(self):
        old,doc=source('real.pdf',end='31 OCT 2026')
        demo,demo_doc=source('Fictional_November.pdf',start='1 NOV 2026',end='30 NOV 2026')
        a=analysis([(old,doc),(demo,demo_doc)])
        self.assertTrue(a['inventory'][1]['demo'])
        self.assertEqual(a['accounts'][0]['coverage']['covered'],11)
        self.assertFalse(a['accounts'][0]['coverage']['balances']['ready'])

    def test_cross_company_source_is_excluded_and_cannot_post(self):
        item,doc=source()
        doc.text_excerpt=doc.text_excerpt.replace('EXAMPLE WORKS','OTHER WORKS')
        item['bytes']=doc.text_excerpt.encode();item['sha256']=sha256(item['bytes']).hexdigest();doc.sha256=item['sha256']
        a=analysis([(item,doc)])
        self.assertEqual(a['inventory'][0]['status'],'Excluded company mismatch')
        self.assertTrue(bank_proposal(a,CFG,[])['errors'])

    def test_approve_exact_proposal_once_rejects_without_mutation(self):
        item,doc=source();a=analysis([(item,doc)])
        p=Package(dict(empty_company(),**CFG));proposal=bank_proposal(a,p.config,p.bank)
        self.assertEqual(proposal['errors'],[])
        before=deepcopy(p.config)
        self.assertFalse(approve_bank(p,a,proposal['id'],False))
        self.assertFalse(approve_bank(p,a,'stale',True))
        self.assertEqual(p.bank,[]);self.assertEqual(p.config,before)
        self.assertTrue(approve_bank(p,a,proposal['id'],True))
        self.assertEqual(len(p.bank),1);self.assertEqual(p.bank[0]['account_code'],'9999')
        self.assertFalse(approve_bank(p,a,proposal['id'],True))
        self.assertEqual(len(p.bank),1)
        restored=Package.from_zip(p.to_zip())
        self.assertEqual(restored.config['auto_imports'],p.config['auto_imports'])
        self.assertFalse(approve_bank(restored,a,proposal['id'],True))

    def test_stale_setup_invalidates_analysis_and_approval(self):
        item,doc=source();a=analysis([(item,doc)])
        p=Package(dict(empty_company(),**CFG));proposal=bank_proposal(a,p.config,[])
        p.config['fy_end']='2026-10-31'
        self.assertFalse(approve_bank(p,a,proposal['id'],True))
        self.assertEqual(p.bank,[])

    def test_overlap_and_wrong_totals_block_approval(self):
        item,doc=source();other,doc2=source('overlap.pdf',closing='101.00')
        a=analysis([(item,doc),(other,doc2)])
        self.assertTrue(bank_proposal(a,CFG,[])['errors'])

    def test_batch_and_fingerprint_limits(self):
        item,doc=source()
        with self.assertRaises(ValueError):analyse([dict(item,sha256='incorrect')],CFG)
        with self.assertRaises(ValueError):analyse([item]*51,CFG)

    def test_ai_response_cannot_change_amount_or_post(self):
        bank=[dict(date='2026-01-02',deposit='',withdrawal='10.00',description='Fee',evidence_ref='DOC-123',account_code='9999')]
        payload=dict(ledger_revision=bank_revision(bank),suggestions=[dict(row=0,account_code='5100',confidence=.8,reason='Bank fee source reviewed',source_ref='DOC-123')])
        before=deepcopy(bank)
        self.assertEqual(validate_proposals(bank,payload)[0]['account_code'],'5100')
        self.assertEqual(bank,before)
        for key,value in [('ledger_revision','stale'),('suggestions',[dict(payload['suggestions'][0],source_ref='wrong')]),('suggestions',[dict(payload['suggestions'][0],account_code='1000')])]:
            bad=deepcopy(payload);bad[key]=value
            with self.assertRaises(ValueError):validate_proposals(bank,bad)

    def test_frozen_reports_and_all_layouts_preserve_numbers_and_label_incomplete(self):
        from engine.report_layouts import LAYOUTS
        from engine.reports import management_pdf,financial_statements_pdf,xlsx_report
        import pdfplumber
        from openpyxl import load_workbook
        p=Package.from_directory(ROOT/'sample_company')
        original=generate(p)
        a=analyse([],p.config)
        for layout in LAYOUTS:
            p.config.update(report_layout_ma=layout,report_layout_ufs=layout)
            result,meta=frozen_report(p,a,[])
            self.assertFalse(meta['authorised']);self.assertFalse(meta['template_approved'])
            self.assertIn('PROVISIONAL',meta['status'])
            self.assertEqual(original['profit'],result['profit'])
            data=export_bundle(result,meta)
            with ZipFile(BytesIO(data)) as z:
                manifest=json.loads(z.read('Report_manifest.json'))
                for name,hash_value in manifest['files'].items():self.assertEqual(sha256(z.read(name)).hexdigest(),hash_value)
                with pdfplumber.open(BytesIO(z.read('Management_Accounts_PROVISIONAL.pdf'))) as pdf:
                    self.assertIn('PROVISIONAL',pdf.pages[0].extract_text())
                wb=load_workbook(BytesIO(z.read('Financial_Workpapers_PROVISIONAL.xlsx')),data_only=True)
                self.assertEqual(wb['Report snapshot']['B2'].value,meta['snapshot'])
                wb.close()
            p.bank[0]['description']='Changed after freeze '+layout
            self.assertNotEqual(p.bank[0]['description'],result['package'].bank[0]['description'])

    def test_issue_poll_timestamps_do_not_invalidate_snapshot(self):
        p=Package.from_directory(ROOT/'sample_company');a=analyse([],p.config)
        p.config['issue_register']={'x':dict(last_seen='first')}
        _,a1=frozen_report(p,a,[])
        p.config['issue_register']['x']['last_seen']='second'
        _,a2=frozen_report(p,a,[])
        self.assertEqual(a1['snapshot'],a2['snapshot'])


class AutoUITests(unittest.TestCase):
    def app(self):return AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()

    def test_default_is_upload_first_without_required_setup_fields(self):
        at=self.app();self.assertFalse(at.exception)
        self.assertEqual(at.session_state['app_mode'],'Auto')
        self.assertTrue(any(h.value=='Otto Auto' for h in at.header))
        self.assertFalse(at.text_input)
        self.assertEqual(at.session_state['pkg'].bank,[])

    def test_staged_sources_show_inventory_and_contextual_setup_no_posting(self):
        at=self.app();content=b'date,description,deposit,withdrawal\n2026-01-02,Fee,,10.00\n'
        at.session_state['guided_files']=[dict(name='records.csv',bytes=content,sha256=sha256(content).hexdigest())]
        at.run();self.assertFalse(at.exception)
        self.assertTrue(any(h.value=='What Otto found' for h in at.subheader))
        self.assertTrue(any(t.label=='Company name' for t in at.text_input))
        self.assertEqual(at.session_state['pkg'].bank,[])
        at.button(key='auto_generate').click().run()
        self.assertFalse(at.exception)
        self.assertIn('auto_report_bundle',at.session_state)

    def test_views_share_ledger_and_new_company_clears_uploads(self):
        at=self.app();p=at.session_state['pkg'];p.bank=[dict(date='2026-01-02',reference='X',description='Funding',deposit='100',withdrawal='',account_code='2100')]
        at.selectbox(key='workspace_view').select('Advanced').run()
        self.assertEqual(at.session_state['pkg'].bank,p.bank)
        at.selectbox(key='workspace_view').select('Auto').run()
        self.assertEqual(at.session_state['pkg'].bank,p.bank)
        next(b for b in at.button if b.label=='＋ Start a new company').click().run()
        self.assertEqual(at.session_state['pkg'].bank,[])
        self.assertEqual(at.session_state['guided_files'],[])


class CategoryApprovalTests(unittest.TestCase):
    def test_stale_rejected_then_approval_and_restore_undo_preserve_amounts(self):
        from engine.auto_classification import apply_categories,revert_categories
        p=Package(dict(empty_company(),**CFG),bank=[dict(date='2025-12-02',deposit='100.00',withdrawal='',description='Funding',account_code='9999')])
        before=deepcopy(p.bank)
        self.assertFalse(apply_categories(p,'stale',['3100']))
        self.assertFalse(apply_categories(p,bank_revision(p.bank),['1000']))
        self.assertEqual(before,p.bank)
        self.assertTrue(apply_categories(p,bank_revision(p.bank),['3100']))
        restored=Package.from_zip(p.to_zip())
        self.assertTrue(revert_categories(restored,restored.config['auto_category_history'][0]['id']))
        self.assertEqual(restored.bank[0]['account_code'],'9999')
        self.assertEqual(restored.bank[0]['deposit'],'100.00')
        self.assertFalse(revert_categories(restored,restored.config['auto_category_history'][0]['id']))

    def test_existing_ledger_with_new_source_identifiers_cannot_be_posted_again(self):
        item,doc=source();a=analysis([(item,doc)])
        existing=[dict(date='2025-12-02',deposit='100.00',withdrawal='',description='Same real receipt',reference='different-source-id')]
        self.assertTrue(any('already contains' in e for e in bank_proposal(a,CFG,existing)['errors']))


class AutoExceptionTests(unittest.TestCase):
    def test_source_withdrawal_and_restore_leave_recheck_open(self):
        from auto import _issues
        item,doc=source();a=analysis([(item,doc)])
        p=Package(dict(empty_company(),**CFG))
        p.config['auto_inventory']=deepcopy(a['inventory'])
        records,_=_issues(p,a,bank_proposal(a,p.config,[]))
        p.config['issue_register']['auto-import']={'id':'auto-import','status':'In progress','notes':'Requested export','events':[],
                    'first_seen':'2026-01-01','severity':'Required','title':'Old extraction','source_required':True}
        restored=Package.from_zip(p.to_zip())
        missing=analyse([],restored.config)
        records,_=_issues(restored,missing,bank_proposal(missing,restored.config,restored.bank))
        old=next(r for r in records if r['id']=='auto-import')
        self.assertEqual(old['status'],'Needs recheck')
        self.assertEqual(old['notes'],'Requested export')
        self.assertTrue(any(r['id']=='auto-restored-sources' and r['status']!='Cleared' for r in records))

    def test_acra_uen_mismatch_is_not_silently_applied(self):
        from unittest.mock import patch
        item,doc=source('profile.pdf',text='Company source record')
        wrong=dict(detected=True,fields=dict(company_name=CFG['company_name'],uen='202600099B'))
        with patch('engine.auto.extract_acra_profile',return_value=wrong):a=analysis([(item,doc)])
        self.assertEqual(a['inventory'][0]['status'],'Excluded company mismatch')
        self.assertNotIn('uen',a['proposals'])
        self.assertTrue(bank_proposal(a,CFG,[])['errors'])
