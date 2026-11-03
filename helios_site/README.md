# Helios site

Simple FastAPI + static HTML dashboard for VRP, term structure / skew, and gamma proxy.

Data is pulled only from LSEG via the `lseg-data` package. No public fallbacks.

## Run

```bash
cd helios_site
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Open http://localhost:8000

Workspace must be running and signed in for the desktop session to work.
