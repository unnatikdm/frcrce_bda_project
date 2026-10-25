"""Local Spark ETL for imported creators with verified source provenance."""
import argparse
import json
import os
from pathlib import Path
import shutil
from datetime import datetime, timezone
from .provenance import provenance_fields_present, sha256_file


def _assert_unique_nonempty(df, column: str, label: str) -> int:
    from pyspark.sql import functions as F

    identifier = F.col(column)
    invalid_identifier = identifier.isNull() | (F.length(F.trim(identifier)) == 0)
    metrics = df.agg(
        F.count(F.lit(1)).alias("rows"),
        F.countDistinct(identifier).alias("distinct_ids"),
        F.sum(F.when(invalid_identifier, 1).otherwise(0)).alias("invalid_ids"),
    ).first()
    if metrics["invalid_ids"] or 0:
        raise ValueError(f"Spark {label} contains a missing or empty {column}")
    if metrics["rows"] != metrics["distinct_ids"]:
        raise ValueError(f"Spark {label} contains duplicate {column} values")
    return metrics["rows"]

def run(raw: Path, lake: Path, master: str = "local[2]") -> int:
    manifest_path = raw / "dataset_manifest.json"
    creators_path = raw / "creators.jsonl"
    if not manifest_path.is_file() or not creators_path.is_file():
        raise FileNotFoundError("No imported dataset. Run influencematch.import_data with a permitted source first.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not provenance_fields_present(manifest):
        raise ValueError("Dataset provenance is incomplete")
    if sha256_file(creators_path) != manifest.get("imported_file_sha256"):
        raise ValueError("Creator data hash does not match its provenance manifest")
    reels_path = raw / str(manifest.get("reels_file", "reels.jsonl")) if manifest.get("reels_file") else None
    if reels_path is not None:
        if not reels_path.is_file():
            raise FileNotFoundError("Provenance manifest declares Reel records but reels.jsonl is missing")
        if sha256_file(reels_path) != manifest.get("reels_file_sha256"):
            raise ValueError("Reel data hash does not match its provenance manifest")
    elif manifest.get("reel_count"):
        raise ValueError("Provenance manifest declares Reel rows without a Reel data file")
    lake.mkdir(parents=True, exist_ok=True)
    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.appName("InfluenceMatchLocalETL").master(master)
             .config("spark.sql.shuffle.partitions", "4")
             .config("spark.driver.memory", "2g").getOrCreate())
    try:
        creators = spark.read.json(str(creators_path))
        count = _assert_unique_nonempty(creators, "creator_id", "creator table")
        if count != manifest.get("record_count"):
            raise ValueError("Spark creator row count does not match the provenance manifest")
        reel_count = 0
        reels = None
        reels_target = lake / "reels"
        if reels_path is not None:
            reels = spark.read.json(str(reels_path))
            reel_count = _assert_unique_nonempty(reels, "video_id", "Reel table")
            if reel_count != manifest.get("reel_count"):
                raise ValueError("Spark Reel row count does not match the provenance manifest")
            from pyspark.sql import functions as F
            missing_creator = (reels.select("creator_id").distinct()
                               .join(creators.select("creator_id").distinct(), "creator_id", "left_anti")
                               .limit(1).count())
            if missing_creator:
                raise ValueError("Spark Reel table contains creator_id values absent from the creator table")

        # All source integrity checks happen before replacing lake outputs.
        creators.write.mode("overwrite").parquet(str(lake / "creators"))
        if reels is not None:
            reels.write.mode("overwrite").parquet(str(reels_target))
        elif reels_target.exists():
            resolved_lake, resolved_target = lake.resolve(), reels_target.resolve()
            if reels_target.is_symlink() or resolved_target.parent != resolved_lake:
                raise ValueError("Refusing to remove a Reel lake path that resolves outside the selected data lake")
            shutil.rmtree(resolved_target)
        lake_manifest = dict(manifest)
        lake_manifest["etl_quality_checks"] = {
            "verified_at_utc": datetime.now(timezone.utc).isoformat(),
            "creator_id_nonempty_and_unique": True,
            "creator_rows": count,
            "reel_id_nonempty_and_unique": True if reels is not None else None,
            "reel_creator_references_valid": True if reels is not None else None,
            "reel_rows": reel_count,
        }
        (lake / "dataset_manifest.json").write_text(json.dumps(lake_manifest, indent=2), encoding="utf-8")
        return count
    finally:
        spark.stop()

if __name__ == "__main__":
    local_data_home = Path(os.environ.get("LOCALAPPDATA", os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))))
    default_lake = local_data_home / "InfluenceMatch" / "data-lake"
    parser=argparse.ArgumentParser(); parser.add_argument("--raw", type=Path, default=Path("data/active")); parser.add_argument("--lake", type=Path, default=default_lake); parser.add_argument("--master", default="local[2]")
    args=parser.parse_args()
    creator_count=run(args.raw, args.lake, args.master)
    manifest=json.loads((args.raw / "dataset_manifest.json").read_text(encoding="utf-8"))
    print(f"Wrote {creator_count} creator and {manifest.get('reel_count', 0)} Reel records to the local Parquet lake")
