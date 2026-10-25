# How to Run, Test, and Deploy InfluenceMatch

> Step-by-step instructions for running every component of InfluenceMatch locally, with Docker, or deploying to Vercel.

---

## 1. Quickest Way: View Live Deployment (No Installation Needed)

You can use the live production system right now in any web browser:

- **Live Web Application**: [https://influencematch-zeta.vercel.app](https://influencematch-zeta.vercel.app)
- **Interactive Swagger API Docs**: [https://influencematch-zeta.vercel.app/docs](https://influencematch-zeta.vercel.app/docs)
- **GitHub Repository**: [https://github.com/unnatikdm/frcrce_bda_project](https://github.com/unnatikdm/frcrce_bda_project)

---

## 2. Local Environment Setup

### Prerequisites
- **Python**: Version 3.11, 3.12, or 3.13.
- **Git**: Installed and configured.
- **Java**: Java 17, 21, or 25 (only required if you want to run Apache Spark locally).
- **Docker**: Docker Desktop (optional, only required if you want to run PostgreSQL container).

### Step 1: Clone the Repository
```bash
git clone git@github.com:unnatikdm/frcrce_bda_project.git
cd frcrce_bda_project
```

### Step 2: Create a Virtual Environment & Install Dependencies
On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[test,repod,dashboard]"
```

On Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[test,repod,dashboard]"
```

---

## 3. Running the Components

### Method A: Run the Local Web Dashboard (Streamlit)
To start the interactive data science dashboard:
```bash
streamlit run src/influencematch/dashboard.py --server.address 127.0.0.1
```
Open your browser at `http://127.0.0.1:8501`.

---

### Method B: Run the Local FastAPI Server
To start the backend API server:
```bash
uvicorn influencematch.api:app --reload --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

---

### Method C: Run the Full-Stack Local Web Client
You can also run the unified Vercel entrypoint locally to serve both the frontend and backend together:
```bash
uvicorn api.index:app --reload --port 3000
```
Open `http://localhost:3000` to see the full light theme web application running on your computer.

---

### Method D: Run with Docker Compose & PostgreSQL
To start the PostgreSQL database container:
```bash
docker compose up -d --wait postgres
```
Load the verified dataset snapshot into PostgreSQL:
```bash
python -m influencematch.db
```
Now run the API in PostgreSQL-backed mode:
```bash
# On Windows PowerShell:
$env:INFLUENCEMATCH_DATA_BACKEND = "postgres"
$env:DATABASE_URL = "postgresql://influence:influence@localhost:55432/influence"
uvicorn influencematch.api:app --reload
```

---

### Method E: Run the Apache Spark ETL Pipeline
To execute the distributed data lake pipeline and generate Parquet partitions:
```bash
pip install -e ".[bigdata]"
python -m influencematch.pipeline --master "local[2]"
```
To run Spark benchmark timings:
```bash
python -m influencematch.benchmark --repeat 2 --report reports/repod_spark_benchmark.json
```

---

## 4. Running the Automated Test Suite

We use **Pytest** to verify functionality, schema validation, zero-emoji rules, and data integrity:

```bash
pytest
```

To run a specific test file:
```bash
pytest tests/test_api.py -v
pytest tests/test_pipeline.py -v
```

Expected output:
```
tests/test_api.py ..                                     [ 13%]
tests/test_dashboard.py .                                [ 20%]
tests/test_db.py s                                       [ 26%]
tests/test_engagement_context.py ..                      [ 40%]
tests/test_import_data.py ..                             [ 53%]
tests/test_pipeline.py ..                                [ 66%]
tests/test_repod_import.py ..                            [ 80%]
tests/test_tvorog_import.py ..                           [ 93%]
tests/test_tvorog_pipeline.py .                          [100%]
============ 14 passed, 1 skipped in ~60s =============
```

---

## 5. Deploying to Vercel

If you fork or clone this repository, you can deploy your own instance to Vercel in seconds:

### Via Vercel CLI:
```bash
npm install -g vercel
vercel login
vercel link --project influencematch --yes
vercel deploy --prod --yes
```

### Via GitHub Integration:
1. Push your repository to GitHub.
2. Go to [https://vercel.com/new](https://vercel.com/new) and select your GitHub repository.
3. Vercel automatically detects the project and deploys it on every push to `main`!
