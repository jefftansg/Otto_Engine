#!/bin/zsh
set -e
printf '\033]0;Otto Financial Report Engine\007'
cd "$(dirname "$0")"
OTTO_VERSION=$(cat VERSION)
echo "Starting Otto Financial Report Engine v${OTTO_VERSION}..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.9 through 3.12 is required. Install it from https://www.python.org/downloads/macos/"
  exit 1
fi
# Check before installing anything or touching another running session.
OTTO_PORT=${OTTO_PORT:-8501}
python3 -m engine.launcher --port "$OTTO_PORT"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
if [ ! -x .venv/bin/python ]; then
  echo "The .venv is incomplete. Rename it to .venv-backup and start Otto again. Your saved workspace ZIPs are separate."
  exit 1
fi
source .venv/bin/activate
python -c 'from engine.launcher import check_runtime; check_runtime()'
# Only install when dependencies change; works offline on subsequent launches.
REQ_HASH=$(shasum -a 256 requirements.txt constraints-m0.txt | shasum -a 256 | awk '{print $1}')
if [ ! -f .venv/.requirements_hash ] || [ "$(cat .venv/.requirements_hash)" != "$REQ_HASH" ] || ! python -c 'import streamlit, reportlab, xlsxwriter, openpyxl, xlrd, pdfplumber'; then
  echo "Installing required PDF, Excel and reporting libraries (first launch or upgrade)..."
  python -m pip --disable-pip-version-check install -r requirements.txt
  python -m pip --disable-pip-version-check check
  echo "$REQ_HASH" > .venv/.requirements_hash
fi
python -m pip --disable-pip-version-check check
echo "Open Otto at http://localhost:$OTTO_PORT and keep this Terminal open."
python -m streamlit run app.py --server.address 127.0.0.1 --server.port "$OTTO_PORT" --browser.gatherUsageStats false
