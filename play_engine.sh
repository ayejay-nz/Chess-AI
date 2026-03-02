#!/bin/bash

set -euo pipefail
ROOT="/media/ayejay/Linux Important/Projects/Chess-AI"
cd "$ROOT"
export PYTHONPATH="$ROOT/src"
export CHESSAI_ENGINE_MODULE="engine"
exec /usr/bin/python3 "$ROOT/src/uci.py"
