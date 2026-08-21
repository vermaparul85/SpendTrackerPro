#!/usr/bin/env bash
echo "Starting SpendTracker Pro on http://localhost:8000 ..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
