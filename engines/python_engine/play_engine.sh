#!/bin/bash

set -euo pipefail
ROOT="/media/ayejay/Linux Important/Projects/Chess-AI"
cd "$ROOT"
export PYTHONPATH="$ROOT/engines/python_engine/src"
export CHESSAI_ENGINE_MODULE="engine"
exec /usr/bin/python3 "$ROOT/engines/python_engine/src/uci.py"
