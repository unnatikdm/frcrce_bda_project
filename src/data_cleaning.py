"""
InfluenceIQ - PySpark Data Cleaning Module
Performs scalable data cleaning, validation, deduplication, and anomaly resolution.
Tracks data quality metrics for governance and validation reporting.
"""

from typing import Dict, Any, Tuple
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.functions import col, when, trim, initcap, lower, lit


# Canonical Niche Mapping for category standardization
CANONICAL_NICHES = {
    "tech & gadgets": "Tech & Gadgets",
    "fashion & lifestyle": "Fashion & Lifestyle",
    "fitness & health": "Fitness & Health",
    "food & culinary": "Food & Culinary",
    "travel & adventure": "Travel & Adventure",
    "beauty & skincare": "Beauty & Skincare",
    "finance & business": "Finance & Business",
    "gaming & esports": "Gaming & Esports",
    "education & career": "Education & Career",
    "parenting & family": "Parenting & Family",
}


def clean_influencer_data(raw_df: DataFrame) -> Tuple[DataFrame, Dict[str, Any]]:
    """
    Cleans raw influencer records using PySpark transformations:
      1. Deduplicates based on influencer_id.
      2. Normalizes text fields (trimming, title-casing, canonical niche mapping).
      3. Imputes missing values in optional fields.
      4. Filters out invalid numbers (non-positive followers, negative metrics).
      5. Calculates and returns data quality metrics.
    """
    initial_count = raw_df.count()

    # 1. Deduplication by primary business key: influencer_id
    dedup_df = raw_df.dropDuplicates(["influencer_id"])
    count_after_dedup = dedup_df.count()
    duplicate_rows_dropped = initial_count - count_after_dedup

    # 2. Text Normalization and Category Standardization
    # Trim strings and lowercase primary_niche for canonical mapping
    normalized_df = dedup_df.withColumn(
        "raw_niche_clean", lower(trim(col("primary_niche")))
    )

    # Standardize niche names using canonical dictionary
    mapping_expr = when(col("raw_niche_clean") == "tech & gadgets", "Tech & Gadgets")
    for key, val in CANONICAL_NICHES.items():
        if key != "tech & gadgets":
            mapping_expr = mapping_expr.when(col("raw_niche_clean") == key, val)
    # Default fallback to initcap if not an exact match
    mapping_expr = mapping_expr.otherwise(initcap(col("primary_niche")))

    # Ensure optional columns exist with sensible defaults if schema is partial
    cols_present = set(normalized_df.columns)
    df_with_cols = normalized_df
    if "location_city" not in cols_present:
        df_with_cols = df_with_cols.withColumn("location_city", lit("Unknown"))
    if "audience_top_city" not in cols_present:
        df_with_cols = df_with_cols.withColumn("audience_top_city", lit("Unknown"))
    if "full_name" not in cols_present:
        df_with_cols = df_with_cols.withColumn("full_name", col("username"))
    if "secondary_niche" not in cols_present:
        df_with_cols = df_with_cols.withColumn("secondary_niche", lit("General"))
    if "avg_video_views" not in cols_present:
        df_with_cols = df_with_cols.withColumn("avg_video_views", lit(None).cast("long"))
    if "following_count" not in cols_present:
        df_with_cols = df_with_cols.withColumn("following_count", lit(0))
    if "posts_count" not in cols_present:
        df_with_cols = df_with_cols.withColumn("posts_count", lit(0))
    if "audience_gender_female_pct" not in cols_present:
        df_with_cols = df_with_cols.withColumn("audience_gender_female_pct", lit(0.50))
    if "is_verified" not in cols_present:
        df_with_cols = df_with_cols.withColumn("is_verified", lit(False))
    if "avg_post_frequency_per_week" not in cols_present:
        df_with_cols = df_with_cols.withColumn("avg_post_frequency_per_week", lit(2.5))

    cleaned_text_df = (
        df_with_cols
        .withColumn("primary_niche", mapping_expr)
        .drop("raw_niche_clean")
        .withColumn("location_city", initcap(trim(col("location_city"))))
        .withColumn("audience_top_city", initcap(trim(col("audience_top_city"))))
        .withColumn("username", lower(trim(col("username"))))
        .withColumn("full_name", trim(col("full_name")))
    )

    # 3. Handle Null Values and Imputation
    # Count null occurrences before imputation for quality report
    null_counts = (
        cleaned_text_df.select([
            F.count(when(col(c).isNull(), c)).alias(c)
            for c in ["secondary_niche", "avg_video_views", "location_city"]
        ]).collect()[0].asDict()
    )

    imputed_df = (
        cleaned_text_df
        .withColumn(
            "secondary_niche",
            when(col("secondary_niche").isNull(), lit("General")).otherwise(trim(col("secondary_niche")))
        )
        .withColumn(
            "location_city",
            when(col("location_city").isNull(), lit("Unknown")).otherwise(col("location_city"))
        )
        .withColumn(
            "avg_video_views",
            when(col("avg_video_views").isNull(), (col("followers_count") * 0.8).cast("long"))
            .otherwise(col("avg_video_views"))
        )
        .withColumn(
            "audience_gender_female_pct",
            when(col("audience_gender_female_pct").isNull(), lit(0.50))
            .otherwise(col("audience_gender_female_pct"))
        )
        .withColumn(
            "is_verified",
            when(col("is_verified").isNull(), lit(False)).otherwise(col("is_verified"))
        )
        .withColumn(
            "avg_post_frequency_per_week",
            when(col("avg_post_frequency_per_week").isNull(), lit(2.5))
            .otherwise(col("avg_post_frequency_per_week"))
        )
        .withColumn("followers_count", col("followers_count").cast("long"))
        .withColumn("following_count", col("following_count").cast("int"))
        .withColumn("posts_count", col("posts_count").cast("int"))
        .withColumn("avg_likes", col("avg_likes").cast("long"))
        .withColumn("avg_comments", col("avg_comments").cast("long"))
        .withColumn("avg_video_views", col("avg_video_views").cast("long"))
    )

    # 4. Filter Invalid Numeric Constraints
    # Business rules:
    # - Followers must be strictly positive (> 0)
    # - Likes and comments cannot be negative (>= 0)
    # - Estimated cost must be positive (> 0)
    valid_records_df = imputed_df.filter(
        (col("followers_count") > 0) &
        (col("avg_likes") >= 0) &
        (col("avg_comments") >= 0) &
        (col("estimated_cost_per_post_inr") > 0)
    )

    final_count = valid_records_df.count()
    invalid_rows_filtered = count_after_dedup - final_count

    quality_metrics = {
        "initial_raw_records": initial_count,
        "duplicate_rows_dropped": duplicate_rows_dropped,
        "invalid_numeric_rows_dropped": invalid_rows_filtered,
        "null_secondary_niches_imputed": null_counts.get("secondary_niche", 0),
        "null_video_views_imputed": null_counts.get("avg_video_views", 0),
        "null_cities_imputed": null_counts.get("location_city", 0),
        "clean_records_count": final_count,
        "clean_retention_pct": round((final_count / initial_count) * 100, 2) if initial_count > 0 else 0.0
    }

    return valid_records_df, quality_metrics
