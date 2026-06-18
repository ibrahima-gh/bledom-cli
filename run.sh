#!/usr/bin/env bash
set -e

VENV=".venv"

if [ ! -d "$VENV" ]; then
  echo "Creating virtual environment…"
  python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"

echo "Installing/updating dependencies…"
pip install -q -r requirements.txt

echo "Starting bledom-cli on http://0.0.0.0:8000"
echo "Access from your phone: http://$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}'):8000"

python main.py
