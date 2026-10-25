import json
from pathlib import Path

import pytest

from influencematch.pipeline import run
from influencematch.tvorog_import import SOURCE_CACHE, import_tvorog


def test_spark_writes_verified_creator_and_reel_parquet(tmp_path):
    if not SOURCE_CACHE.is_file():
        pytest.skip("run the optional checksum-verified Zenodo adapter once to cache its workbook")
    active = tmp_path / "active"
    manifest = import_tvorog(active)
    lake = tmp_path / "lake"

    assert run(active, lake, "local[2]") == manifest["record_count"] == 21
    copied = json.loads((lake / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert copied["reel_count"] == 300
    assert copied["etl_quality_checks"]["creator_id_nonempty_and_unique"] is True
    assert copied["etl_quality_checks"]["reel_id_nonempty_and_unique"] is True
    assert copied["etl_quality_checks"]["reel_creator_references_valid"] is True
    assert copied["etl_quality_checks"]["creator_rows"] == 21
    assert copied["etl_quality_checks"]["reel_rows"] == 300
    assert (lake / "creators" / "_SUCCESS").is_file()
    assert (lake / "reels" / "_SUCCESS").is_file()
