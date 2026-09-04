@echo off
start "flask" cmd /k ".venv\Scripts\activate && python app.py"
start "vite" cmd /k "cd frontend && npm run dev"
