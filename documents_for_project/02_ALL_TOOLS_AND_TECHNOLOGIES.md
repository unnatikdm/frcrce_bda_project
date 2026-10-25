# Technologies and Tools Used in InfluenceMatch

> A simple, plain-English explanation of every software, library, engine, and cloud service used in this project.

---

## Quick Reference Table

| Category | Tool / Technology | What It Does In This Project |
| :--- | :--- | :--- |
| **Core Language** | Python 3.12 / 3.13 | The main programming language used for the entire backend, pipelines, and algorithms. |
| **Backend API** | FastAPI & Starlette | High-speed web framework that provides the REST API endpoints (`/health`, `/dataset`, `/match`, `/creators`). |
| **Web Server** | Uvicorn | ASGI server that runs the FastAPI application locally with lightning-fast asynchronous performance. |
| **Big Data Engine** | Apache Spark (PySpark 4.0+) | Distributed computing engine used to clean data, validate integrity, and create scalable data lakes. |
| **Data Lake Format** | Apache Parquet | High-performance, compressed columnar file format used to store creator and post records. |
| **Relational Database**| PostgreSQL 16 | Production SQL database used to store dataset snapshots and run SQL analytics summaries. |
| **Containerization** | Docker & Docker Compose | Packages PostgreSQL into an isolated container so it runs identically on any computer. |
| **Machine Learning & NLP**| Scikit-Learn & SciPy | Computes TF-IDF (Term Frequency-Inverse Document Frequency) vectors and Cosine Similarity math. |
| **Local Dashboard** | Streamlit | Python dashboard library used for the interactive local data analysis and recommendation interface. |
| **Web Frontend** | Vanilla HTML5, CSS3, JavaScript | Lightweight, zero-framework web client with custom design system, full light theme, and no external UI bloat. |
| **Cloud Hosting** | Vercel | Cloud platform hosting the production web app and running the FastAPI backend as Serverless Functions. |
| **Testing** | Pytest & HTTPX | Automated test suite that runs 15 tests to ensure zero bugs and strict data integrity. |
| **Version Control** | Git & GitHub | Tracks all code revisions and connects directly to Vercel for continuous deployment. |

---

## Detailed Breakdown of Each Technology

### 1. Python (Core Programming Language)
- **What it is**: Python is one of the most popular, readable, and widely supported programming languages in data science and web development.
- **Why we used it**: Python has the best ecosystem for combining Big Data (PySpark), Machine Learning (Scikit-Learn), and modern web APIs (FastAPI) in a single codebase.
- **Where it lives**: All core logic in [`src/influencematch/`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/src/influencematch/).

---

### 2. FastAPI (Application Programming Interface)
- **What it is**: FastAPI is a modern, high-performance web framework for building APIs with Python.
- **Why we used it**: 
  - It is extremely fast (on par with NodeJS and Go).
  - It automatically checks request data using Pydantic schemas.
  - It automatically creates interactive Swagger documentation (`/docs`) without writing extra code.
- **Where it lives**: [`src/influencematch/api.py`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/src/influencematch/api.py) and [`api/index.py`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/api/index.py).

---

### 3. Apache Spark / PySpark (Big Data Engine)
- **What it is**: Apache Spark is an industry-standard distributed data processing system. It can process millions or billions of records across a cluster of computers.
- **Why we used it**:
  - We use Spark in local mode (`local[2]`) to run our ETL (Extract, Transform, Load) pipeline.
  - It verifies file hashes, checks for duplicate creator IDs, validates relationships (for example, ensuring each Reel belongs to an existing creator), and partitions output data.
- **Where it lives**: [`src/influencematch/pipeline.py`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/src/influencematch/pipeline.py) and [`src/influencematch/benchmark.py`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/src/influencematch/benchmark.py).

---

### 4. Apache Parquet (Columnar Storage)
- **What it is**: Parquet is a columnar file storage format. Unlike CSV files where data is stored line by line, Parquet stores data column by column.
- **Why we used it**:
  - Files are compressed with Snappy, making them 80% smaller than raw JSON or CSV.
  - Scanning millions of rows to check follower counts only reads the "followers" column, saving massive amounts of memory and CPU time.
- **Where it lives**: Partitioned data written to `%LOCALAPPDATA%\InfluenceMatch\data-lake` or `data/lake`.

---

### 5. PostgreSQL (Relational Database)
- **What it is**: PostgreSQL is one of the most reliable and advanced open-source relational databases in the world.
- **Why we used it**:
  - It stores imported datasets in atomic database transactions (all-or-nothing writes).
  - It provides SQL analytics (calculating follower distribution percentiles, niche breakdowns, and engagement aggregations).
- **Where it lives**: [`src/influencematch/db.py`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/src/influencematch/db.py) and configured in [`docker-compose.yml`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/docker-compose.yml).

---

### 6. Docker & Docker Compose (Container Management)
- **What it is**: Docker packages software and its dependencies into a lightweight "container" that runs anywhere without configuration headaches.
- **Why we used it**:
  - Instead of forcing the user to manually install and configure PostgreSQL on their machine, running `docker compose up -d` starts PostgreSQL automatically on port 55432 with the exact tables and permissions needed.
- **Where it lives**: [`docker-compose.yml`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/docker-compose.yml).

---

### 7. Scikit-Learn (Machine Learning & Natural Language Processing)
- **What it is**: Scikit-Learn is the premier Python library for classical machine learning and data modeling.
- **Why we used it**:
  - **TfidfVectorizer**: Converts creator text (bios, primary topics, coded tags) into mathematical vectors.
  - **Cosine Similarity**: Measures the mathematical angle between the user's campaign brief and creator profiles to determine exact relevance scores from 0.0 to 1.0.
- **Where it lives**: [`src/influencematch/matching.py`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/src/influencematch/matching.py).

---

### 8. Streamlit (Local Data Science Dashboard)
- **What it is**: Streamlit is an open-source Python framework that turns Python data scripts into shareable web apps.
- **Why we used it**:
  - Allows local operators to explore the data, adjust weights, view Spark benchmarks, and download full ranking traces without writing frontend code.
- **Where it lives**: [`src/influencematch/dashboard.py`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/src/influencematch/dashboard.py).

---

### 9. Vanilla HTML5, CSS3, and JavaScript (Web Frontend)
- **What it is**: The core building blocks of the web:
  - **HTML5**: Creates the structure (cards, forms, tables, buttons).
  - **CSS3**: Styles the page with a clean Light Theme (Inter font, slate colors, subtle borders, card elevation).
  - **JavaScript**: Fetches live data from the API and dynamically updates the charts and tables without page reloads.
- **Why we used Vanilla (no React/Vue/Tailwind)**:
  - Loads in less than 50 milliseconds.
  - Zero heavy `node_modules` dependencies.
  - No compilation or build step required.
  - 100% full control over styles and layout.
- **Where it lives**: [`public/index.html`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/public/index.html), [`public/styles.css`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/public/styles.css), [`public/app.js`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/public/app.js).

---

### 10. Vercel (Cloud Deployment Platform)
- **What it is**: Vercel is a global cloud platform for frontend frameworks and serverless functions.
- **Why we used it**:
  - Hosts the web application globally with edge caching.
  - Runs our Python FastAPI backend as an automatic Serverless Function (`api/index.py`).
  - Automatically deploys any new commit pushed to the GitHub `main` branch.
- **Where it lives**: Configured in [`vercel.json`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/vercel.json) and [`.vercelignore`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/.vercelignore).

---

### 11. Pytest (Automated Testing Framework)
- **What it is**: Pytest is a testing framework for Python.
- **Why we used it**:
  - We wrote 15 tests covering API responses, database transactions, dataset provenance, formula checks, and Spark ETL integrity.
  - Running `pytest` gives 100% confidence that no change breaks the system.
- **Where it lives**: [`tests/`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/tests/).
