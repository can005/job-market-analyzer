#!/usr/bin/env bash
set -euo pipefail

python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-ingestion.txt -r requirements-ui.txt -r requirements-dev.txt
pip install -e . --no-deps
echo "✅ Done. Activate with: source venv/bin/activate"
