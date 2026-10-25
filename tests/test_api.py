from fastapi.testclient import TestClient
from influencematch import api

def test_api_reports_missing_real_dataset(tmp_path, monkeypatch):
    monkeypatch.delenv("INFLUENCEMATCH_DATA_BACKEND", raising=False)
    monkeypatch.setattr(api, "DATA", tmp_path / "active")
    client=TestClient(api.app)
    health=client.get("/health").json()
    assert health["dataset"]["status"] == "unavailable"
    assert health["dataset"]["profiles_loaded"] == 0
    response=client.post("/match", json={"brief":"travel creators"})
    assert response.status_code == 503
    assert "No imported real dataset" in response.json()["detail"]["reason"]
    sql_summary = client.get("/analytics/summary")
    assert sql_summary.status_code == 409
    assert "require INFLUENCEMATCH_DATA_BACKEND=postgres" in sql_summary.json()["detail"]


def test_api_rejects_incomplete_provenance_before_reading_profiles(tmp_path, monkeypatch):
    from pathlib import Path
    import json
    data = tmp_path / "active"
    data.mkdir()
    (data / "creators.jsonl").write_text("not valid creator JSON\n", encoding="utf-8")
    (data / "dataset_manifest.json").write_text(json.dumps({"record_count": 1}), encoding="utf-8")
    monkeypatch.setattr(api, "DATA", data)
    state = TestClient(api.app).get("/dataset").json()
    assert state["status"] == "invalid"
    assert state["reason"] == "Dataset provenance is incomplete."
