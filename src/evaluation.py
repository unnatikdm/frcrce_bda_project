"""
InfluenceIQ - Big Data Evaluation & Benchmarking Module
Empirically evaluates:
  1. PySpark scalability and processing time across dataset scales (1k to 25k records).
  2. In-memory caching speedup factor.
  3. Recommendation ranking quality across realistic business campaign scenarios.
"""

import os
import time
import json
import pandas as pd
from typing import Dict, Any, List

from src.data_ingestion import get_spark_session, load_raw_influencers, load_niche_benchmarks
from src.data_cleaning import clean_influencer_data
from src.feature_engineering import engineer_influencer_features, demonstrate_lazy_and_caching
from src.recommender import recommend_influencers, DEFAULT_WEIGHTS
from scripts.generate_sample_data import generate_influencer_record, inject_controlled_anomalies


def benchmark_spark_scalability(spark, sizes: List[int] = [1000, 5000, 10000, 20000]) -> List[Dict[str, Any]]:
    """
    Measures PySpark processing throughput and execution time across increasing dataset sizes.
    Demonstrates Big Data scaling behavior on local Spark.
    """
    print("=" * 70)
    print("   InfluenceIQ - PySpark Scaling Benchmark")
    print("=" * 70)
    results = []

    benchmarks_path = "data/benchmarks/niche_benchmarks.csv"
    bench_df = load_niche_benchmarks(spark, benchmarks_path) if os.path.exists(benchmarks_path) else None

    for size in sizes:
        print(f"\n[+] Benchmarking pipeline with N = {size:,} records...")
        # 1. Synthesize batch
        t0 = time.perf_counter()
        raw_list = [generate_influencer_record(i) for i in range(1, size + 1)]
        anom_list = inject_controlled_anomalies(raw_list)
        gen_time = time.perf_counter() - t0

        # Convert to PySpark DataFrame
        t_ingest_start = time.perf_counter()
        raw_spark_df = spark.createDataFrame(pd.DataFrame(anom_list))
        ingest_time = time.perf_counter() - t_ingest_start

        # 2. PySpark Cleaning
        t_clean_start = time.perf_counter()
        clean_df, metrics = clean_influencer_data(raw_spark_df)
        clean_time = time.perf_counter() - t_clean_start

        # 3. PySpark Feature Engineering & Broadcast Join
        t_feat_start = time.perf_counter()
        feat_df = engineer_influencer_features(clean_df, bench_df)
        feat_time = time.perf_counter() - t_feat_start

        # 4. Trigger Execution via Action (Aggregation)
        t_action_start = time.perf_counter()
        agg_summary = feat_df.groupBy("primary_niche").agg({"engagement_rate": "avg", "influencer_id": "count"}).collect()
        action_time = time.perf_counter() - t_action_start

        total_etl_time = ingest_time + clean_time + feat_time + action_time
        throughput = round(size / max(total_etl_time, 0.001), 1)

        print(f"    - ETL Pipeline execution time: {total_etl_time:.3f} s")
        print(f"    - Throughput: {throughput:,} records/sec")

        results.append({
            "dataset_size": size,
            "ingest_seconds": round(ingest_time, 3),
            "cleaning_seconds": round(clean_time, 3),
            "features_seconds": round(feat_time, 3),
            "action_seconds": round(action_time, 3),
            "total_etl_seconds": round(total_etl_time, 3),
            "throughput_records_per_sec": throughput,
            "clean_records_count": metrics["clean_records_count"]
        })

    return results


def evaluate_recommendation_quality(processed_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates recommender accuracy, constraint satisfaction, and ranking separation
    across diverse enterprise campaign scenarios.
    """
    print("\n" + "=" * 70)
    print("   InfluenceIQ - Recommendation Quality Evaluation")
    print("=" * 70)

    test_scenarios = [
        {
            "name": "Tech Startup Seed Launch",
            "niche": "Tech & Gadgets",
            "budget": 45000.0,
            "min_er": 2.5,
            "follower_range": (5000, 75000),
            "location": "Bengaluru"
        },
        {
            "name": "Luxury Ethnic Fashion Campaign",
            "niche": "Fashion & Lifestyle",
            "budget": 120000.0,
            "min_er": 3.0,
            "follower_range": (30000, 350000),
            "location": "Mumbai"
        },
        {
            "name": "Fitness & Whey Protein Push",
            "niche": "Fitness & Health",
            "budget": 35000.0,
            "min_er": 3.5,
            "follower_range": (5000, 60000),
            "location": "Pune"
        },
        {
            "name": "Cloud Kitchen Brand Expansion",
            "niche": "Food & Culinary",
            "budget": 75000.0,
            "min_er": 3.2,
            "follower_range": (15000, 200000),
            "location": "Delhi"
        },
        {
            "name": "Gaming Streamer Sponsorship",
            "niche": "Gaming & Esports",
            "budget": 50000.0,
            "min_er": 3.8,
            "follower_range": (10000, 150000),
            "location": "Hyderabad"
        }
    ]

    scenario_evals = []

    for sc in test_scenarios:
        recs, is_exact, msg = recommend_influencers(
            df=processed_df,
            target_niche=sc["niche"],
            campaign_budget=sc["budget"],
            min_engagement_rate=sc["min_er"],
            follower_range=sc["follower_range"],
            preferred_location=sc["location"],
            top_n=5
        )

        if not recs.empty:
            avg_score = round(recs["recommendation_score"].mean(), 2)
            budget_util = round((recs["estimated_cost_per_post_inr"].mean() / sc["budget"]) * 100, 1)
            avg_er = round(recs["engagement_rate"].mean(), 2)
            within_budget_pct = round((recs["estimated_cost_per_post_inr"] <= sc["budget"]).mean() * 100, 1)
            target_niche_pct = round((recs["primary_niche"] == sc["niche"]).mean() * 100, 1)
        else:
            avg_score, budget_util, avg_er, within_budget_pct, target_niche_pct = 0, 0, 0, 0, 0

        print(f"[+] Scenario '{sc['name']}':")
        print(f"    - Matches found: {len(recs)} | Avg Score: {avg_score} | Avg ER: {avg_er}% | Budget Fit: {within_budget_pct}%")

        scenario_evals.append({
            "scenario_name": sc["name"],
            "target_niche": sc["niche"],
            "budget_inr": sc["budget"],
            "matches_returned": len(recs),
            "is_exact_match": is_exact,
            "average_recommendation_score": avg_score,
            "average_engagement_rate": avg_er,
            "budget_compliance_rate_pct": within_budget_pct,
            "niche_precision_pct": target_niche_pct,
            "average_budget_utilization_pct": budget_util
        })

    overall_precision = round(sum(s["niche_precision_pct"] for s in scenario_evals) / len(scenario_evals), 1)
    overall_budget_compliance = round(sum(s["budget_compliance_rate_pct"] for s in scenario_evals) / len(scenario_evals), 1)

    summary = {
        "overall_niche_precision_pct": overall_precision,
        "overall_budget_compliance_pct": overall_budget_compliance,
        "scenarios_evaluated": scenario_evals
    }

    return summary


def run_full_evaluation():
    """Runs end-to-end evaluation and stores metrics to disk."""
    spark = get_spark_session("InfluenceIQ-Evaluation")
    raw_path = "data/raw/influencers_raw.csv"
    bench_path = "data/benchmarks/niche_benchmarks.csv"

    if not os.path.exists(raw_path):
        print(f"[!] Raw file {raw_path} not found. Run scripts/generate_sample_data.py first.")
        return

    # 1. Scaling benchmark
    scaling_metrics = benchmark_spark_scalability(spark, sizes=[500, 1500, 3000])

    # 2. Caching demonstration
    print("\n[+] Demonstrating PySpark Lazy Evaluation & Memory Caching...")
    raw_df = load_raw_influencers(spark, raw_path)
    clean_df, _ = clean_influencer_data(raw_df)
    bench_df = load_niche_benchmarks(spark, bench_path)
    feat_df = engineer_influencer_features(clean_df, bench_df)
    cache_demo = demonstrate_lazy_and_caching(feat_df)
    print(f"    - Lazy definition: {cache_demo['lazy_definition_seconds']:.6f} s")
    print(f"    - Uncached execution: {cache_demo['uncached_action_seconds']:.4f} s")
    print(f"    - Cached execution: {cache_demo['cached_action_seconds']:.4f} s")
    print(f"    - Caching speedup factor: {cache_demo['cache_speedup_factor']}x")

    # 3. Recommendation Quality Evaluation
    pandas_df = feat_df.toPandas()
    recs_eval = evaluate_recommendation_quality(pandas_df)

    eval_output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "spark_scaling_benchmarks": scaling_metrics,
        "spark_caching_performance": cache_demo,
        "recommendation_quality": recs_eval
    }

    os.makedirs("data/processed", exist_ok=True)
    out_file = "data/processed/evaluation_report.json"
    with open(out_file, "w") as f:
        json.dump(eval_output, f, indent=2)

    print(f"\n[SUCCESS] Evaluation report saved to {out_file}")
    spark.stop()


if __name__ == "__main__":
    run_full_evaluation()
