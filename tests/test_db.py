"""Optional PostgreSQL integration checks; set DATABASE_URL to enable."""
import json
import os
from pathlib import Path

import psycopg
import pytest

from influencematch.db import load_creators


def test_postgres_load_serves_real_source_rows_and_recommendations(monkeypatch):
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("set DATABASE_URL to run the optional PostgreSQL integration test")

    data_dir = Path(os.environ.get("INFLUENCEMATCH_TEST_DATA_DIR", "data/active"))
    manifest = json.loads((data_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    loaded = load_creators(data_dir / "creators.jsonl", database_url)
    assert loaded == manifest["record_count"]

    with psycopg.connect(database_url) as conn:
        rows, null_engagement = conn.execute(
            "SELECT count(*), count(*) FILTER (WHERE engagement_rate IS NULL) FROM creators"
        ).fetchone()
        reels = conn.execute("SELECT count(*) FROM reels").fetchone()[0]

    assert rows == manifest["record_count"]
    assert null_engagement == manifest["record_count"]
    assert reels == manifest.get("reel_count", 0)

    monkeypatch.setenv("INFLUENCEMATCH_DATA_BACKEND", "postgres")
    from fastapi.testclient import TestClient
    from influencematch.api import app

    client = TestClient(app)
    state = client.get("/dataset").json()
    assert state["status"] == "available"
    assert state["backend"] == "postgres"
    assert state["profiles_loaded"] == manifest["record_count"]
    assert len(state["database_snapshot_sha256"]) == 64
    is_reels = manifest.get("dataset_key") == "zenodo_23301344_educational_reels"
    brief = "science education" if is_reels else "fitness campaign"
    result = client.post("/match", json={"brief": brief, "limit": 5})
    assert result.status_code == 200
    assert result.json()["result_count"] > 0
    assert result.json()["dataset"]["database_snapshot_sha256"] == state["database_snapshot_sha256"]
    expected_method = "cosine similarity" if is_reels else "niche overlap"
    assert all(item["score_method"].startswith(expected_method) for item in result.json()["results"])
    summary_response = client.get("/analytics/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["sql_backend"] == "PostgreSQL"
    assert summary["creator_count"] == manifest["record_count"]
    assert summary["reel_count"] == manifest.get("reel_count", 0)
    assert summary["database_snapshot_sha256"] == state["database_snapshot_sha256"]
    if is_reels:
        assert sum(topic["post_count"] for topic in summary["reel_topic_summary"]) == manifest["reel_count"]
        assert all(topic["views_are_approximate"] for topic in summary["reel_topic_summary"])
    else:
        assert {item["niche"] for item in summary["niche_creator_counts"]} == {"fitness", "beauty", "lifestyle", "travel"}

    from streamlit.testing.v1 import AppTest

    dashboard = AppTest.from_file(
        str(Path(__file__).parents[1] / "src" / "influencematch" / "dashboard.py")
    ).run(timeout=20)
    assert not dashboard.exception
    assert any("PostgreSQL SQL source summary" in item.label for item in dashboard.expander)
    dashboard.text_area[0].set_value(brief)
    dashboard.run(timeout=20)
    dashboard.button[0].click()
    dashboard.run(timeout=20)
    assert not dashboard.exception
    assert dashboard.dataframe
    assert any("score_explanation" in table.value.columns for table in dashboard.dataframe)
