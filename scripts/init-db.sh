#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
cd ai-engine
PYTHONPATH=. python3 -c "
from app.config import load_config
from app.main import build_app
cfg,ctx,s,ws,db = build_app('../config/civilization.yaml')
print('Database initialized at', cfg.database_path)
db.close()
"