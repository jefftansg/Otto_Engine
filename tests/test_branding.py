"""Otto interface branding regressions; does not require a running browser."""
from pathlib import Path
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class OttoBrandingTests(unittest.TestCase):
    def test_original_logo_and_derived_assets_exist(self):
        for name in ('otto_original_logo.png', 'otto_wordmark.png',
                     'otto_mascot.png', 'otto_icon.png'):
            path = ROOT / 'assets' / name
            self.assertTrue(path.is_file(), name)
            with Image.open(path) as image:
                self.assertGreater(image.width, 100)
                self.assertGreater(image.height, 100)
                image.verify()

    def test_page_title_and_favicon_are_branded(self):
        app = (ROOT / 'app.py').read_text(encoding='utf-8')
        self.assertIn("page_title='Otto | Financial Report Engine'", app)
        self.assertIn("ASSETS / 'otto_icon.png'", app)
        self.assertIn("ASSETS / 'otto_mascot.png'", app)
        self.assertIn("ASSETS / 'otto_wordmark.png'", app)

    def test_saved_workspace_and_reports_use_new_name(self):
        for filename in ('app.py', 'guided.py'):
            text = (ROOT / filename).read_text(encoding='utf-8')
            self.assertIn('Otto_Client_Workspace.zip', text)
        self.assertIn('Otto Financial Report Engine | DRAFT',
                      (ROOT / 'engine/reports.py').read_text(encoding='utf-8'))

    def test_mac_launcher_is_executable(self):
        launcher = ROOT / 'START_ON_MAC.command'
        self.assertTrue(launcher.is_file())
        self.assertTrue(bool(launcher.stat().st_mode & 0o111))
        self.assertIn('Starting Otto Financial Report Engine', launcher.read_text())


if __name__ == '__main__':
    unittest.main()
