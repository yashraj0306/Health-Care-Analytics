@echo off
REM One-time setup (Windows). Run from the project root.
cd backend
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cd ..\frontend
npm install
echo Setup done. See README.md "Run it".
