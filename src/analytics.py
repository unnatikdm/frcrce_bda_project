"""
InfluenceIQ - Spark SQL Analytics Module
Executes scalable SQL aggregations, window queries, and statistical rollups.
Provides data views for Streamlit and Plotly interactive dashboards.
"""

from typing import Dict, Any, Optional
import pandas as pd
from pyspark.sql import SparkSession, DataFrame


def register_temp_view(df: DataFrame, view_name: str = "influencers") -> None:
    """Registers or replaces a temporary SQL view in the Spark catalog."""
    df.createOrReplaceTempView(view_name)


def get_niche_performance(spark: SparkSession, df: Optional[DataFrame] = None) -> pd.DataFrame:
    """
    Spark SQL Aggregation: Analyzes engagement, creator volume, and pricing per niche.
    """
    if df is not None:
        register_temp_view(df)

    sql = """
        SELECT
            primary_niche,
            COUNT(*) AS total_creators,
            ROUND(AVG(engagement_rate), 2) AS avg_engagement_rate,
            ROUND(AVG(cost_per_engagement_inr), 2) AS avg_cpe_inr,
            ROUND(AVG(estimated_cost_per_post_inr), 0) AS avg_cost_per_post_inr,
            ROUND(AVG(followers_count), 0) AS avg_followers,
            ROUND(MAX(benchmark_engagement_rate), 2) AS benchmark_er
        FROM influencers
        GROUP BY primary_niche
        ORDER BY avg_engagement_rate DESC
    """
    return spark.sql(sql).toPandas()


def get_location_analytics(spark: SparkSession, df: Optional[DataFrame] = None) -> pd.DataFrame:
    """
    Spark SQL Query: Regional distribution, average pricing, and aggregate audience reach.
    """
    if df is not None:
        register_temp_view(df)

    sql = """
        SELECT
            location_city,
            COUNT(*) AS creator_count,
            ROUND(AVG(engagement_rate), 2) AS avg_engagement_rate,
            ROUND(AVG(estimated_cost_per_post_inr), 0) AS avg_cost_per_post_inr,
            ROUND(SUM(followers_count) / 1000000.0, 2) AS total_reach_millions
        FROM influencers
        GROUP BY location_city
        ORDER BY creator_count DESC
    """
    return spark.sql(sql).toPandas()


def get_follower_tier_analytics(spark: SparkSession, df: Optional[DataFrame] = None) -> pd.DataFrame:
    """
    Spark SQL Aggregation: Demonstrates engagement decay curve across follower tiers.
    """
    if df is not None:
        register_temp_view(df)

    sql = """
        SELECT
            follower_tier,
            COUNT(*) AS creator_count,
            ROUND(AVG(engagement_rate), 2) AS avg_engagement_rate,
            ROUND(AVG(cost_per_engagement_inr), 2) AS avg_cpe_inr,
            ROUND(AVG(estimated_cost_per_post_inr), 0) AS avg_cost_per_post_inr,
            ROUND(AVG(comment_to_like_ratio) * 100, 2) AS comment_depth_pct
        FROM influencers
        GROUP BY follower_tier
        ORDER BY avg_engagement_rate DESC
    """
    return spark.sql(sql).toPandas()


def get_budget_scatter_data(spark: SparkSession, df: Optional[DataFrame] = None, sample_fraction: float = 1.0) -> pd.DataFrame:
    """
    Extracts multi-dimensional influencer metrics for bubble and scatter plots:
    Followers (size), Cost (x), Engagement Rate (y), Niche (color).
    """
    if df is not None:
        register_temp_view(df)

    sql = """
        SELECT
            influencer_id,
            username,
            full_name,
            primary_niche,
            follower_tier,
            followers_count,
            engagement_rate,
            estimated_cost_per_post_inr,
            cost_per_engagement_inr,
            location_city,
            relative_engagement_index
        FROM influencers
    """
    res_df = spark.sql(sql)
    if sample_fraction < 1.0:
        res_df = res_df.sample(withReplacement=False, fraction=sample_fraction, seed=42)
    return res_df.toPandas()


def explain_spark_query(spark: SparkSession, query_sql: str) -> str:
    """
    Extracts the Spark Catalyst Optimizer physical and logical execution plan
    for educational inspection in the UI.
    """
    plan_df = spark.sql(query_sql)
    # PySpark 3.x+ explain returns None in console, but we can capture the plan via Java object
    try:
        return plan_df._jdf.queryExecution().explainString(
            spark._jsparkSession.sessionState().executePlan(plan_df._jdf.logicalPlan()).explainMode()
        )
    except Exception:
        # Fallback to simple plan representation
        return str(plan_df._jdf.queryExecution().simpleString())
