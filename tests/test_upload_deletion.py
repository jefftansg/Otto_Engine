"""Session upload deletion, accounting preservation and Guided UI regressions."""
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

import guided
from engine.core import Package, generate
from engine.intake_review import upload_id
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class UploadDeletionTests(unittest.TestCase):
    def setUp(self):
        self.files = [dict(name='statement.pdf', bytes=b'one', sha256='a'*64),
                      dict(name='statement.pdf', bytes=b'two', sha256='b'*64)]
        self.state = dict(guided_files=deepcopy(self.files), guided_upload_version=3,
                          guided_import_checked=True)
        self.pkg = Package.from_directory(ROOT/'sample_company')

    def test_delete_by_content_not_filename_preserves_saved_records_and_reports(self):
        before = generate(self.pkg)
        saved = deepcopy([self.pkg.bank, self.pkg.claims, self.pkg.journals,
                          self.pkg.invoices, self.pkg.evidence])
        register = [dict(source='statement.pdf', sha256='a'*64)]
        self.pkg.config['statement_register'] = deepcopy(register)
        with patch.object(guided.st, 'session_state', self.state):
            self.assertTrue(guided._delete_uploads(self.pkg, [upload_id(self.files[0])], ['a'*64]))
            self.assertFalse(guided._delete_uploads(self.pkg, [upload_id(self.files[0])]))
        self.assertEqual(self.state['guided_files'], [self.files[1]])
        self.assertEqual(self.state['guided_upload_version'], 4)
        self.assertNotIn('guided_import_checked', self.state)
        self.assertFalse(self.pkg.config['bank_balances_confirmed'])
        self.assertEqual(self.pkg.config['statement_register'], register)
        self.assertEqual(saved, [self.pkg.bank, self.pkg.claims, self.pkg.journals,
                                 self.pkg.invoices, self.pkg.evidence])
        after = generate(self.pkg)
        for field in ('ledger_end', 'profit', 'entries', 'balances', 'cashflows'):
            self.assertEqual(before[field], after[field])
        restored = Package.from_zip(self.pkg.to_zip())
        self.assertEqual(restored.bank, self.pkg.bank)
        self.assertFalse(restored.config['bank_balances_confirmed'])

    def test_empty_or_stale_selection_rejected_without_mutation(self):
        original = deepcopy(self.state)
        cfg = deepcopy(self.pkg.config)
        with patch.object(guided.st, 'session_state', self.state):
            for selection in ([], ['missing'], [upload_id(self.files[0]), 'missing']):
                self.assertFalse(guided._delete_uploads(self.pkg, selection))
        self.assertEqual(self.state, original)
        self.assertEqual(self.pkg.config, cfg)

    def test_supporting_file_keeps_confirmed_balances(self):
        self.pkg.config['bank_balances_confirmed'] = True
        with patch.object(guided.st, 'session_state', self.state):
            guided._delete_uploads(self.pkg, [upload_id(self.files[0])])
        self.assertTrue(self.pkg.config['bank_balances_confirmed'])

    def test_old_register_without_hash_rechecks_balances_on_clear(self):
        self.pkg.config['statement_register'] = [dict(source='statement.pdf')]
        with patch.object(guided.st, 'session_state', self.state):
            guided._delete_uploads(self.pkg, [upload_id(f) for f in self.files])
        self.assertEqual(self.state['guided_files'], [])
        self.assertFalse(self.pkg.config['bank_balances_confirmed'])


class UploadDeletionUITests(unittest.TestCase):
    def app(self, stage):
        at = AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()
        files = []
        import hashlib
        for path in sorted((ROOT/'example_imports'/'guided_demo').glob('*.pdf')):
            payload = path.read_bytes()
            files.append(dict(name=path.name, bytes=payload, sha256=hashlib.sha256(payload).hexdigest()))
        at.session_state['guided_files'] = files
        at.session_state['guided_stage'] = stage
        at.session_state['pkg'].config.update(fy_start='2025-01-01', fy_end='2025-12-31',
                                              fy_confirmed=True, bank_balances_confirmed=True)
        return at.run()

    def test_delete_from_bank_refreshes_summary_and_prevents_reimport(self):
        at = self.app(2)
        self.assertFalse(at.exception)
        original = list(at.session_state['guided_files'])
        from engine.importers import inspect_document
        from engine.autofill import extract_bank_statement
        selected = next(upload_id(f) for f in original
                        if extract_bank_statement(inspect_document(f['name'], f['bytes'])).get('detected'))
        at.multiselect[0].set_value([selected]).run()
        next(b for b in at.button if b.label == 'Delete selected files').click().run()
        self.assertFalse(at.exception)
        self.assertNotIn(selected, [upload_id(f) for f in at.session_state['guided_files']])
        self.assertFalse(at.session_state['pkg'].config['bank_balances_confirmed'])
        self.assertTrue(any('No bank statement was recognised' in w.value for w in at.warning))
        self.assertTrue(at.multiselect)  # The company profile can still be reviewed.
        at.run()
        self.assertEqual(len(at.session_state['guided_files']), len(original)-1)
        # Re-uploading the same content remains possible and does not approve a posting.
        at.session_state['guided_files'] = original
        at.run()
        self.assertTrue(at.multiselect)
        self.assertEqual(at.session_state['pkg'].bank, [])

    def test_upload_page_deletes_one_file_and_clear_removes_rest(self):
        at = self.app(0)
        self.assertFalse(at.exception)
        original = list(at.session_state['guided_files'])
        at.multiselect[0].set_value([upload_id(original[0])]).run()
        next(b for b in at.button if b.label == 'Delete selected files').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.session_state['guided_files']), len(original)-1)
        next(b for b in at.button if b.label == 'Clear uploaded files').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['guided_files'], [])
        self.assertFalse(at.multiselect)

    def test_advanced_entry_still_renders(self):
        at = self.app(0)
        at.session_state['app_mode'] = 'Advanced'
        at.run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Smart document intake' in h.value for h in at.header))

    def test_flagged_copy_can_be_retained_then_deleted_independently(self):
        at = self.app(0)
        original = list(at.session_state['guided_files'])
        copy = dict(original[0], name='duplicate.pdf')
        at.session_state['guided_files'] = original + [copy]
        at.run()
        self.assertTrue(any('Exact duplicate' in str(value) for table in at.dataframe for value in table.value.to_numpy().flat))
        at.multiselect[0].set_value([upload_id(copy)]).run()
        next(b for b in at.button if b.label == 'Retain selected files').click().run()
        self.assertEqual(len(at.session_state['guided_files']), len(original)+1)
        self.assertTrue(any('Retained' in str(value) for table in at.dataframe for value in table.value.to_numpy().flat))
        next(b for b in at.button if b.label == 'Delete selected files').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['guided_files'], original)


if __name__ == '__main__':
    unittest.main()
