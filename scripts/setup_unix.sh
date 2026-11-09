#!/usr/bin/env bash
# One-time setup (macOS/Linux). Run from the project root.
set -e
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cd ../frontend
npm install
echo "Setup done. See README.md 'Run it'."
