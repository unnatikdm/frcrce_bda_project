"""
InfluenceIQ - PySpark Feature Engineering & Parquet Persistence Module
Implements domain-specific metrics, broadcast joins, tier classifications,
partitioning, and demonstrates Spark lazy evaluation and caching.
"""

import time
from typing import Optional, Tuple, Dict, Any
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.functions import col, when, round as spark_round, lit, broadcast


def engineer_influencer_features(
    cleaned_df: DataFrame,
    benchmarks_df: Optional[DataFrame] = None
) -> DataFrame:
    """
    Computes key performance indicators (KPIs) and features using PySpark expressions:
      - Engagement Rate (%) = ((avg_likes + avg_comments) / followers_count) * 100
      - Comment-to-Like Ratio = avg_comments / (avg_likes + 1)
      - Follower Tier classification (Nano, Micro, Mid-Tier, Macro, Mega)
      - Cost per Engagement (CPE in INR) = estimated_cost / (likes + comments + 1)
      - Broadcast Join with niche industry benchmarks
      - Relative Engagement Index = engagement_rate / benchmark_engagement_rate
      - Activity Score (0-100) based on weekly posting cadence
    """
    # 1. Basic Engagement Metrics
    base_features_df = (
        cleaned_df
        .withColumn(
            "engagement_rate",
            spark_round(((col("avg_likes") + col("avg_comments")) / col("followers_count")) * 100.0, 3)
        )
        .withColumn(
            "comment_to_like_ratio",
            spark_round(col("avg_comments") / (col("avg_likes") + 1.0), 4)
        )
        .withColumn(
            "video_view_ratio",
            spark_round(col("avg_video_views") / col("followers_count"), 3)
        )
        # Classify Influencer Tier based on industry standard thresholds
        .withColumn(
            "follower_tier",
            when(col("followers_count") < 10000, lit("Nano (1K-10K)"))
            .when(col("followers_count") < 50000, lit("Micro (10K-50K)"))
            .when(col("followers_count") < 500000, lit("Mid-Tier (50K-500K)"))
            .when(col("followers_count") < 1000000, lit("Macro (500K-1M)"))
            .otherwise(lit("Mega (>1M)"))
        )
        .withColumn(
            "cost_per_engagement_inr",
            spark_round(
                col("estimated_cost_per_post_inr") / (col("avg_likes") + col("avg_comments") + 1.0),
                2
            )
        )
        .withColumn(
            "cost_per_mille_inr",
            spark_round((col("estimated_cost_per_post_inr") / col("followers_count")) * 1000.0, 2)
        )
        # Activity score (100 is optimal: ~5 to 7 posts/week)
        .withColumn(
            "activity_score",
            spark_round(
                when(col("avg_post_frequency_per_week") <= 7.0, (col("avg_post_frequency_per_week") / 7.0) * 100.0)
                .otherwise(lit(100.0) - (col("avg_post_frequency_per_week") - 7.0) * 8.0),
                1
            )
        )
    )

    # 2. Big Data Demonstration: Broadcast Join with Reference Benchmarks
    # Since benchmarks table is small (< 100 rows), broadcasting avoids expensive network shuffle
    if benchmarks_df is not None:
        enriched_df = (
            base_features_df.join(
                broadcast(benchmarks_df),
                on="primary_niche",
                how="left"
            )
            .withColumn(
                "benchmark_engagement_rate",
                when(col("benchmark_engagement_rate").isNull(), lit(3.0))
                .otherwise(col("benchmark_engagement_rate"))
            )
            .withColumn(
                "relative_engagement_index",
                spark_round(
                    col("engagement_rate") / col("benchmark_engagement_rate"),
                    2
                )
            )
        )
    else:
        enriched_df = (
            base_features_df
            .withColumn("benchmark_engagement_rate", lit(3.0))
            .withColumn(
                "relative_engagement_index",
                spark_round(col("engagement_rate") / 3.0, 2)
            )
            .withColumn("benchmark_cpm_inr", lit(250.0))
            .withColumn("niche_market_demand", lit("High"))
        )

    return enriched_df


def save_to_parquet(
    df: DataFrame,
    output_path: str,
    partition_by: str = "primary_niche",
    mode: str = "overwrite"
) -> None:
    """
    Persists transformed PySpark DataFrame to Apache Parquet columnar storage.
    Partitions data to enable partition pruning during queries.
    """
    (
        df.write
        .mode(mode)
        .partitionBy(partition_by)
        .parquet(output_path)
    )


def read_from_parquet(spark, input_path: str) -> DataFrame:
    """
    Reads partitioned Parquet files into a PySpark DataFrame.
    """
    return spark.read.parquet(input_path)


def demonstrate_lazy_and_caching(df: DataFrame) -> Dict[str, Any]:
    """
    Empirically demonstrates Apache Spark's Lazy Evaluation and Caching.
    Measures execution time without cache vs with in-memory caching.
    """
    # 1. Lazy evaluation: defining a transformation pipeline without execution
    t0 = time.perf_counter()
    filtered_trans = df.filter(col("engagement_rate") > 3.0).groupBy("follower_tier").count()
    lazy_definition_time = time.perf_counter() - t0

    # 2. First Action triggers physical execution of the Directed Acyclic Graph (DAG)
    t1 = time.perf_counter()
    _ = filtered_trans.collect()
    uncached_action_time = time.perf_counter() - t1

    # 3. Cache DataFrame in memory
    cached_df = df.cache()

    # Trigger action to materialize cache in Spark memory
    t2 = time.perf_counter()
    _ = cached_df.count()
    cache_materialization_time = time.perf_counter() - t2

    # Second action over cached dataset (avoids re-executing entire upstream lineage)
    t3 = time.perf_counter()
    _ = cached_df.filter(col("engagement_rate") > 3.0).groupBy("follower_tier").count().collect()
    cached_action_time = time.perf_counter() - t3

    # Clean up cache
    cached_df.unpersist()

    return {
        "lazy_definition_seconds": round(lazy_definition_time, 6),
        "uncached_action_seconds": round(uncached_action_time, 4),
        "cache_materialization_seconds": round(cache_materialization_time, 4),
        "cached_action_seconds": round(cached_action_time, 4),
        "cache_speedup_factor": round(uncached_action_time / max(cached_action_time, 0.0001), 2)
    }
