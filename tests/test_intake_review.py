"""Review suggestions are conservative, deterministic and never delete files."""
from copy import deepcopy
from types import SimpleNamespace
import unittest
from engine.intake_review import flag_uploads, merge_uploads, upload_id
from guided import _bank_batch


def file(name, digest):
    return dict(name=name, sha256=digest, bytes=b'fixture')


def parsed(item, start='2025-01-01', end='2025-12-31', account='same'):
    doc = SimpleNamespace(name=item['name'], sha256=item['sha256'])
    return (doc, {}, dict(detected=True, source=doc.name, sha256=doc.sha256,
                          account_id=account, period_start=start, period_end=end))


class IntakeReviewTests(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(fy_confirmed=True, fy_start='2025-01-01', fy_end='2025-12-31', uen='202500001A')

    def test_renamed_duplicates_are_visible_and_retries_are_idempotent(self):
        a, b = file('original.pdf', 'a'), file('copy.pdf', 'a')
        files = merge_uploads([a], [a, b])
        self.assertEqual(files, [a, b])
        self.assertNotEqual(upload_id(a), upload_id(b))
        flags = flag_uploads(files, [parsed(a), parsed(b)], self.cfg)
        self.assertEqual(len(flags), 2)
        self.assertTrue(all('Exact duplicate' in f['reasons'][0] for f in flags))
        self.assertEqual(merge_uploads(files, [a, b]), files)

    def test_overlap_is_possible_duplicate_only_for_same_account(self):
        a, b = file('jan.pdf', 'a'), file('annual.pdf', 'b')
        flags = flag_uploads([a, b], [parsed(a, end='2025-01-31'), parsed(b)], self.cfg)
        self.assertTrue(all('Possible duplicate coverage' in f['reasons'][0] for f in flags))
        self.assertEqual(flag_uploads([a, b], [parsed(a), parsed(b, account='different')], self.cfg), [])

    def test_cutoffs_require_confirmed_year_and_do_not_discard_prior_evidence(self):
        a = file('previous.pdf', 'a')
        docs = [parsed(a, start='2024-01-01', end='2024-12-31')]
        flag = flag_uploads([a], docs, self.cfg)[0]
        self.assertIn('outside the confirmed financial year', flag['reasons'][0])
        self.assertIn('opening or comparative evidence', flag['reasons'][0])
        self.cfg['fy_confirmed'] = False
        self.assertEqual(flag_uploads([a], docs, self.cfg), [])

    def test_unknown_and_unreadable_are_flagged_as_uncertain_without_mutation(self):
        a, b = file('receipt.csv', 'a'), file('bad.pdf', 'b')
        files = [a, b]
        before = deepcopy(files)
        docs = [(SimpleNamespace(name=a['name'], sha256=a['sha256']), {}, {})]
        flags = flag_uploads(files, docs, self.cfg)
        self.assertIn('May be valid supporting evidence', flags[0]['reasons'][0])
        self.assertIn('Could not read', flags[1]['reasons'][0])
        self.assertEqual(files, before)

    def test_different_company_profile_is_flagged(self):
        a = file('profile.pdf', 'a')
        doc = SimpleNamespace(name=a['name'], sha256=a['sha256'])
        docs = [(doc, dict(detected=True, fields=dict(uen='202500002B')), {})]
        self.assertIn('Company UEN differs', flag_uploads([a], docs, self.cfg)[0]['reasons'][0])
        self.cfg['uen'] = '202500002B'
        self.assertEqual(flag_uploads([a], docs, self.cfg), [])

    def test_retained_exact_copy_does_not_duplicate_proposed_transactions(self):
        from test_guided import parsed_demo
        docs = parsed_demo()
        bank = next(row for row in docs if row[2].get('detected'))
        duplicate = deepcopy(bank)
        duplicate[0].name = 'copy.pdf'
        original = _bank_batch(docs, self.cfg, [])
        repeated = _bank_batch(docs + [duplicate], self.cfg, [])
        self.assertEqual(original['rows'], repeated['rows'])
        self.assertEqual(original['duplicates'], repeated['duplicates'])
