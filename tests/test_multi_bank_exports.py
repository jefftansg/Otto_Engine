"""Independent numeric, document geometry and legacy export acceptance."""
from copy import deepcopy
from decimal import Decimal as D
from io import BytesIO,StringIO
from pathlib import Path
import unittest
import pdfplumber
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest
from engine.core import generate,Package
from engine.reports import management_pdf,financial_statements_pdf,xlsx_report
from engine.bank_intake import suggest_transfers,approve_transfer
from test_multi_bank import fixture

ROOT=Path(__file__).resolve().parents[1]


class MultiBankExportTests(unittest.TestCase):
    def test_pdf_figures_cashflow_bank_rows_and_geometry(self):
        result=generate(fixture())
        for render,landscape in ((management_pdf,True),(financial_statements_pdf,False)):
            with pdfplumber.open(BytesIO(render(result))) as pdf:
                texts=[]
                for page in pdf.pages:
                    self.assertAlmostEqual(page.width,841.89 if landscape else 595.28,places=1)
                    self.assertAlmostEqual(page.height,595.28 if landscape else 841.89,places=1)
                    self.assertTrue(all(-1<=c['x0']<=c['x1']<=page.width+1 and -1<=c['top']<=c['bottom']<=page.height+1 for c in page.chars))
                    texts.append(page.extract_text() or '')
                text='\n'.join(texts)
                for figure in ('1,500.00','1,800.00','300.00'):self.assertIn(figure,text)
                self.assertIn('Bank A',text);self.assertIn('Bank B',text)
                self.assertIn('Cash Flow',text)
                self.assertIn('DRAFT',text)
                if landscape:
                    recon=next(t for t in texts if 'Individual account reconciliations' in t)
                    self.assertIn('1000 Bank A 1,000.00 200.00 1,200.00 1,200.00 0.00',recon)
                    self.assertIn('1001 Bank B 500.00 100.00 600.00 600.00 0.00',recon)

    def test_xlsx_numeric_cells_formula_cache_and_source_preservation(self):
        p=fixture()
        for row in p.bank:
            if row.get('transfer_id'):row.update(transfer_id='',account_code='9999')
        choice=suggest_transfers(p)[0];self.assertTrue(approve_transfer(p,choice['id'],'Reviewer','Original evidence',True))
        p.bank[0].update(source_sha256='a'*64,source_row='1',source_reference='Original R1')
        r=generate(p);self.assertEqual(r['errors'],[])
        blob=xlsx_report(r);values=load_workbook(BytesIO(blob),data_only=True);formulas=load_workbook(BytesIO(blob),data_only=False)
        self.assertEqual(values['Cash Flows']['B2'].value,300)
        self.assertEqual(values['Cash Flows']['B3'].value,0);self.assertEqual(values['Cash Flows']['B4'].value,0)
        self.assertEqual(values['Cash Flows']['B6'].value,1500);self.assertEqual(values['Cash Flows']['B7'].value,1800)
        self.assertEqual(formulas['Cash Flows']['B7'].value,'=B6+SUM(B2:B5)')
        for row,closing in ((2,1200),(3,600)):
            self.assertEqual(values['Bank Accounts'].cell(row,7).value,closing)
            self.assertEqual(values['Bank Accounts'].cell(row,8).value,0)
        headers=[c.value for c in values['Source Bank'][1]]
        self.assertEqual(values['Source Bank'].cell(2,headers.index('source_sha256')+1).value,'a'*64)
        self.assertEqual(values['Source Bank'].cell(2,headers.index('source_reference')+1).value,'Original R1')
        self.assertEqual(values['Internal Transfers'].max_row,3)
        self.assertEqual(values['Internal Transfers']['H2'].value,'Reviewer')
        self.assertEqual(values['Internal Transfers']['I3'].value,'Original evidence')
        for ws in values:
            self.assertFalse(any(c.data_type=='e' for row in ws for c in row),ws.title)
        restored=Package.from_zip(p.to_zip());again=generate(restored)
        for key in ('entries','balances','cashflows','bank_reconciliations','profit'):self.assertEqual(r[key],again[key])
        self.assertEqual(restored.config['transfer_reviews'],p.config['transfer_reviews'])

    def test_non_company_management_only_and_legacy_geometry(self):
        p=Package.from_directory(ROOT/'sample_company');p.config['entity_type']='Sole proprietor';r=generate(p)
        self.assertTrue(management_pdf(r).startswith(b'%PDF'))
        with self.assertRaises(ValueError):financial_statements_pdf(r)
        self.assertNotIn('Bank Accounts',load_workbook(BytesIO(xlsx_report(r))).sheetnames)
        import zipfile
        with zipfile.ZipFile(BytesIO(p.to_zip())) as archive:
            self.assertEqual(archive.read('bank.csv').decode('utf-8-sig').splitlines()[0],'date,description,reference,deposit,withdrawal,account_code,evidence_ref,notes')


    def test_cli_non_company_preserves_previous_entity_output(self):
        from tempfile import TemporaryDirectory
        from contextlib import redirect_stdout
        from run_demo import run
        p=fixture();p.config['entity_type']='Sole proprietor'
        with TemporaryDirectory() as directory:
            root=Path(directory);source=root/'client.zip';source.write_bytes(p.to_zip());out=root/'out';out.mkdir()
            (out/'Unaudited_FS_DRAFT.pdf').write_bytes(b'previous entity PDF')
            (out/'Unaudited_FS_PREVIOUS_ENTITY.pdf').write_bytes(b'earlier saved PDF')
            with redirect_stdout(StringIO()):self.assertTrue(run(source,out))
            self.assertFalse((out/'Unaudited_FS_DRAFT.pdf').exists())
            self.assertEqual((out/'Unaudited_FS_PREVIOUS_ENTITY.pdf').read_bytes(),b'earlier saved PDF')
            self.assertEqual((out/'Unaudited_FS_PREVIOUS_ENTITY_1.pdf').read_bytes(),b'previous entity PDF')
            self.assertTrue((out/'Management_Accounts_DRAFT.pdf').read_bytes().startswith(b'%PDF'))


class MultiBankUITests(unittest.TestCase):
    def app(self,p=None):
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        at.session_state['app_mode']='Guided'
        if p is not None:at.session_state['pkg']=p
        at.run()
        self.assertFalse(at.exception);return at

    def test_pilot_opt_in_empty_and_restored_reconciled_workspace(self):
        at=self.app();at.button(key='enable_multi_bank').click().run()
        self.assertFalse(at.exception);self.assertIn('bank_accounts',at.session_state['pkg'].config)
        self.assertTrue(any('Resolve blocking' in w.value for w in at.warning))
        p=Package.from_zip(fixture().to_zip());at=self.app(p)
        self.assertFalse(at.exception)
        self.assertTrue(any('Arithmetic checks passed' in i.value for i in at.info))
        self.assertFalse(at.tabs)
        self.assertTrue(any('Bank statements' in f.label for f in at.get('file_uploader')))

    def test_transfer_inbox_requires_review_and_company_changes_invalidate(self):
        p=fixture()
        for row in p.bank:
            if row.get('transfer_id'):row.update(transfer_id='',account_code='9999')
        at=self.app(p);before=deepcopy(p.bank)
        next(b for b in at.button if b.label=='Approve this transfer pair').click().run()
        self.assertFalse(at.exception);self.assertEqual(at.session_state['pkg'].bank,before)
        self.assertTrue(any('Approval rejected' in e.value for e in at.error))
        next(t for t in at.text_input if t.label=='Company name').set_value('CHANGED PTE LTD')
        next(b for b in at.button if b.label=='Apply company details').click().run()
        self.assertFalse(at.exception)
        self.assertFalse(at.session_state['pkg'].config['bank_accounts'][0]['coverage_confirmed'])

    def test_uploaded_statement_group_review_and_staging_forms(self):
        from test_bank_intake import package,document
        source=document()
        script='''
from io import BytesIO
from unittest.mock import patch
import streamlit as st
from test_bank_intake import package,document
from multi_bank_ui import render
source=document();uploaded=BytesIO(source['bytes']);uploaded.name=source['name']
if 'pilot' not in st.session_state:st.session_state['pilot']=package()
with patch('bank_intake_ui.st.file_uploader',return_value=[uploaded]):
    render(st.session_state['pilot'])
'''
        at=AppTest.from_string(script,default_timeout=30).run();self.assertFalse(at.exception)
        key=next(t.key for t in at.text_input if t.label=='Reviewer name')
        at.text_input(key=key).set_value('Reviewer')
        next(t for t in at.text_input if t.label=='Review note (optional for uploaded statements)').set_value('Original archive')
        next(c for c in at.checkbox if c.label.startswith('I checked the originals')).check()
        next(b for b in at.button if b.label=='Approve account identity and coverage').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.session_state['pilot'].config['bank_accounts']),1)
        self.assertEqual(at.session_state['pilot'].bank,[])
        next(t for t in at.text_input if t.label=='Transaction reviewer').set_value('Reviewer')
        next(t for t in at.text_input if t.label=='Transaction review note (optional for uploaded statements)').set_value('Original archive')
        next(c for c in at.checkbox if c.label.startswith('I matched all transaction dates')).check()
        next(b for b in at.button if b.label=='Approve and stage proposed transactions').click().run()
        self.assertFalse(at.exception)
        p=at.session_state['pilot'];self.assertEqual(len(p.bank),1);self.assertEqual(p.bank[0]['account_code'],'9999')
        original=deepcopy(p.bank)
        next(b for b in at.button if b.label=='Apply bank transactions').click().run()
        self.assertFalse(at.exception);self.assertEqual(at.session_state['pilot'].bank,original)
