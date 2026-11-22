"""Small-preparer workflow begins with company details, not general intake."""
from pathlib import Path
from unittest.mock import patch
import hashlib
import unittest
from streamlit.testing.v1 import AppTest
import guided

ROOT = Path(__file__).resolve().parents[1]


class CompanyFirstTests(unittest.TestCase):
    def app(self):
        at = AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()
        at.session_state['app_mode']='Guided'
        return at.run()

    def test_manual_setup_clears_company_then_continues_to_documents_and_bank(self):
        at = self.app()
        self.assertFalse(at.exception)
        self.assertIn('1  Company', at.tabs[0].label)
        self.assertIn('2  Documents', at.tabs[1].label)
        at.text_input[0].set_value('TEST BOOKKEEPING CLIENT PTE LTD')
        at.text_input[1].set_value('202600001A')
        confirmation = next(c for c in at.tabs[0].checkbox if 'checked these dates' in c.label)
        confirmation.check()
        next(b for b in at.button if b.label=='Save company information').click().run()
        self.assertFalse(at.exception)
        self.assertIn('Cleared', at.tabs[0].label)
        self.assertIn('Not started', at.tabs[1].label)
        self.assertEqual(at.session_state['pkg'].bank, [])
        next(b for b in at.button if b.label=='Continue to documents').click().run()
        self.assertEqual(at.session_state['guided_stage'], 1)
        at.button(key='documents_continue_bank').click().run()
        self.assertEqual(at.session_state['guided_stage'], 2)

    def test_optional_profile_fills_only_after_explicit_action(self):
        at = self.app()
        path = next(p for p in (ROOT/'example_imports'/'guided_demo').glob('*.pdf') if 'acra' in p.name.lower())
        payload = path.read_bytes()
        at.session_state['guided_files'] = [dict(name=path.name,bytes=payload,sha256=hashlib.sha256(payload).hexdigest())]
        at.run()
        self.assertEqual(at.session_state['pkg'].config['company_name'], '')
        next(b for b in at.button if b.label=='Use information found in ACRA document').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['guided_stage'], 0)
        self.assertEqual(at.session_state['pkg'].config['company_name'], 'GUIDED DEMO PTE. LTD.')
        self.assertFalse(at.session_state['pkg'].config['fy_confirmed'])
        self.assertEqual(at.session_state['pkg'].bank, [])

    def test_missing_source_issue_routes_to_documents_after_reorder(self):
        state = {}
        with patch.object(guided.st, 'session_state', state):
            guided._open_issue(dict(status='Needs recheck',guided_stage=2))
        self.assertEqual(state['guided_stage'], 1)
