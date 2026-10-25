import pytest
from influencematch.import_data import import_creators

def test_import_refuses_without_rights_attestation(tmp_path):
    source=tmp_path / "input.csv"
    source.write_text("creator_id,handle,platform\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Import refused"):
        import_creators(source, tmp_path / "out", source_name="", source_url="", license_id="", source_date="2025-01-01", rights_confirmed=False)

def test_import_requires_traceable_license_fields(tmp_path):
    source=tmp_path / "input.csv"
    source.write_text("creator_id,handle,platform\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Source name, source URL, and license"):
        import_creators(source, tmp_path / "out", source_name="declared source", source_url="https://example.invalid", license_id="", source_date="2025-01-01", rights_confirmed=True)
