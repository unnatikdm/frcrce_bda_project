import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from influencematch import api
from influencematch.evaluate_tvorog import evaluate
from influencematch.export import build_recommendation_export
from influencematch.tvorog_import import EXPECTED_MD5, SOURCE_CACHE, import_tvorog


def test_zenodo_reels_import_api_and_dashboard_use_published_source(tmp_path, monkeypatch):
    if not SOURCE_CACHE.is_file():
        pytest.skip("run the optional checksum-verified Zenodo adapter once to cache its workbook")
    assert hashlib.md5(SOURCE_CACHE.read_bytes()).hexdigest() == EXPECTED_MD5
    destination = tmp_path / "active"
    manifest = import_tvorog(destination)

    assert manifest["license_id"] == "CC-BY-4.0"
    assert manifest["record_count"] == 21
    assert manifest["reel_count"] == 300
    assert manifest["source_collection_window"] == {"start": "2026-09-02", "end": "2026-10-01"}
    profiles = [json.loads(line) for line in (destination / "creators.jsonl").read_text(encoding="utf-8").splitlines()]
    reels = [json.loads(line) for line in (destination / "reels.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(profiles) == 21
    assert len(reels) == 300
    assert all(profile["source_metrics"]["reels_observed"] > 0 for profile in profiles)
    assert all("No likes are supplied" in profile["source_metric_note"] for profile in profiles)
    evaluation = evaluate(destination)
    assert evaluation["reels_evaluated"] == 300
    assert evaluation["tfidf_topic_retrieval"]["mrr"] is not None
    assert evaluation["follower_count_baseline"]["queries"] == 300
    assert "not creator-level holdout" in evaluation["evaluation_type"]

    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.setattr(api, "DATA", destination)
    client = TestClient(api.app)
    response = client.post("/match", json={"brief": "science education", "limit": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["result_count"] > 0
    assert body["dataset"]["imported_file_sha256"] == manifest["imported_file_sha256"]
    assert body["dataset"]["reels_file_sha256"] == manifest["reels_file_sha256"]
    assert "300 observed educational Reels" in body["note"]
    assert body["results"][0]["match_score"] > 0
    assert body["results"][0]["score_explanation"]["method"] == "tfidf_cosine_similarity"
    assert body["results"][0]["score_explanation"]["value"] == body["results"][0]["match_score"]
    trace = body["results"][0]["score_explanation"]
    assert trace["term_contributions"]
    assert trace["contribution_sum"] == pytest.approx(trace["unrounded_value"])
    assert {term["term"] for term in trace["term_contributions"]} == set(body["results"][0]["matched_terms"])
    export = build_recommendation_export(manifest, "available", {"brief": "science education", "limit": 10}, body["results"])
    serialized_export = json.loads(json.dumps(export, allow_nan=False))
    assert serialized_export["dataset"]["reels_file_sha256"] == manifest["reels_file_sha256"]
    assert serialized_export["result_count"] == len(body["results"])
    assert serialized_export["results"][0]["score_explanation"] == trace
    assert serialized_export["results"][0]["engagement_reference"]["status"] == "unavailable"
    assert body["results"][0]["source_metrics"]["mean_views"] >= 0
    assert body["results"][0]["engagement_reference"]["status"] == "unavailable"
    assert client.post("/match", json={"brief": "science", "creator_country": "US"}).status_code == 422
    budget = client.post("/match", json={"brief": "science", "budget_amount": 100, "budget_currency": "USD", "rate_deliverable": "instagram_reel"})
    assert budget.status_code == 422

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    dashboard = AppTest.from_file(str(Path(__file__).parents[1] / "src" / "influencematch" / "dashboard.py")).run(timeout=20)
    assert not dashboard.exception
    assert any("300 educational Reels" in element.value for element in dashboard.info)
    dashboard.text_area[0].set_value("science education")
    dashboard.run(timeout=20)
    dashboard.button[0].click()
    dashboard.run(timeout=20)
    assert not dashboard.exception
    assert dashboard.dataframe
    assert len(dashboard.download_button) == 1
    assert "score traces" in dashboard.download_button[0].label


def test_api_rejects_tampered_real_reel_artifact(tmp_path, monkeypatch):
    if not SOURCE_CACHE.is_file():
        pytest.skip("run the optional checksum-verified Zenodo adapter once to cache its workbook")
    destination = tmp_path / "active"
    import_tvorog(destination)
    reels_path = destination / "reels.jsonl"
    reels_path.write_bytes(reels_path.read_bytes() + b"\n")

    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.delenv("INFLUENCEMATCH_DATA_BACKEND", raising=False)
    monkeypatch.setattr(api, "DATA", destination)
    loaded, state = api.dataset_state()
    assert loaded is None
    assert state["status"] == "invalid"
    assert "Reel data hash" in state["reason"]
