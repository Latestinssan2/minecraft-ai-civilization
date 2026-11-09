#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "Starting backend..."
"$ROOT/scripts/start-backend.sh" &
BACKEND_PID=$!
sleep 3
echo "Starting dashboard..."
"$ROOT/scripts/start-dashboard.sh" &
DASH_PID=$!
echo "Backend PID: $BACKEND_PID"
echo "Dashboard PID: $DASH_PID"
echo "Press Ctrl+C to stop."
wait