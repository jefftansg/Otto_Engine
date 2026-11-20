"""Restore the unmodified synthetic sample schema from the v1.2.4 baseline."""
from pathlib import Path
import unittest
from engine.core import Package, generate
from engine.issue_tracker import sync_issues
from engine.attention import build_attention


class LegacyWorkspaceTests(unittest.TestCase):
    def test_v124_fixture_restores_with_identical_reports_after_tracker_initialization(self):
        data=(Path(__file__).parent/'fixtures'/'workspace-v1.2.4.zip').read_bytes()
        legacy=Package.from_zip(data)
        self.assertNotIn('issue_register', legacy.config)
        before=generate(legacy)
        sync_issues(legacy.config, build_attention(legacy,result=before))
        restored=Package.from_zip(legacy.to_zip())
        after=generate(restored)
        for field in ('entries','balances','cashflows','profit','ledger_end','errors'):
            self.assertEqual(before[field],after[field])
        for field in ('bank','claims','journals','invoices','evidence'):
            self.assertEqual(getattr(legacy,field),getattr(restored,field))
        self.assertEqual(legacy.config['issue_register'],restored.config['issue_register'])
