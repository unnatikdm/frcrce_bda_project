import pytest
import importlib.util
import json
from pathlib import Path
from influencematch.pipeline import run

def test_pipeline_requires_imported_provenance(tmp_path):
    with pytest.raises(FileNotFoundError, match="No imported dataset"):
        run(tmp_path / "missing", tmp_path / "lake")


@pytest.mark.skipif(importlib.util.find_spec("pyspark") is None, reason="install the optional bigdata extra")
def test_repod_pipeline_writes_parquet_from_imported_source(tmp_path):
    raw = Path("data/active")
    if not (raw / "dataset_manifest.json").is_file():
        pytest.skip("run the permitted RepOD importer first")
    expected = json.loads((raw / "dataset_manifest.json").read_text(encoding="utf-8"))["record_count"]
    assert run(raw, tmp_path / "lake", master="local[2]") == expected
    lake_manifest = json.loads((tmp_path / "lake" / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert lake_manifest["etl_quality_checks"]["creator_id_nonempty_and_unique"] is True
    assert lake_manifest["etl_quality_checks"]["creator_rows"] == expected
    assert lake_manifest["etl_quality_checks"]["reel_creator_references_valid"] is None
    parts = list((tmp_path / "lake" / "creators").glob("part-*.parquet"))
    assert parts
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.master("local[2]").appName("InfluenceMatchParquetTest").getOrCreate()
    try:
        assert spark.read.parquet(str(tmp_path / "lake" / "creators")).count() == expected
    finally:
        spark.stop()
