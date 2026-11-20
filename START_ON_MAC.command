#!/bin/zsh
set -e
printf '\033]0;Otto Financial Report Engine\007'
echo "Starting Otto Financial Report Engine v1.2.4..."
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.9+ is required. Install it from https://www.python.org/downloads/macos/"
  read -k 1 "?Press any key to exit..."
  exit 1
fi
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
# Only install when dependencies change; works offline on subsequent launches.
REQ_HASH=$(shasum -a 256 requirements.txt | awk '{print $1}')
if [ ! -f .venv/.requirements_hash ] || [ "$(cat .venv/.requirements_hash)" != "$REQ_HASH" ]; then
  echo "Installing required PDF, Excel and reporting libraries (first launch or upgrade)..."
  python -m pip install -r requirements.txt
  echo "$REQ_HASH" > .venv/.requirements_hash
fi
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
