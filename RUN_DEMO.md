# Run Demo (quickstart)

Windows PowerShell (recommended):

1. Create and activate a virtual environment

```powershell
python -m venv venv
& venv\Scripts\Activate.ps1
```

2. Install dependencies (full) — this may take several minutes

```powershell
pip install -r requirements.txt
```

Alternatively, for a faster demo-only install (minimal):

```powershell
pip install fastapi uvicorn[standard] pydantic websockets python-dotenv
```

3. (Optional) Create `.env` from `.env.example` and add any required keys

```powershell
copy .env.example .env
# then edit .env to add secrets (OPENAI_API_KEY etc.)
```

4. Start the backend

```powershell
$env:PYTHONPATH='.'; & venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --app-dir backend
```

5. Seed demo data (from `app/index.html` click "Seed Demo Data"), or use API:

```powershell
& venv\Scripts\python.exe -c "import requests; requests.post('http://localhost:8000/api/telemetry', json={'vehicle_id':'J-214','route':'04L','latitude':14.5992,'longitude':120.9840,'occupancy':9,'timestamp':'2026-06-03T02:30:00+00:00'})"
```

6. Run mock telemetry (stdout/http/ws)

```powershell
& venv\Scripts\python.exe edge\mock_telemetry.py --mode ws --url ws://localhost:8000/api/ws/telemetry --interval 1
```

7. Smoke tests

```powershell
& venv\Scripts\python.exe tests\run_api_smoke.py
```

Notes:
- If you want a light-weight demo without installing heavy ML libs, use the minimal install in step 2 and skip the YOLO/model training steps.
- The frontend is served from [app/index.html] when the backend is running; open `http://localhost:8000/` in your browser.
