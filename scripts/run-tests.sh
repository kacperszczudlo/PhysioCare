#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

cd "${BACKEND_DIR}"

if [[ ! -f venv/bin/activate ]]; then
  echo "Brak venv. Utwórz: python -m venv venv && pip install -r requirements.txt"
  exit 1
fi

# shellcheck source=/dev/null
source venv/bin/activate

mkdir -p reports

pytest tests \
  --cov=physiocare \
  --cov-config=.coveragerc \
  --cov-report=term-missing \
  --cov-report=html:reports/coverage \
  --html=reports/pytest-report.html \
  --self-contained-html

echo
echo "Raport HTML: ${BACKEND_DIR}/reports/pytest-report.html"
echo "Coverage HTML: ${BACKEND_DIR}/reports/coverage/index.html"
