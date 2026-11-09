#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
cd ai-engine
mkdir -p data
PYTHONPATH=. python3 -m app.main --config ../config/civilization.yaml