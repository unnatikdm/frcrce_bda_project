from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_dashboard_renders_unavailable_state_without_dataset(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app=Path(__file__).parents[1] / "src" / "influencematch" / "dashboard.py"
    result=AppTest.from_file(str(app)).run(timeout=10)
    assert not result.exception
    assert "No imported real dataset is available" in result.warning[0].value
    assert "No profiles or recommendation scores are shown" in result.info[0].value
