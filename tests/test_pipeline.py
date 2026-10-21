"""
InfluenceIQ - Unit and Integration Tests
Tests data generation, PySpark cleaning, feature engineering, and recommendation ranking.
"""

import pytest
import pandas as pd
from scripts.generate_sample_data import generate_influencer_record, inject_controlled_anomalies
from src.recommender import (
    normalize_weights,
    calculate_sub_scores,
    recommend_influencers,
    DEFAULT_WEIGHTS
)
from src.data_ingestion import get_spark_session
from src.data_cleaning import clean_influencer_data
from src.feature_engineering import engineer_influencer_features


@pytest.fixture(scope="session")
def spark():
    """Provides a shared PySpark local session for tests."""
    session = get_spark_session("InfluenceIQ-Tests")
    yield session
    session.stop()


def test_synthetic_data_generation():
    """Verifies that synthetic data generation produces valid schemas."""
    record = generate_influencer_record(1)
    assert "influencer_id" in record
    assert "primary_niche" in record
    assert record["followers_count"] > 0
    assert record["estimated_cost_per_post_inr"] > 0
    assert record["avg_likes"] >= 0


def test_controlled_anomaly_injection():
    """Verifies that controlled anomalies are injected for ETL testing."""
    records = [generate_influencer_record(i) for i in range(1, 100)]
    anomalous = inject_controlled_anomalies(records)
    # Should contain more rows than original due to duplicate injection
    assert len(anomalous) >= len(records)


def test_recommender_weight_normalization():
    """Verifies weight normalization to exact 1.0 sum."""
    raw_weights = {"a": 30.0, "b": 20.0, "c": 50.0}
    norm = normalize_weights(raw_weights)
    assert pytest.approx(sum(norm.values()), 0.001) == 1.0

    # Test all-zeros fallback
    zero_weights = {"a": 0.0, "b": 0.0}
    norm_zero = normalize_weights(zero_weights)
    assert norm_zero["a"] == 0.5
    assert norm_zero["b"] == 0.5


def test_sub_score_ranges():
    """Ensures all dimension sub-scores stay between 0.0 and 1.0."""
    row = pd.Series({
        "primary_niche": "Beauty & Skincare",
        "secondary_niche": "Clean Beauty",
        "engagement_rate": 3.8,
        "benchmark_engagement_rate": 3.45,
        "comment_to_like_ratio": 0.04,
        "estimated_cost_per_post_inr": 18000,
        "location_city": "Mumbai",
        "audience_top_city": "Mumbai",
        "followers_count": 45000
    })

    sub_scores = calculate_sub_scores(
        row=row,
        target_niche="Beauty & Skincare",
        campaign_budget=20000.0,
        preferred_location="Mumbai",
        min_followers=10000,
        max_followers=100000
    )

    for k, score in sub_scores.items():
        assert 0.0 <= score <= 1.0, f"Score for {k} was out of range: {score}"


def test_recommendation_ranking_monotonicity():
    """Verifies that recommendation results are properly ordered descending by score."""
    sample_data = pd.DataFrame([
        {
            "influencer_id": "INF_1",
            "username": "@creator_1",
            "full_name": "Creator One",
            "primary_niche": "Beauty & Skincare",
            "secondary_niche": "Clean Beauty",
            "followers_count": 25000,
            "engagement_rate": 4.5,
            "benchmark_engagement_rate": 3.45,
            "comment_to_like_ratio": 0.05,
            "estimated_cost_per_post_inr": 12000.0,
            "location_city": "Mumbai",
            "audience_top_city": "Mumbai",
            "follower_tier": "Micro (10K-50K)"
        },
        {
            "influencer_id": "INF_2",
            "username": "@creator_2",
            "full_name": "Creator Two",
            "primary_niche": "Beauty & Skincare",
            "secondary_niche": "Dermatology",
            "followers_count": 30000,
            "engagement_rate": 2.2,
            "benchmark_engagement_rate": 3.45,
            "comment_to_like_ratio": 0.01,
            "estimated_cost_per_post_inr": 19000.0,
            "location_city": "Delhi",
            "audience_top_city": "Delhi",
            "follower_tier": "Micro (10K-50K)"
        }
    ])

    recs, is_exact, _ = recommend_influencers(
        df=sample_data,
        target_niche="Beauty & Skincare",
        campaign_budget=20000.0,
        min_engagement_rate=2.0,
        follower_range=(10000, 50000),
        preferred_location="Mumbai"
    )

    assert not recs.empty
    assert len(recs) == 2
    assert is_exact is True
    # First creator should have a higher score due to ER, location match and budget sweet spot
    assert recs.iloc[0]["recommendation_score"] >= recs.iloc[1]["recommendation_score"]
    assert recs.iloc[0]["influencer_id"] == "INF_1"


def test_zero_match_graceful_fallback():
    """Verifies that impossible filter combinations do not crash and activate graceful fallback."""
    sample_data = pd.DataFrame([
        {
            "influencer_id": "INF_10",
            "username": "@elite",
            "full_name": "Elite Star",
            "primary_niche": "Tech & Gadgets",
            "secondary_niche": "AI",
            "followers_count": 100000,
            "engagement_rate": 2.0,
            "benchmark_engagement_rate": 2.85,
            "comment_to_like_ratio": 0.02,
            "estimated_cost_per_post_inr": 50000.0,
            "location_city": "Bengaluru",
            "audience_top_city": "Bengaluru",
            "follower_tier": "Mid-Tier (50K-500K)"
        }
    ])

    recs, is_exact, msg = recommend_influencers(
        df=sample_data,
        target_niche="Tech & Gadgets",
        campaign_budget=1000.0,  # Unrealistic low budget
        min_engagement_rate=5.0,  # Unrealistic high ER
        follower_range=(1000, 200000),
        preferred_location="Bengaluru"
    )

    # Should fallback without throwing exceptions
    assert isinstance(recs, pd.DataFrame)
    assert is_exact is False


def test_spark_data_cleaning_pipeline(spark):
    """Verifies PySpark data cleaning operations including deduplication and text standardization."""
    raw_data = [
        ("INF_1", "User1", " tech & gadgets ", 10000, 500, 100, 15000.0),
        ("INF_1", "User1", "tech & gadgets", 10000, 500, 100, 15000.0),  # Duplicate
        ("INF_2", "User2", "FASHION & LIFESTYLE", 50000, 2000, 200, 35000.0),
        ("INF_3", "User3", "Fitness & Health", -100, 50, 5, 5000.0),     # Invalid negative followers
    ]
    cols = ["influencer_id", "username", "primary_niche", "followers_count", "avg_likes", "avg_comments", "estimated_cost_per_post_inr"]

    raw_df = spark.createDataFrame(raw_data, cols)
    cleaned_df, metrics = clean_influencer_data(raw_df)

    assert metrics["duplicate_rows_dropped"] == 1
    assert metrics["invalid_numeric_rows_dropped"] == 1
    assert cleaned_df.count() == 2

    # Verify canonical category mapping
    niches = [r["primary_niche"] for r in cleaned_df.collect()]
    assert "Tech & Gadgets" in niches
    assert "Fashion & Lifestyle" in niches


def test_instagram_graph_api_token_auth():
    """Verifies Instagram Graph API client authentication and sandbox token handling."""
    from src.instagram_api import InstagramGraphAPIClient
    client = InstagramGraphAPIClient()
    
    # 1. Test empty token
    valid, msg, info = client.set_token("")
    assert valid is False
    assert client.is_authenticated is False

    # 2. Test sandbox/demo token
    valid_sb, msg_sb, info_sb = client.set_token("demo_token")
    assert valid_sb is True
    assert client.is_authenticated is True
    assert "id" in info_sb
    assert info_sb["account_type"] == "BUSINESS"

    # 3. Test Business Discovery query with authenticated client
    ok, data = client.fetch_live_creator_metrics("@tarini_peshwaria")
    assert ok is True
    assert data["status"] == "LIVE_VERIFIED"


def test_authentic_dataset_integrity():
    """Verifies that the authentic dataset contains genuine creator handles and valid schemas."""
    import os
    parquet_path = "data/processed/influencers_parquet"
    if os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
        assert len(df) >= 1000
        # Verify genuine verified creators exist in the dataset
        handles = set(df["username"].str.lower().tolist())
        assert "@tarini_peshwaria" in handles or "@komalpandeyofficial" in handles or "@hudabeauty" in handles

