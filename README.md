# InfluenceMatch

> **An Explainable Big Data & NLP Instagram Influencer Recommendation System Backed by Cryptographically Verified Research Data.**

[![Deployment Status](https://img.shields.io/badge/Vercel-Live%20Deployment-000000?style=flat&logo=vercel)](https://influencematch-zeta.vercel.app)
[![API Documentation](https://img.shields.io/badge/Swagger-OpenAPI%203.0-0284c7?style=flat)](https://influencematch-zeta.vercel.app/docs)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776ab?style=flat&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-4.0+-e25a1c?style=flat&logo=apachespark)](https://spark.apache.org)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Tests](https://img.shields.io/badge/Tests-14%20Passed%20%7C%201%20Skipped-10b981?style=flat)]()

---

## Live Links

- **Production Web Application**: [https://influencematch-zeta.vercel.app](https://influencematch-zeta.vercel.app)
- **Interactive Swagger API Docs**: [https://influencematch-zeta.vercel.app/docs](https://influencematch-zeta.vercel.app/docs)
- **GitHub Source Repository**: [https://github.com/unnatikdm/frcrce_bda_project](https://github.com/unnatikdm/frcrce_bda_project)
- **Simple English Documentation**: [documents_for_project/](documents_for_project/)

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Technologies & Tools Used](#technologies--tools-used)
5. [Strict Zero-Synthetic Data Policy](#strict-zero-synthetic-data-policy)
6. [Datasets & Provenance](#datasets--provenance)
7. [Quick Start (Local Setup)](#quick-start-local-setup)
8. [Running Components](#running-components)
9. [Automated Testing & Quality Verification](#automated-testing--quality-verification)
10. [Documentation Index](#documentation-index)
11. [Academic Citation](#academic-citation)

---

## Overview

**InfluenceMatch** is an end-to-end Big Data engineering and recommendation platform that helps brands and businesses find the right Instagram creators for marketing campaigns.

Unlike generic tools that use black-box formulas or fabricate simulated profiles, InfluenceMatch is built upon a **100% authentic data philosophy**:
- Every creator profile is an observed real account from peer-reviewed, openly licensed research datasets.
- Every recommendation score is mathematically traceable back to source data and explicit formulas.
- All datasets are validated through cryptographic SHA-256 and MD5 checksum manifests before processing.
- The interface strictly rejects visual clutter and emojis in favor of a minimalist, high-contrast, production-grade design system.

---

## Key Features

- **Natural Language Campaign Brief Matching**: Businesses can submit natural briefs (e.g., *"fitness and lifestyle creators"* or *"beauty skincare nano influencers"*).
- **Explainable Ranking**: Transparent score explanations break down term cosine weights, observed judge ratings, and formula numerators/denominators.
- **Big Data Analytics Pipeline**: Powered by Apache Spark to clean data, validate relational schemas, and store columnar Snappy-compressed Parquet tables.
- **Transactional Database Backend**: PostgreSQL snapshot storage with SQL queries calculating follower percentiles, niche coverage, and engagement aggregations.
- **Reference Engagement Quartiles**: Descriptive comparisons against dated industry quartiles from Cheerful.ai (5,924 accounts) without distorting rank scores.
- **Dual User Interfaces**:
  - **Cloud Web Application**: Ultra-fast, zero-dependency, full light theme client running on Vercel Edge.
  - **Local Data Science Dashboard**: Streamlit application for deep exploratory data analysis and JSON trace exports.

---

## System Architecture

```mermaid
graph TD
    subgraph "1. Data Acquisition & Integrity"
        DS1["RepOD Research Dataset<br/>(392 Real Creators, CC BY 4.0)"]
        DS2["Zenodo Reels Dataset<br/>(300 Real Reels, 21 Accounts)"]
        DS3["Cheerful Engagement Benchmarks<br/>(5,924 Accounts Reference)"]
        MAN["Provenance Manifest & SHA-256 Verifier"]
        DS1 --> MAN
        DS2 --> MAN
    end

    subgraph "2. Big Data & Storage Layer"
        SPK["Apache Spark ETL Engine<br/>(PySpark local[2])"]
        PQT["Snappy Columnar Parquet Lake<br/>(Partitioned Tables)"]
        PG["PostgreSQL 16 Database<br/>(Atomic Snapshots & SQL Analytics)"]
        MAN --> SPK
        SPK --> PQT
        SPK --> PG
    end

    subgraph "3. Scoring & Intelligence Engine"
        TF["Scikit-Learn TF-IDF Vectorizer"]
        COS["Cosine Similarity Matcher"]
        OPL["Judge-Rated Opinion Leadership Formula<br/>(6-Item Composite Mean)"]
        REF["Quartile Band Comparator"]
        MAN --> TF
        TF --> COS
        COS --> OPL
        DS3 --> REF
        OPL --> REF
    end

    subgraph "4. Serving & User Interfaces"
        API["FastAPI Serverless Backend<br/>(/api/match, /api/creators, /api/dataset)"]
        WEB["Vercel Cloud Web App<br/>(Full Light Theme, Vanilla JS/CSS)"]
        DASH["Local Streamlit Dashboard<br/>(Big Data Analytics & SQL Views)"]
        REF --> API
        PG --> API
        API --> WEB
        API --> DASH
    end
```

---

## Technologies & Tools Used

| Tool / Library | Role in InfluenceMatch |
| :--- | :--- |
| **Python (3.12 / 3.13)** | Core programming language for processing, APIs, and models |
| **FastAPI & Starlette** | High-performance asynchronous REST API framework |
| **Apache Spark (PySpark 4.0+)** | Distributed Big Data ETL engine for schema validation and lake processing |
| **Apache Parquet** | Snappy-compressed columnar file format for fast, scalable analytics |
| **PostgreSQL 16** | Relational database for atomic snapshot transactions and SQL analytics |
| **Docker & Docker Compose** | Isolated container environment for running PostgreSQL locally |
| **Scikit-Learn & SciPy** | Natural Language Processing (TF-IDF) and Cosine Similarity math |
| **Streamlit** | Python web application framework for local data exploration |
| **Vanilla HTML5, CSS3, JS** | Lightweight, zero-framework, full light theme frontend deployed to Vercel |
| **Vercel** | Global cloud deployment for web frontend and Serverless Python functions |
| **Pytest** | Automated testing suite with 15 behavioral and data integrity tests |
| **Git & GitHub** | Source control and continuous integration trigger for Vercel |

*For in-depth explanations of every tool in simple English, see [documents_for_project/02_ALL_TOOLS_AND_TECHNOLOGIES.md](documents_for_project/02_ALL_TOOLS_AND_TECHNOLOGIES.md).*

---

## Strict Zero-Synthetic Data Policy

InfluenceMatch enforces non-negotiable data integrity principles:
1. **Never fabricate records**: No mock influencer accounts, artificial follower counts, or generated campaign outcomes.
2. **Fail transparently**: When an attribute (such as audience gender or per-deliverable pricing) is missing from real datasets, the system explicitly reports that limitation rather than inventing synthetic defaults.
3. **Cryptographic validation**: Every file processed must match its recorded SHA-256 and MD5 digests.

---

## Datasets & Provenance

InfluenceMatch uses three openly licensed real research datasets:

| Dataset | Records | License | Source & Citation |
| :--- | :--- | :--- | :--- |
| **Judge-rated dataset of nano- and micro-influencers** | 392 Profiles | CC-BY-4.0 | Korzyński & Protsiuk (2026), RepOD, DOI [10.18150/KUW9CA](https://doi.org/10.18150/KUW9CA) |
| **Educational Instagram Reels** | 300 Reels, 21 Accounts | CC-BY-4.0 | Grigorii Tvorogov (2026), Zenodo, DOI [10.5281/zenodo.23301344](https://doi.org/10.5281/zenodo.23301344) |
| **Instagram Engagement Benchmarks** | 5,924 Accounts Reference | CC-BY-4.0 | Cheerful.ai Research (Aug-Sep 2026 quartile reference bands) |

*For complete dataset analysis, limitations, and verification manifests, see [documents_for_project/03_DATASETS_AND_AUTHENTICITY.md](documents_for_project/03_DATASETS_AND_AUTHENTICITY.md).*

---

## Quick Start (Local Setup)

Clone the repository and set up a Python virtual environment:

```powershell
# 1. Clone repository
git clone git@github.com:unnatikdm/frcrce_bda_project.git
cd frcrce_bda_project

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
python -m pip install --upgrade pip
pip install -e ".[test,repod,dashboard]"
```

---

## Running Components

### Option 1: Run the Interactive Local Dashboard (Streamlit)
```powershell
streamlit run src/influencematch/dashboard.py --server.address 127.0.0.1
```
Open your browser at `http://127.0.0.1:8501`.

### Option 2: Run the Local FastAPI Server
```powershell
uvicorn influencematch.api:app --reload --port 8000
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

### Option 3: Run with Docker Compose & PostgreSQL
```powershell
# Start PostgreSQL container on port 55432
docker compose up -d --wait postgres

# Load dataset snapshot into PostgreSQL
python -m influencematch.db

# Run API in PostgreSQL-backed mode
$env:INFLUENCEMATCH_DATA_BACKEND = "postgres"
$env:DATABASE_URL = "postgresql://influence:influence@localhost:55432/influence"
uvicorn influencematch.api:app --reload
```

### Option 4: Run Apache Spark ETL Pipeline
```powershell
pip install -e ".[bigdata]"
python -m influencematch.pipeline --master "local[2]"
```

---

## Automated Testing & Quality Verification

All behavior, data integrity rules, and API endpoints are validated via automated tests:

```powershell
pytest
```

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

- Zero emoji leaks verified via automated AST / regex scanning across all code, templates, and UI assets.
- Live Vercel deployment verified across desktop and mobile viewports.
- Complete audit sign-off details are recorded in [`VERIFICATION_REPORT.md`](file:///c:/Users/elonm/OneDrive/Projects/bda_social%20media/VERIFICATION_REPORT.md).

---

## Documentation Index

Explore our plain-English documentation guides in the [`documents_for_project/`](documents_for_project/) folder:

- **[01. Project Summary](documents_for_project/01_PROJECT_SUMMARY.md)**: What problem InfluenceMatch solves and how it works.
- **[02. Technologies & Tools](documents_for_project/02_ALL_TOOLS_AND_TECHNOLOGIES.md)**: Explanation of every language, library, and tool.
- **[03. Datasets & Authenticity](documents_for_project/03_DATASETS_AND_AUTHENTICITY.md)**: Details on our real CC-BY-4.0 datasets and hash integrity.
- **[04. System Architecture & Data Flow](documents_for_project/04_STEP_BY_STEP_ARCHITECTURE.md)**: Mermaid diagram and end-to-end data pipeline.
- **[05. How to Run, Test & Deploy](documents_for_project/05_HOW_TO_RUN_EVERYTHING.md)**: Step-by-step instructions for local execution and cloud deployment.

---

## Academic Citation

If you use or reference InfluenceMatch in academic research or project coursework, please cite:

```bibtex
@misc{influencematch2026,
  title={InfluenceMatch: Big Data-Driven Instagram Influencer Recommendation System},
  author={Unnati Kadam},
  year={2026},
  publisher={GitHub},
  howpublished={\url{https://github.com/unnatikdm/frcrce_bda_project}}
}
```

Primary dataset citation:
> Korzyński, P., & Protsiuk, O. (2026). *Judge-rated dataset of nano- and micro-influencers*. RepOD, DOI: [10.18150/KUW9CA](https://doi.org/10.18150/KUW9CA), Creative Commons Attribution 4.0.
