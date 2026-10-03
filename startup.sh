#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/src"
export USER_DB_PATH="${USER_DB_PATH:-/home/data/EnglishLearnApp/user.db}"
export WORDS_DB_PATH="${WORDS_DB_PATH:-$PWD/database/words.db}"
python deployment/azure_startup.py
exec python -m streamlit run app.py --server.address 0.0.0.0 --server.port "${PORT:-8000}" --server.headless true --browser.gatherUsageStats false
