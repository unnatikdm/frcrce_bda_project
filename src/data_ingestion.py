"""
InfluenceIQ - Big Data Ingestion Module
Handles SparkSession lifecycle and schema-enforced data ingestion from CSV and JSON.
Demonstrates:
  - SparkSession configuration for local mode ('local[*]')
  - Schema-on-read enforcement with StructType
  - Multi-format ingestion (CSV, JSON)
"""

import os
from typing import Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, BooleanType, LongType
)

# Explicit Schema Definition for Schema-on-Read validation
INFLUENCER_SCHEMA = StructType([
    StructField("influencer_id", StringType(), False),
    StructField("username", StringType(), False),
    StructField("full_name", StringType(), True),
    StructField("primary_niche", StringType(), True),
    StructField("secondary_niche", StringType(), True),
    StructField("followers_count", DoubleType(), True),
    StructField("following_count", DoubleType(), True),
    StructField("posts_count", DoubleType(), True),
    StructField("avg_likes", DoubleType(), True),
    StructField("avg_comments", DoubleType(), True),
    StructField("avg_video_views", DoubleType(), True),
    StructField("location_city", StringType(), True),
    StructField("location_country", StringType(), True),
    StructField("audience_top_country", StringType(), True),
    StructField("audience_top_city", StringType(), True),
    StructField("audience_age_group", StringType(), True),
    StructField("audience_gender_female_pct", DoubleType(), True),
    StructField("is_verified", BooleanType(), True),
    StructField("avg_post_frequency_per_week", DoubleType(), True),
    StructField("estimated_cost_per_post_inr", DoubleType(), True)
])

BENCHMARK_SCHEMA = StructType([
    StructField("primary_niche", StringType(), False),
    StructField("benchmark_engagement_rate", DoubleType(), False),
    StructField("benchmark_cpm_inr", DoubleType(), False),
    StructField("niche_market_demand", StringType(), True)
])


def get_spark_session(app_name: str = "InfluenceIQ-Analytics") -> SparkSession:
    """
    Initializes or retrieves an active PySpark session.
    Configured for local execution on a multi-core machine (local[*]).
    Optimizes shuffle partitions to 4 to prevent partition bloat on single-node execution.
    """
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName(app_name)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.default.parallelism", "2")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.ui.enabled", "false")  # Avoid port conflicts during automated runs
        .getOrCreate()
    )
    # Suppress verbose JVM log messages to keep console outputs clear
    spark.sparkContext.setLogLevel("WARN")
    return spark


def load_raw_influencers(
    spark: SparkSession,
    file_path: str,
    file_format: str = "auto",
    enforce_schema: bool = True
) -> DataFrame:
    """
    Loads raw influencer profiles from disk.
    Supports CSV and JSON formats with explicit schema validation.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found at: {file_path}")

    # Determine format if auto
    if file_format == "auto":
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            file_format = "csv"
        elif ext == ".json":
            file_format = "json"
        else:
            raise ValueError(f"Unsupported file extension: {ext}. Expected .csv or .json")

    schema = INFLUENCER_SCHEMA if enforce_schema else None

    if file_format == "csv":
        reader = spark.read.option("header", "true")
        if schema:
            df = reader.schema(schema).csv(file_path)
        else:
            df = reader.option("inferSchema", "true").csv(file_path)
    elif file_format == "json":
        reader = spark.read.option("multiline", "true")
        if schema:
            df = reader.schema(schema).json(file_path)
        else:
            df = reader.json(file_path)
    else:
        raise ValueError(f"Unsupported format: {file_format}")

    return df


def load_niche_benchmarks(
    spark: SparkSession,
    file_path: str,
    file_format: str = "auto"
) -> DataFrame:
    """
    Loads industry reference benchmarks used for broadcast joins.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Benchmark file not found at: {file_path}")

    if file_format == "auto":
        file_format = "csv" if file_path.endswith(".csv") else "json"

    if file_format == "csv":
        return spark.read.option("header", "true").schema(BENCHMARK_SCHEMA).csv(file_path)
    return spark.read.schema(BENCHMARK_SCHEMA).json(file_path)
