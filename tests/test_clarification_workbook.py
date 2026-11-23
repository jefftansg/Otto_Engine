"""Synthetic client Excel round trips; replies never post or categorise financial rows."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import unittest
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest
from engine.clarification_workbook import (prepare_workbook,preview_answers,approve_answers,transaction_reply,TX_HEADERS,Q_HEADERS)
from engine.core import Package
from engine.auto_classification import bank_revision
from test_bank_intake import package

ROOT=Path(__file__).resolve().parents[1]
QUESTIONS=[dict(id='company-question',question='Who will review the statements?',request='Provide the director names.',section='Company',audience='Client')]


def pkg():
    p=package()
    p.bank=[dict(date='2025-06-01',description='Customer receipt',reference='R1',deposit='100.00',withdrawal='',account_code='9999',evidence_ref='DOC-A',bank_account_code='1000',transfer_id='',notes='',source_sha256='a'*64,source_row='1',source_reference='BANK-A'),
            dict(date='2025-06-02',description='Service charge',reference='R2',deposit='',withdrawal='15.00',account_code='9999',evidence_ref='DOC-A',bank_account_code='1000',transfer_id='',notes='',source_sha256='a'*64,source_row='2',source_reference='BANK-B')]
    return p


def edit(data,fn):
    book=load_workbook(BytesIO(data));fn(book);out=BytesIO();book.save(out);return out.getvalue()


def answered(data):
    def fill(book):
        t=book['Transactions'];t['G6']='Consulting invoice June';t['H6']='Sale';t['I6']='INV-001';t['J6']='Client reviewer'
        q=book['Other questions'];q['D6']='Director A will review';q['F6']='Client reviewer'
    return edit(data,fill)

class WorkbookTests(unittest.TestCase):
    def test_export_is_scoped_client_input_with_types_dropdowns_and_no_ledger_changes(self):
        p=pkg();before=deepcopy(p.bank);data=prepare_workbook(p,QUESTIONS)
        book=load_workbook(BytesIO(data));t=book['Transactions']
        self.assertEqual([c.value for c in t[5]],TX_HEADERS)
        self.assertEqual([c.value for c in book['Other questions'][5]],Q_HEADERS)
        self.assertEqual(t['E6'].value,100);self.assertEqual(t['F6'].value,0)
        self.assertEqual(t['B6'].value.strftime('%Y-%m-%d'),'2025-06-01')
        self.assertEqual(t.freeze_panes,'C6');self.assertTrue(t.column_dimensions['A'].hidden)
        self.assertEqual(book['_Otto'].sheet_state,'veryHidden');self.assertTrue(t.data_validations.dataValidation)
        self.assertEqual(p.bank,before);self.assertEqual(preview_answers(p,data)['replies'],[])

    def test_preview_requires_review_and_zip_restore_preserves_history_without_posting(self):
        p=pkg();data=answered(prepare_workbook(p,QUESTIONS));before=deepcopy([p.bank,p.journals,p.evidence,p.config])
        preview=preview_answers(p,data);self.assertEqual(len(preview['replies']),2)
        self.assertEqual([p.bank,p.journals,p.evidence,p.config],before)
        self.assertFalse(approve_answers(p,data,'Reviewer',False));self.assertEqual(p.config,before[-1])
        self.assertTrue(approve_answers(p,data,'Reviewer',True))
        self.assertEqual(p.bank,before[0]);self.assertEqual(p.journals,before[1]);self.assertEqual(p.evidence,before[2])
        reply=transaction_reply(p,p.bank[0],0);self.assertEqual(reply['money_type'],'Sale')
        self.assertEqual(p.bank[0]['account_code'],'9999')
        self.assertEqual(p.config['clarification_answers']['company-question']['status'],'Answered')
        restored=Package.from_zip(p.to_zip())
        self.assertEqual(restored.config['clarification_import_history'],p.config['clarification_import_history'])
        self.assertEqual(preview_answers(restored,data)['replies'],[])
        self.assertFalse(approve_answers(p,data,'Reviewer',True));self.assertEqual(len(p.config['clarification_import_history']),1)

    def test_sort_and_partial_replies_match_ids_not_row_positions(self):
        p=pkg();data=prepare_workbook(p,QUESTIONS)
        def reorder(book):
            s=book['Transactions'];a=[c.value for c in s[6]];b=[c.value for c in s[7]]
            for col,v in enumerate(b,1):s.cell(6,col,v)
            for col,v in enumerate(a,1):s.cell(7,col,v)
            s['G6']='Monthly bank fee';s['H6']='Business expense'
        data=edit(data,reorder)
        self.assertTrue(approve_answers(p,data,'Reviewer',True))
        self.assertEqual(transaction_reply(p,p.bank[1],1)['answer'],'Monthly bank fee')
        self.assertEqual(transaction_reply(p,p.bank[0],0),{})

    def test_later_partial_response_can_be_added_without_reimporting_unchanged_answers(self):
        p=pkg();data=answered(prepare_workbook(p,QUESTIONS));self.assertTrue(approve_answers(p,data,'Reviewer',True))
        later=edit(data,lambda b:setattr(b['Transactions']['G7'],'value','Monthly bank fee'))
        self.assertEqual(len(preview_answers(p,later)['replies']),1)
        self.assertTrue(approve_answers(p,later,'Reviewer',True));self.assertEqual(len(p.config['transaction_clarifications']),2)

    def test_company_period_bank_changes_and_foreign_workspace_are_rejected(self):
        for change in ('bank','company','period','foreign'):
            p=pkg();data=answered(prepare_workbook(p,QUESTIONS))
            if change=='bank':p.bank[0]['deposit']='101.00'
            elif change=='company':p.config['uen']='OTHER'
            elif change=='period':p.config['fy_end']='2026-12-31'
            else:p.config['clarification_exports']={}
            before=deepcopy(p.config)
            with self.assertRaises(ValueError):approve_answers(p,data,'Reviewer',True)
            self.assertEqual(p.config,before)

    def test_source_edits_duplicate_deleted_ids_headings_and_formula_replies_rejected(self):
        changes=[lambda b:setattr(b['Transactions']['E6'],'value',999),
                 lambda b:setattr(b['Transactions']['A7'],'value',b['Transactions']['A6'].value),
                 lambda b:b['Transactions'].delete_rows(7),
                 lambda b:setattr(b['Transactions']['G5'],'value','Changed heading'),
                 lambda b:setattr(b['Transactions']['G6'],'value','=1+1')]
        for fn in changes:
            p=pkg();data=edit(prepare_workbook(p,QUESTIONS),fn);before=deepcopy(p.config)
            with self.assertRaises(ValueError):approve_answers(p,data,'Reviewer',True)
            self.assertEqual(p.config,before)

    def test_existing_answer_changes_cannot_be_overwritten_by_old_export(self):
        p=pkg();data=answered(prepare_workbook(p,QUESTIONS))
        p.config['clarification_answers']={'company-question':dict(answer='Already checked elsewhere',status='Answered')}
        before=deepcopy(p.config)
        with self.assertRaisesRegex(ValueError,'answer changed'):approve_answers(p,data,'Reviewer',True)
        self.assertEqual(p.config,before)

    def test_formula_like_source_is_literal_and_changed_transaction_hides_old_reply(self):
        p=pkg();p.bank[0]['description']='=HYPERLINK("https://invalid.example", "source")'
        data=answered(prepare_workbook(p,QUESTIONS));book=load_workbook(BytesIO(data))
        self.assertEqual(book['Transactions']['D6'].data_type,'s')
        self.assertTrue(approve_answers(p,data,'Reviewer',True))
        p.bank[0]['deposit']='200.00';self.assertEqual(transaction_reply(p,p.bank[0],0),{})

    def test_invalid_types_statuses_and_blank_explanations_rejected(self):
        for field,value,reason in [('H6','Ignore','money type'),('K6','Approved','response status')]:
            p=pkg()
            def change(b):
                b['Transactions']['G6']='Explanation';b['Transactions'][field]=value
            data=edit(prepare_workbook(p,QUESTIONS),change)
            with self.assertRaisesRegex(ValueError,reason):preview_answers(p,data)
        p=pkg();data=prepare_workbook(p,QUESTIONS)
        data=edit(data,lambda b:[setattr(b['Transactions']['G6'],'value','Need to check with supplier'),setattr(b['Transactions']['K6'],'value','Need more information')])
        self.assertEqual(preview_answers(p,data)['replies'][0]['status'],'Needs answer')

    def test_transfer_and_classified_rows_are_not_sent_as_uncategorised_questions(self):
        p=pkg();p.bank[0].update(account_code='TRANSFER',transfer_id='PAIR');p.bank[1]['account_code']='5200'
        p.config['clarification_answers']={'company-question':dict(status='Answered',answer='Done')}
        with self.assertRaisesRegex(ValueError,'no unanswered'):prepare_workbook(p,QUESTIONS)


    def test_category_review_can_progress_while_client_answers_without_staling_source_facts(self):
        p=pkg();data=answered(prepare_workbook(p,QUESTIONS));p.bank[0]['account_code']='4000'
        self.assertTrue(approve_answers(p,data,'Reviewer',True));self.assertEqual(p.bank[0]['account_code'],'4000')
        self.assertEqual(transaction_reply(p,p.bank[0],0)['answer'],'Consulting invoice June')

    def test_unreadable_oversized_macro_and_external_link_files_are_rejected_without_mutation(self):
        from zipfile import ZipFile,ZIP_DEFLATED
        p=pkg();data=prepare_workbook(p,QUESTIONS);before=deepcopy(p.config)
        files=[b'not Excel',b'x'*(10*1024*1024+1)]
        for name in ('xl/vbaProject.bin','xl/externalLinks/externalLink1.xml'):
            out=BytesIO(data)
            with ZipFile(out,'a',ZIP_DEFLATED) as z:z.writestr(name,b'placeholder')
            files.append(out.getvalue())
        for f in files:
            with self.assertRaises(ValueError):approve_answers(p,f,'Reviewer',True)
            self.assertEqual(p.config,before)

class WorkbookUITests(unittest.TestCase):
    def test_auto_and_guided_expose_export_and_download_without_changing_ledger(self):
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run();p=pkg()
        at.session_state['pkg']=p;at.run();before=bank_revision(p.bank)
        at.button(key='auto_prepare_clarifications').click().run();self.assertFalse(at.exception)
        self.assertTrue(at.session_state['pkg'].config['clarification_exports'])
        self.assertTrue(any(x.label=='Download client clarification workbook' for x in at.get('download_button')))
        self.assertEqual(bank_revision(at.session_state['pkg'].bank),before)
        returned=answered(at.session_state['auto_clarification_export_cache']['data'])
        self.assertTrue(approve_answers(at.session_state['pkg'],returned,'Reviewer',True))
        at.run();self.assertFalse(at.exception)
        views=[x.value for x in at.dataframe if 'Client_reply' in x.value.columns]
        self.assertTrue(any('Consulting invoice June' in str(x.iloc[0]['Client_reply']) for x in views))
        at.selectbox(key='workspace_view').select('Guided').run();self.assertFalse(at.exception)
        # Multi-bank Guided uses detailed tools. The same replies and export record remain shared.
        self.assertEqual(bank_revision(at.session_state['pkg'].bank),before)

    def test_uploaded_answers_are_previewed_then_require_explicit_review_to_save(self):
        code="""
import streamlit as st
from unittest.mock import patch
from types import SimpleNamespace
from test_clarification_workbook import pkg,QUESTIONS,answered
from engine.clarification_workbook import prepare_workbook
from clarification_ui import render
if 'pkg' not in st.session_state:
    st.session_state['pkg']=pkg()
    st.session_state['returned']=answered(prepare_workbook(st.session_state['pkg'],QUESTIONS))
with patch('clarification_ui.st.file_uploader',return_value=SimpleNamespace(getvalue=lambda:st.session_state['returned'])):
    render(st.session_state['pkg'],QUESTIONS,prefix='test')
"""
        at=AppTest.from_string(code,default_timeout=30).run();self.assertFalse(at.exception)
        before=deepcopy(at.session_state['pkg'].bank)
        preview=next(t.value for t in at.dataframe if 'Answer' in t.value.columns)
        self.assertEqual(preview.iloc[0]['Question'],'Customer receipt')
        self.assertEqual(preview.iloc[0]['Received'],'100.00')
        self.assertNotIn('transaction_clarifications',at.session_state['pkg'].config)
        next(t for t in at.text_input if t.label=='Replies reviewed by').set_value('Reviewer')
        next(c for c in at.checkbox if c.label.startswith('I reviewed these returned answers')).check()
        next(b for b in at.button if b.label=='Approve and save clarification replies').click().run()
        self.assertFalse(at.exception);self.assertTrue(at.session_state['pkg'].config['transaction_clarifications'])
        self.assertTrue(any('Last import: 2 answers saved by Reviewer.' in c.value for c in at.caption))
        self.assertEqual(at.session_state['pkg'].bank,before)
