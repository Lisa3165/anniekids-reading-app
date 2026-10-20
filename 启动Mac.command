#!/bin/bash
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null; then
 echo 'Please install Python 3.11 or 3.12 from python.org first.'
 read -r
 exit 1
fi
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv || exit 1; fi
.venv/bin/python -m pip install -r requirements.txt || exit 1
.venv/bin/python -m streamlit run app.py
