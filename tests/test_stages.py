from copy import deepcopy
import unittest
from engine.clarifications import build_questions, OTHER_RECORDS
from engine.core import Package, generate
from engine.importers import empty_company
from engine.stages import stage_statuses, tab_labels
from guided import _bank_batch
from test_guided import parsed_demo


class StageStatusTests(unittest.TestCase):
    def test_empty_workspace_is_grey_without_mutation(self):
        p = Package(empty_company())
        before = deepcopy(p.config)
        self.assertEqual(stage_statuses(p, [], {}), ['Not started']*5)
        self.assertEqual(p.config, before)

    def ready(self):
        p = Package(empty_company())
        p.config.update(company_name='TEST PTE LTD',uen='202588888A',fy_start='2025-01-01',fy_end='2025-12-31',fy_confirmed=True,
                        bank_balances_confirmed=True,bank_statement_opening='0',bank_statement_closing='1230',other_records_confirmed=True,
                        simple_questions={key:'No' for key,_,_ in OTHER_RECORDS})
        docs = parsed_demo()
        batch = _bank_batch(docs,p.config,[])
        p.bank = batch['rows']
        for r,code in zip(p.bank,['3100','4000','5400','5100']):r['account_code']=code
        p.config['clarification_answers']={q['id']:dict(status='Answered',answer='Synthetic fixture confirmed') for q in build_questions(p,docs,batch)}
        files=[dict(name=d.name,sha256=d.sha256) for d,_,_ in docs]
        return p,docs,files

    def test_green_stages_revert_to_amber_if_category_removed(self):
        p,docs,files = self.ready()
        batch = _bank_batch(docs,p.config,p.bank)
        self.assertFalse(generate(p)['errors'])
        self.assertEqual(stage_statuses(p,docs,batch,files), ['Cleared']*5)
        p.bank[0]['account_code']='9999'
        states=stage_statuses(p,docs,batch,files)
        self.assertEqual(states[2], 'Needs attention')
        self.assertEqual(states[4], 'Needs attention')
        self.assertEqual(states[0], 'Cleared')

    def test_unreviewed_duplicate_requires_decision_before_upload_is_green(self):
        p,docs,files = self.ready()
        from engine.intake_review import flag_uploads
        from types import SimpleNamespace
        original=docs[0]
        copy=dict(files[0],name='copy.pdf')
        d=SimpleNamespace(name=copy['name'],sha256=copy['sha256'])
        docs=docs+[(d,original[1],original[2])]
        files=files+[copy]
        batch=_bank_batch(docs,p.config,p.bank)
        self.assertEqual(stage_statuses(p,docs,batch,files)[1],'Needs attention')
        decisions={f['file_id']:f['reasons'] for f in flag_uploads(files,docs,p.config)}
        self.assertEqual(stage_statuses(p,docs,batch,files,decisions)[1],'Cleared')

    def test_labels_include_symbols_text_and_colour(self):
        labels=tab_labels(['Upload','Company','Bank'],['Cleared','Needs attention','Not started'])
        for label,colour,status in zip(labels,['green','orange','gray'],['Cleared','Needs attention','Not started']):
            self.assertIn(':'+colour+'[',label)
            self.assertIn(status,label)
