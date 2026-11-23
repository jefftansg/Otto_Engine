"""Direct reply dropdowns/manual entry preserve books and suggest categories for review."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import unittest
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest
from engine.client_replies import query_state,save_direct_replies,suggested_category,MANUAL
from engine.clarification_workbook import prepare_workbook,preview_answers,approve_answers,transaction_key,transaction_reply
from engine.clarifications import outstanding
from engine.core import Package
from engine.auto_classification import bank_revision
from test_clarification_workbook import pkg,QUESTIONS,answered,edit

ROOT=Path(__file__).resolve().parents[1]
BINARY=[dict(id='customers-owing',question='Did any customers still owe money at year-end?',request='Provide the unpaid invoices.',section='Other records')]

class DirectReplyTests(unittest.TestCase):
    def test_category_only_reply_saves_facts_and_proposal_but_not_accounting(self):
        p=pkg();before=deepcopy([p.bank,p.journals,p.evidence]);s=query_state(p,QUESTIONS)
        key=transaction_key(p.bank[1],1)
        self.assertEqual(save_direct_replies(p,QUESTIONS,s['revision'],[dict(id=key,choice='Bank charges')],'Reviewer'),1)
        reply=transaction_reply(p,p.bank[1],1)
        self.assertEqual(reply['answer'],'Bank charges');self.assertEqual(suggested_category(reply),'5100')
        self.assertEqual([p.bank,p.journals,p.evidence],before)
        self.assertEqual(p.config['clarification_import_history'][-1]['source'],'Entered in Otto')

    def test_manual_reply_is_editable_audited_and_retained_through_zip(self):
        p=pkg();key=transaction_key(p.bank[0],0);s=query_state(p,QUESTIONS)
        row=dict(id=key,choice=MANUAL,manual='Reimbursement',answer='Client repaid courier cost',document='Receipt 123')
        self.assertEqual(save_direct_replies(p,QUESTIONS,s['revision'],[row],'Reviewer'),1)
        restored=Package.from_zip(p.to_zip());reply=transaction_reply(restored,restored.bank[0],0)
        self.assertEqual(reply['manual_reply'],'Reimbursement');self.assertIn('courier cost',reply['answer'])
        self.assertIsNone(suggested_category(reply))
        s=query_state(p,QUESTIONS);self.assertEqual(save_direct_replies(p,QUESTIONS,s['revision'],[row],'Reviewer'),0)
        row['answer']='Repaid delivery cost';s=query_state(p,QUESTIONS)
        self.assertEqual(save_direct_replies(p,QUESTIONS,s['revision'],[row],'Reviewer'),1)
        self.assertIn('courier cost',p.config['clarification_import_history'][-1]['previous'][key]['answer'])

    def test_general_yes_no_answers_resolve_questions_and_not_sure_stays_open(self):
        for choice,remaining in [('No',0),('Not sure',1),('Not applicable',0)]:
            p=pkg();s=query_state(p,BINARY)
            self.assertEqual(save_direct_replies(p,BINARY,s['revision'],[dict(id=BINARY[0]['id'],choice=choice)],'Reviewer'),1)
            self.assertEqual(len(outstanding(BINARY,p.config['clarification_answers'])),remaining)
        p=pkg();s=query_state(p,QUESTIONS)
        save_direct_replies(p,QUESTIONS,s['revision'],[dict(id=QUESTIONS[0]['id'],choice=MANUAL,answer='Waiting for names',status='Need more information')],'Reviewer')
        self.assertEqual(len(outstanding(QUESTIONS,p.config['clarification_answers'])),1)
        p=pkg();s=query_state(p,QUESTIONS)
        save_direct_replies(p,QUESTIONS,s['revision'],[dict(id=QUESTIONS[0]['id'],choice=MANUAL,answer='Not sure')],'Reviewer')
        self.assertEqual(len(outstanding(QUESTIONS,p.config['clarification_answers'])),1)
        p=pkg();s=query_state(p,QUESTIONS)
        with self.assertRaisesRegex(ValueError,'needs a name or explanation'):save_direct_replies(p,QUESTIONS,s['revision'],[dict(id=QUESTIONS[0]['id'],choice='Yes')],'Reviewer')

    def test_stale_invalid_missing_recorder_and_duplicates_reject_without_mutation(self):
        for case in ('stale','invalid','recorder','duplicate'):
            p=pkg();s=query_state(p,QUESTIONS);row=dict(id=transaction_key(p.bank[0],0),choice='Sale')
            if case=='stale':p.bank[0]['deposit']='101.00'
            if case=='invalid':row['choice']='Invented category'
            rows=[row,row] if case=='duplicate' else [row];before=deepcopy(p.config)
            with self.assertRaises(ValueError):save_direct_replies(p,QUESTIONS,s['revision'],rows,'' if case=='recorder' else 'Reviewer')
            self.assertEqual(p.config,before)

    def test_direct_and_excel_answers_share_history_and_conflict_checks(self):
        p=pkg();older=answered(prepare_workbook(p,QUESTIONS));s=query_state(p,QUESTIONS)
        key=transaction_key(p.bank[0],0)
        save_direct_replies(p,QUESTIONS,s['revision'],[dict(id=key,choice='Sale',answer='Invoice 456')],'Reviewer')
        with self.assertRaisesRegex(ValueError,'answer changed'):approve_answers(p,older,'Reviewer',True)
        current=prepare_workbook(p,QUESTIONS)
        self.assertEqual(preview_answers(p,current)['replies'],[])
        workbook=load_workbook(BytesIO(current))
        self.assertIn('Bank charges',[c.value for c in workbook['_Otto']['B']])
        uncertain=edit(current,lambda b:[setattr(b['Other questions']['D6'],'value','Not sure'),setattr(b['Other questions']['G6'],'value','Answered')])
        self.assertEqual(preview_answers(p,uncertain)['replies'][0]['status'],'Needs answer')

    def test_uncertain_loan_and_transfer_replies_never_create_category_or_transfer(self):
        for choice in ('Loan','Owner funding','Transfer between own accounts','Not sure'):
            p=pkg();s=query_state(p,QUESTIONS);key=transaction_key(p.bank[0],0)
            save_direct_replies(p,QUESTIONS,s['revision'],[dict(id=key,choice=choice)],'Reviewer')
            reply=transaction_reply(p,p.bank[0],0);self.assertIsNone(suggested_category(reply))
            self.assertEqual(p.bank[0]['account_code'],'9999');self.assertEqual(p.bank[0]['transfer_id'],'')
            if choice=='Not sure':self.assertEqual(reply['status'],'Needs answer')

class DirectReplyUITests(unittest.TestCase):
    def test_direct_grid_save_is_visible_and_keeps_ledger_unchanged(self):
        code="""
import streamlit as st
from unittest.mock import patch
from test_clarification_workbook import pkg,QUESTIONS
from clarification_ui import render
if 'pkg' not in st.session_state:st.session_state['pkg']=pkg()
def edit(rows,**kwargs):
    return [dict(r,Reply_category='Bank charges',Client_reply='Monthly bank fee') if r['Question']=='Service charge' else r for r in rows]
with patch('clarification_ui.st.data_editor',side_effect=edit):
    render(st.session_state['pkg'],QUESTIONS,prefix='test')
"""
        at=AppTest.from_string(code,default_timeout=30).run();self.assertFalse(at.exception)
        before=deepcopy(at.session_state['pkg'].bank)
        next(t for t in at.text_input if t.label=='Replies recorded by').set_value('Reviewer')
        next(b for b in at.button if b.label=='Save client replies').click().run()
        self.assertFalse(at.exception);self.assertEqual(at.session_state['pkg'].bank,before)
        self.assertIn('Monthly bank fee',transaction_reply(at.session_state['pkg'],before[1],1)['answer'])
        self.assertTrue(any('Last saved replies: 1 answers saved by Reviewer.' in c.value for c in at.caption))

    def test_client_category_is_a_proposal_until_category_approval(self):
        p=pkg();s=query_state(p,QUESTIONS);key=transaction_key(p.bank[1],1)
        save_direct_replies(p,QUESTIONS,s['revision'],[dict(id=key,choice='Bank charges')],'Reviewer')
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run();at.session_state['pkg']=p
        at.session_state['auto_ai_proposals']={'revision':bank_revision(p.bank),'rows':{1:dict(account_code='4000',reason='Older suggestion')}}
        at.run()
        self.assertFalse(at.exception)
        grid=next(x.value for x in at.dataframe if 'Client_reply' in x.value.columns)
        self.assertEqual(grid.iloc[1]['Category'],'Bank charges')
        self.assertIn('Client reply suggestion',grid.iloc[1]['Basis'])
        self.assertEqual(at.session_state['pkg'].bank[1]['account_code'],'9999')
        at.button(key='auto_save_categories').click().run();self.assertFalse(at.exception)
        self.assertEqual(at.session_state['pkg'].bank[1]['account_code'],'5100')
        self.assertEqual(at.session_state['pkg'].bank[1]['withdrawal'],'15.00')
