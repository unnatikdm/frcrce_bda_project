"""
InfluenceIQ - End-to-End PySpark ETL Pipeline Orchestrator
Coordinates: Ingestion -> PySpark Cleaning -> Feature Engineering -> Partitioned Parquet Persistence.
"""

import os
import time
from typing import Dict, Any, Tuple
from pyspark.sql import SparkSession, DataFrame

from src.data_ingestion import get_spark_session, load_raw_influencers, load_niche_benchmarks
from src.data_cleaning import clean_influencer_data
from src.feature_engineering import engineer_influencer_features, save_to_parquet, read_from_parquet


def run_etl(
    spark: SparkSession,
    raw_path: str = "data/raw/influencers_raw.csv",
    benchmark_path: str = "data/benchmarks/niche_benchmarks.csv",
    output_parquet_path: str = "data/processed/influencers_parquet"
) -> Tuple[DataFrame, Dict[str, Any]]:
    """
    Executes the complete PySpark ETL batch pipeline:
      1. Ingestion: Reads raw CSV/JSON with schema enforcement.
      2. Cleaning: Deduplication, text normalization, null imputation, constraint checks.
      3. Feature Engineering: KPI calculations, broadcast join with benchmarks.
      4. Persistence: Saves partitioned Parquet files with snappy compression.
    """
    start_time = time.perf_counter()
    print(f"[ETL] Starting batch processing pipeline...")

    # 1. Ingestion
    raw_df = load_raw_influencers(spark, raw_path)
    ingest_count = raw_df.count()
    print(f"[ETL] Ingested {ingest_count:,} raw records.")

    # 2. Cleaning
    clean_df, quality_metrics = clean_influencer_data(raw_df)
    clean_count = clean_df.count()
    print(f"[ETL] Cleaned data: {clean_count:,} records retained ({quality_metrics['clean_retention_pct']}%).")

    # 3. Reference benchmarks & broadcast join
    benchmarks_df = None
    if os.path.exists(benchmark_path):
        benchmarks_df = load_niche_benchmarks(spark, benchmark_path)
        print(f"[ETL] Loaded niche benchmarks for broadcast join.")

    # 4. Feature Engineering
    features_df = engineer_influencer_features(clean_df, benchmarks_df)

    # 5. Parquet Columnar Persistence (Partitioned by primary_niche)
    os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
    print(f"[ETL] Persisting partitioned Parquet dataset to: {output_parquet_path}...")
    save_to_parquet(features_df, output_parquet_path, partition_by="primary_niche", mode="overwrite")

    # Read back to verify Parquet integrity
    persisted_df = read_from_parquet(spark, output_parquet_path)

    elapsed = round(time.perf_counter() - start_time, 2)
    print(f"[ETL] Batch ETL complete in {elapsed} seconds.")

    etl_metadata = {
        "pipeline_duration_seconds": elapsed,
        "input_records": ingest_count,
        "output_records": clean_count,
        "quality_metrics": quality_metrics,
        "output_path": output_parquet_path,
        "partition_column": "primary_niche"
    }

    return persisted_df, etl_metadata


if __name__ == "__main__":
    spark = get_spark_session("InfluenceIQ-ETL")
    df, meta = run_etl(spark)
    print("ETL Metadata:", meta)
    spark.stop()
