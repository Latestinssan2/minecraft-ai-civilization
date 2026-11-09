#!/usr/bin/env bash
pkill -f "app.main" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
echo "Stopped."