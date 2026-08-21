@echo off
echo Starting SpendTracker Pro on http://localhost:8000 ...
C:\Users\verma\anaconda3\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
