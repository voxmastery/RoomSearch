#!/bin/sh
set -e
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT"
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  echo "Missing .venv. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi
exec "$ROOT/.venv/bin/python" -m uvicorn server.main:app --host 127.0.0.1 --port 43124
