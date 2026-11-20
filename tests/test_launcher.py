"""Fail early without killing sessions or installing dependencies on a bad start."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from engine.launcher import check_runtime, check_project, check_port

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def test_supported_runtime_bounds(self):
        for version in ((3,9),(3,10),(3,11),(3,12)):
            check_runtime(version)
        for version in ((3,8),(3,13),(2,7)):
            with self.assertRaisesRegex(ValueError,'Python 3.9 through 3.12'):
                check_runtime(version)

    def test_incomplete_release_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'Extract the complete release ZIP'):
                check_project(folder)
        check_project(ROOT)

    def test_busy_port_preserves_existing_session_and_explains_recovery(self):
        with patch('engine.launcher.socket.socket') as socket:
            socket.return_value.__enter__.return_value.bind.side_effect = OSError('in use')
            with self.assertRaisesRegex(ValueError, 'save your workspace ZIP') as result:
                check_port(8501)
            self.assertIn('Control+C', str(result.exception))
            self.assertIn('OTTO_PORT=8502', str(result.exception))
            self.assertIn('No running application has been stopped', str(result.exception))

    def test_invalid_ports_rejected_before_socket_access(self):
        with patch('engine.launcher.socket.socket') as socket:
            for port in (0,80,65536):
                with self.assertRaisesRegex(ValueError,'1024 to 65535'):
                    check_port(port)
            socket.assert_not_called()

    def test_port_probe_stays_on_loopback_and_releases_socket(self):
        with patch('engine.launcher.socket.socket') as socket:
            check_port(8513)
            socket.return_value.__enter__.return_value.bind.assert_called_once_with(('127.0.0.1',8513))
            socket.return_value.__exit__.assert_called_once()
