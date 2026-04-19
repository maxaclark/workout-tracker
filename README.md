# workout-tracker

## Requirements
- **Python** 3.8+
- **pip**
- Local clone of this repository
- Postgres/pgAdmin4 downloaded locally
- Import workout_tracker_schema.sql in pgAdmin4
- Fill .streamlit/sectrets.toml.example with local credentials and publish as streamlit/secrets.toml

---

## App Quickstart

### 1) Create a virtual environment (optional)
**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install streamlit pandas plotly sqlalchemy datetime time
```

### 3) Launch the app
```bash
streamlit run app.py
```
Then open your browser at:
```
http://localhost:8501
```

### 4) Stop the app
Press **Ctrl + C** in the terminal running Streamlit.
