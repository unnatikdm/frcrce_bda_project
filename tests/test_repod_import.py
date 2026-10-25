import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from influencematch import api, repod_import
from influencematch.api import dataset_state
from influencematch.matching import match
from influencematch.evaluate import evaluate
from influencematch.export import build_recommendation_export


def test_repod_source_checksum_and_import(tmp_path, monkeypatch):
    source_path = Path("data/source/repod_kuw9ca/source.ods")
    if not source_path.is_file():
        pytest.skip("run the optional RepOD import once to cache the verified source file")
    source = source_path.read_bytes()
    assert hashlib.md5(source).hexdigest() == repod_import.EXPECTED_MD5
    monkeypatch.setattr(repod_import, "SOURCE_CACHE", source_path)

    class Response:
        content = source

        @staticmethod
        def raise_for_status():
            pass

    monkeypatch.setattr(repod_import.requests, "get", lambda *a, **kw: Response())
    manifest = repod_import.import_repod(tmp_path / "active")
    assert manifest["record_count"] == 392
    assert manifest["source_observation_count"] == 393
    assert manifest["excluded_missing_creator_identifier"] == 1
    assert manifest["source_metric_non_null_counts"]["audience_quality_score"] > 0
    assert manifest["research_rating_non_null_profile_counts"]["opinion_leadership"] > 0
    assert manifest["source_formula_error_cells"].get("Aver_median_income", 0) == 1
    assert manifest["license_id"] == "CC-BY-4.0"
    assert "Not disclosed" in manifest["source_collection_date"]
    profiles = dataset_state_for(tmp_path / "active")
    assert len(profiles) == 392
    assert any(p["niches"] for p in profiles)
    assert any(p["research_ratings"].get("opinion_leadership") is not None for p in profiles)
    assert any(p.get("source_metrics", {}).get("audience_quality_score") is not None for p in profiles)
    assert any(p.get("source_metrics", {}).get("compensation_source_value") is not None for p in profiles)
    assert all("currency" in p["source_metric_note"] for p in profiles)
    results = match(profiles, "fitness", 5)
    assert results
    assert all("fitness" in p["matched_terms"] for p in results)
    assert all("historical research measure" in p["score_method"] for p in results)
    assert all(p["score_explanation"]["method"] == "mean_of_observed_source_rating_items" for p in results)
    assert all(p["score_explanation"]["observed_item_count"] > 0 for p in results)
    assert all(p["match_score"] == round(p["research_ratings"]["opinion_leadership"], 4) for p in results)
    for result in results:
        trace = result["score_explanation"]
        assert trace["observed_item_count"] == len(trace["observed_items"])
        assert trace["numerator"] == sum(trace["observed_items"].values())
        assert trace["unrounded_value"] == pytest.approx(trace["numerator"] / trace["observed_item_count"])
    export = build_recommendation_export(manifest, "available", {"brief": "fitness", "limit": 5}, results)
    serialized_export = json.loads(json.dumps(export, allow_nan=False))
    assert serialized_export["dataset"]["imported_file_sha256"] == manifest["imported_file_sha256"]
    assert serialized_export["result_count"] == len(results)
    assert serialized_export["results"][0]["score_explanation"] == results[0]["score_explanation"]
    assert serialized_export["results"][0]["engagement_reference"]["status"] == "unavailable"
    evaluation = evaluate(tmp_path / "active")
    assert evaluation["records_loaded"] == 392
    assert evaluation["overall"]["n"] == 392
    assert evaluation["overall"]["spearman_rho"] is not None
    assert "not independent" in evaluation["evaluation_type"]
    ranking = evaluation["ranking_evaluation"]
    assert ranking["overall"]["k"] == 10
    assert ranking["overall"]["opinion_leadership_ndcg"] is not None
    assert ranking["overall"]["follower_count_baseline_ndcg"] is not None
    assert "not a held-out evaluation" in ranking["scope"]
    candidate_folds = ranking["candidate_fold_diagnostic"]
    assert candidate_folds["folds"] == 5
    assert sum(fold["n"] for fold in candidate_folds["fold_results"]) == candidate_folds["n"]
    assert candidate_folds["opinion_leadership_ndcg_mean"] is not None
    assert "not model cross-validation" in candidate_folds["scope"]
    assert "not independent outcome or campaign validation" in candidate_folds["scope"]
    assert evaluate(tmp_path / "active")["ranking_evaluation"]["candidate_fold_diagnostic"]["fold_results"] == candidate_folds["fold_results"]
    monkeypatch.setattr(api, "DATA", tmp_path / "active")
    client = TestClient(api.app)
    assert client.get("/dataset").json()["status"] == "available"
    response = client.post("/match", json={"brief": "fitness", "limit": 5})
    assert response.status_code == 200
    assert response.json()["result_count"] > 0
    assert response.json()["dataset"]["license_id"] == "CC-BY-4.0"
    assert response.json()["dataset"]["imported_file_sha256"] == manifest["imported_file_sha256"]
    assert response.json()["dataset"]["retrieved_at_utc"] == manifest["retrieved_at_utc"]
    assert "historical judge-rated opinion leadership" in response.json()["note"]
    assert "observed_item_count" in response.json()["results"][0]["score_explanation"]
    assert "TF-IDF" not in response.json()["note"]
    assert all(result["engagement_reference"]["status"] == "unavailable" for result in response.json()["results"])
    assert client.post("/match", json={"brief": "fitness", "creator_country": "US"}).status_code == 422
    assert client.post("/match", json={"brief": "fitness", "min_engagement_rate": 0.05}).status_code == 422
    budget_response = client.post("/match", json={"brief": "fitness", "budget_amount": 100, "budget_currency": "USD", "rate_deliverable": "instagram_reel"})
    assert budget_response.status_code == 422
    assert "no complete per-deliverable creator rates" in budget_response.json()["detail"]
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    dashboard = AppTest.from_file(str(Path(__file__).parents[1] / "src" / "influencematch" / "dashboard.py")).run(timeout=20)
    dashboard.text_area[0].set_value("fitness campaign")
    dashboard.run(timeout=20)
    dashboard.button[0].click()
    dashboard.run(timeout=20)
    assert not dashboard.exception
    assert dashboard.dataframe
    assert len(dashboard.download_button) == 1
    assert "score traces" in dashboard.download_button[0].label
    assert not dashboard.text_input
    assert all("engagement rate" not in item.label.casefold() for item in dashboard.number_input)
    columns = dashboard.dataframe[0].value.columns
    assert "audience_quality_score" in columns
    assert "historical_opinion_leadership" in columns
    assert "opinion_leadership_items_used" in columns
    assert "score_explanation" in columns


def test_repod_refuses_changed_download(tmp_path, monkeypatch):
    class Response:
        content = b"not the published dataset"

        @staticmethod
        def raise_for_status():
            pass

    monkeypatch.setattr(repod_import.requests, "get", lambda *a, **kw: Response())
    monkeypatch.setattr(repod_import, "SOURCE_CACHE", tmp_path / "not-cached.ods")
    with pytest.raises(ValueError, match="checksum mismatch"):
        repod_import.import_repod(tmp_path)


def dataset_state_for(path):
    import json
    from influencematch.provenance import sha256_file

    manifest_path = path / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data = path / "creators.jsonl"
    assert manifest["imported_file_sha256"] == sha256_file(data)
    return [json.loads(line) for line in data.read_text(encoding="utf-8").splitlines()]
