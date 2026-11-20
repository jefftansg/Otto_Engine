"""Issue lifecycle, persistence, accounting invariants and tab navigation."""
from copy import deepcopy
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest
from engine.attention import build_attention
from engine.clarifications import build_questions
from engine.core import Package, generate
from engine.importers import empty_company
from engine.issue_tracker import sync_issues, update_issue, issues_csv

ROOT = Path(__file__).resolve().parents[1]


class IssueTrackerTests(unittest.TestCase):
    def setUp(self):
        self.pkg = Package(empty_company())
        self.item = next(r for r in build_attention(self.pkg) if r['id']=='company-setup')

    def test_progress_clears_only_after_fix_and_reopens_on_regression(self):
        sync_issues(self.pkg.config, [self.item], now='first')
        self.assertTrue(update_issue(self.pkg.config, self.item['id'], 'In progress', 'Requested ACRA', now='working'))
        sync_issues(self.pkg.config, [self.item], now='still-open')
        r = self.pkg.config['issue_register'][self.item['id']]
        self.assertEqual(r['status'], 'In progress')
        sync_issues(self.pkg.config, [], now='fixed')
        self.assertEqual(r['status'], 'Cleared')
        self.assertEqual(r['cleared_at'], 'fixed')
        sync_issues(self.pkg.config, [self.item], now='recurred')
        self.assertEqual(r['status'], 'Open')
        self.assertNotIn('cleared_at', r)
        self.assertEqual(r['notes'], 'Requested ACRA')
        self.assertEqual([e['status'] for e in r['events']], ['Open','In progress','Cleared','Open'])
        self.assertEqual(r['first_seen'], 'first')

    def test_manual_clear_and_unknown_issue_rejected_without_mutation(self):
        sync_issues(self.pkg.config, [self.item])
        before = deepcopy(self.pkg.config)
        self.assertFalse(update_issue(self.pkg.config, self.item['id'], 'Cleared', 'Trust me'))
        self.assertFalse(update_issue(self.pkg.config, 'unknown', 'In progress', ''))
        self.assertEqual(self.pkg.config, before)

    def test_missing_source_does_not_silently_clear_on_restore(self):
        self.item['source_required'] = True
        sync_issues(self.pkg.config, [self.item])
        restored = Package.from_zip(self.pkg.to_zip())
        records = sync_issues(restored.config, [], sources_available=False)
        self.assertEqual(records[0]['status'], 'Needs recheck')
        update_issue(restored.config, self.item['id'], 'In progress', 'Need original PDF')
        self.assertEqual(records[0]['status'], 'Needs recheck')
        records = sync_issues(restored.config, [], sources_available=True)
        self.assertEqual(records[0]['status'], 'Cleared')

    def test_older_workspace_initializes_register_and_notes_survive_zip(self):
        old = Package.from_directory(ROOT/'sample_company')
        before = generate(old)
        self.assertNotIn('issue_register', old.config)
        sync_issues(old.config, [self.item])
        update_issue(old.config, self.item['id'], 'In progress', 'Director to confirm')
        restored = Package.from_zip(old.to_zip())
        self.assertEqual(restored.config['issue_register'], old.config['issue_register'])
        after = generate(restored)
        for field in ('entries','balances','cashflows','profit','ledger_end'):
            self.assertEqual(before[field], after[field])
        self.assertEqual(restored.evidence, old.evidence)
        self.assertIn(b'Director to confirm', issues_csv(list(old.config['issue_register'].values())))

    def test_all_questions_and_validation_details_are_listed(self):
        qs = build_questions(self.pkg)
        errors = ['Manual journal issue '+str(i) for i in range(6)]
        items = build_attention(self.pkg, qs, dict(errors=errors))
        self.assertEqual({r['question_id'] for r in items if r['question_id']}, {q['id'] for q in qs})
        validation = next(r for r in items if r['id'].startswith('validation-'))
        self.assertEqual(validation['details'], errors)

    def test_uncategorized_questions_not_truncated_after_eight_rows(self):
        self.pkg.bank = [dict(date='2026-01-01',reference=str(i),description='Transfer',deposit='10',withdrawal='',account_code='9999') for i in range(12)]
        qs = build_questions(self.pkg)
        self.assertEqual(len([q for q in qs if q['id'].startswith('uncategorised-')]), 12)


class IssueTrackerUITests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()

    def test_five_native_tabs_all_render_and_command_menu_is_gone(self):
        at = self.app()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.tabs), 5)
        for tab,label in zip(at.tabs, ['1  Company','2  Documents','3  Bank','4  Other records','5  Reports']):
            self.assertIn(label, tab.label)
            self.assertIn('Not started', tab.label)
        self.assertFalse(any(str(b.key).startswith('guided_nav_') for b in at.button))
        self.assertEqual(len(at.selectbox(key='issue_picker_0').options), len([r for r in at.session_state['pkg'].config['issue_register'].values() if r['status']!='Cleared']))
        self.assertTrue(any('Final review and reports' in h.value for h in at.subheader))

    def test_issue_progress_routes_to_company_then_clears_and_retains_history(self):
        at = self.app()
        at.selectbox(key='issue_picker_0').set_value('company-setup').run()
        progress = next(r for r in at.tabs[0].radio if r.label=='Work status')
        progress.set_value('In progress')
        next(t for t in at.tabs[0].text_area if t.label=='Progress / action taken').set_value('Asked director')
        next(b for b in at.tabs[0].button if b.label=='Save issue progress').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['pkg'].config['issue_register']['company-setup']['status'], 'In progress')
        at.button(key='issue_fix_0').click().run()
        self.assertEqual(at.session_state['guided_stage'], 0)
        at.session_state['pkg'].config.update(company_name='TEST PTE LTD',uen='202600001A',fy_confirmed=True)
        at.run()
        r = at.session_state['pkg'].config['issue_register']['company-setup']
        self.assertEqual((r['status'], r['notes']), ('Cleared', 'Asked director'))
        self.assertFalse(at.exception)

    def test_question_action_targets_exact_question_without_changing_accounts(self):
        at = self.app()
        pkg = at.session_state['pkg']
        issue = next(r for r in pkg.config['issue_register'].values() if r.get('question_id'))
        at.selectbox(key='issue_picker_0').set_value(issue['id']).run()
        at.button(key='issue_fix_0').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['guided_stage'], 3)
        self.assertEqual(at.session_state['question_focus_id'], issue['question_id'])
        self.assertEqual(at.session_state['pkg'].bank, [])
