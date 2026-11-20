from copy import deepcopy
from pathlib import Path
import unittest
from io import BytesIO
from streamlit.testing.v1 import AppTest
from engine.core import Package, generate
from engine.document_history import record_id, remove_statement_history

ROOT = Path(__file__).resolve().parents[1]


class HistoryTests(unittest.TestCase):
    def test_remove_restore_and_preserve_accounting(self):
        p = Package.from_directory(ROOT/'sample_company')
        a = dict(source='same.pdf', sha256='one')
        b = dict(source='same.pdf', sha256='two')
        p.config.update(statement_register=[a,b], bank_balances_confirmed=True)
        before = generate(p)
        saved = deepcopy([p.bank,p.claims,p.journals,p.invoices,p.evidence])
        self.assertTrue(remove_statement_history(p, [record_id(a)]))
        self.assertEqual(p.config['statement_register'], [b])
        self.assertFalse(p.config['bank_balances_confirmed'])
        self.assertEqual(saved, [p.bank,p.claims,p.journals,p.invoices,p.evidence])
        after = generate(p)
        for field in ('ledger_end','profit','entries','balances','cashflows'):
            self.assertEqual(before[field],after[field])
        restored = Package.from_zip(p.to_zip())
        self.assertEqual(restored.config['statement_register'],[b])
        cfg = deepcopy(p.config)
        for selection in ([], ['stale'], [record_id(b),'stale']):
            self.assertFalse(remove_statement_history(p,selection))
            self.assertEqual(p.config,cfg)

    def test_history_removal_in_guided_and_advanced(self):
        for mode,scope in [('Guided','documents'),('Advanced','advanced')]:
            at = AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
            record = dict(source='previous.pdf', opening=None, warnings=['Unreadable balance'])
            at.session_state['pkg'].config['statement_register']=[record]
            at.session_state['app_mode']=mode
            at.session_state['guided_stage']=1
            at.run()
            at.multiselect(key='history_selection_'+scope).set_value([record_id(record)]).run()
            at.button(key='history_remove_'+scope).click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state['pkg'].config['statement_register'],[])

    def test_advanced_removal_retains_other_upload_and_does_not_reappear(self):
        at = AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        at.session_state['app_mode']='Advanced'
        at.run()
        files=[]
        for name in ('old.csv','keep.csv'):
            f=BytesIO(b'date,deposit,withdrawal\n2025-01-01,5,0\n');f.name=name;files.append(f)
        at.session_state['advanced_upload_files']=files
        at.run()
        import hashlib
        key=('old.csv',hashlib.sha256(files[0].getvalue()).hexdigest())
        at.multiselect(key='advanced_remove_files').set_value([key]).run()
        next(b for b in at.button if b.label=='Remove selected available files').click().run()
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual([f.name for f in at.session_state['advanced_upload_files']],['keep.csv'])
