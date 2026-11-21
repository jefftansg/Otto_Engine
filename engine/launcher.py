"""Dependency-free startup checks for the local Mac launcher."""
import argparse
from pathlib import Path
import socket
import sys


def check_runtime(version=None):
    version = version or sys.version_info[:2]
    if not (3, 9) <= tuple(version) < (3, 13):
        raise ValueError('This release supports Python 3.9 through 3.12. Install a supported Python and recreate the local .venv.')


def check_project(root):
    required = ('app.py', 'guided.py', 'auto.py', 'requirements.txt', 'constraints-m0.txt',
                'assets/otto_icon.png', 'assets/otto_mascot.png', 'assets/otto_wordmark.png')
    missing = [name for name in required if not (Path(root)/name).is_file()]
    if missing:
        raise ValueError('The Otto folder is incomplete. Extract the complete release ZIP. Missing: '+', '.join(missing))


def check_port(port):
    if not 1024 <= port <= 65535:
        raise ValueError('OTTO_PORT must be a number from 1024 to 65535.')
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            # Match Tornado's restart behaviour: a stopped server can leave
            # connections in TIME_WAIT even though no process is listening.
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(('127.0.0.1', port))
    except OSError as exc:
        raise ValueError(
            f'Port {port} is unavailable. If Otto is already open, save your workspace ZIP, '
            'then stop its Terminal with Control+C before starting this copy. '
            'For a separate session, run: OTTO_PORT=8502 ./START_ON_MAC.command. '
            'No running application has been stopped.'
        ) from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8501)
    args = parser.parse_args()
    try:
        check_runtime()
        check_project(Path(__file__).resolve().parents[1])
        check_port(args.port)
    except ValueError as exc:
        print('Otto could not start: '+str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
