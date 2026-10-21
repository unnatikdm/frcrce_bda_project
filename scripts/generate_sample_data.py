"""
InfluenceIQ - Synthetic Data Generator
Generates reproducible, realistic Instagram influencer datasets and industry benchmarks.
Includes realistic data anomalies (nulls, duplicates, casing issues, invalid records)
to demonstrate Big Data ETL and cleaning capabilities in Apache Spark.
"""

import argparse
import json
import os
import random
import numpy as np
import pandas as pd

# Set reproducible seeds
DEFAULT_SEED = 42

NICHES = [
    "Tech & Gadgets",
    "Fashion & Lifestyle",
    "Fitness & Health",
    "Food & Culinary",
    "Travel & Adventure",
    "Beauty & Skincare",
    "Finance & Business",
    "Gaming & Esports",
    "Education & Career",
    "Parenting & Family",
]

SECONDARY_NICHES = {
    "Tech & Gadgets": ["AI & Coding", "Consumer Tech", "Mobile Reviews", "Smart Home", "Gaming"],
    "Fashion & Lifestyle": ["Sustainable Fashion", "Streetwear", "Luxury", "Traditional Wear", "Thrifting"],
    "Fitness & Health": ["Yoga & Mindfulness", "Bodybuilding", "CrossFit", "Nutrition & Diet", "Marathon"],
    "Food & Culinary": ["Street Food", "Baking", "Vegan Cuisine", "Regional Recipes", "Restaurant Reviews"],
    "Travel & Adventure": ["Solo Travel", "Backpacking", "Luxury Resorts", "Trekking", "Cultural Heritage"],
    "Beauty & Skincare": ["Clean Beauty", "Dermatology", "Bridal Makeup", "Haircare", "Men's Grooming"],
    "Finance & Business": ["Stock Markets", "Crypto & Web3", "Personal Budgeting", "Startups", "Real Estate"],
    "Gaming & Esports": ["PC Gaming", "Mobile Gaming", "Live Streaming", "Game Dev", "Retro Games"],
    "Education & Career": ["Upskilling", "Exam Prep", "Study Abroad", "Productivity", "Soft Skills"],
    "Parenting & Family": ["Newborn Care", "Montessori", "Kids Activities", "Family Travel", "Work-Life Balance"]
}

CITIES = [
    ("Mumbai", "Maharashtra", "Tier 1"),
    ("Delhi", "Delhi NCR", "Tier 1"),
    ("Bengaluru", "Karnataka", "Tier 1"),
    ("Hyderabad", "Telangana", "Tier 1"),
    ("Pune", "Maharashtra", "Tier 2"),
    ("Chennai", "Tamil Nadu", "Tier 1"),
    ("Kolkata", "West Bengal", "Tier 1"),
    ("Ahmedabad", "Gujarat", "Tier 2"),
    ("Jaipur", "Rajasthan", "Tier 2"),
    ("Chandigarh", "Punjab/Haryana", "Tier 2"),
    ("Kochi", "Kerala", "Tier 2"),
    ("Indore", "Madhya Pradesh", "Tier 2"),
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Ananya", "Arjun", "Deepak", "Diya", "Ishaan", "Kavya",
    "Manish", "Meera", "Neha", "Nikhil", "Pooja", "Pranav", "Priya", "Rahul",
    "Rhea", "Rohan", "Sakshi", "Siddharth", "Sneha", "Tanvi", "Varun", "Zoya",
    "Vikram", "Tara", "Kabir", "Shreya", "Kunal", "Alia", "Aditya", "Simran"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Mehta", "Reddy", "Nair", "Iyer", "Kulkarni",
    "Deshmukh", "Chopra", "Kapoor", "Bhatia", "Sen", "Chatterjee", "Gupta",
    "Jain", "Singh", "Rao", "Malhotra", "Joshi", "Bansal", "Saxena", "Menon"
]

AGE_GROUPS = ["18-24", "25-34", "35-44"]
AGE_WEIGHTS = [0.45, 0.40, 0.15]

BENCHMARKS = [
    {"primary_niche": "Tech & Gadgets", "benchmark_engagement_rate": 2.85, "benchmark_cpm_inr": 280.0, "niche_market_demand": "High"},
    {"primary_niche": "Fashion & Lifestyle", "benchmark_engagement_rate": 3.20, "benchmark_cpm_inr": 240.0, "niche_market_demand": "Very High"},
    {"primary_niche": "Fitness & Health", "benchmark_engagement_rate": 4.10, "benchmark_cpm_inr": 290.0, "niche_market_demand": "High"},
    {"primary_niche": "Food & Culinary", "benchmark_engagement_rate": 3.85, "benchmark_cpm_inr": 220.0, "niche_market_demand": "High"},
    {"primary_niche": "Travel & Adventure", "benchmark_engagement_rate": 3.60, "benchmark_cpm_inr": 260.0, "niche_market_demand": "Medium"},
    {"primary_niche": "Beauty & Skincare", "benchmark_engagement_rate": 3.45, "benchmark_cpm_inr": 270.0, "niche_market_demand": "Very High"},
    {"primary_niche": "Finance & Business", "benchmark_engagement_rate": 2.20, "benchmark_cpm_inr": 420.0, "niche_market_demand": "Very High"},
    {"primary_niche": "Gaming & Esports", "benchmark_engagement_rate": 4.50, "benchmark_cpm_inr": 190.0, "niche_market_demand": "High"},
    {"primary_niche": "Education & Career", "benchmark_engagement_rate": 2.50, "benchmark_cpm_inr": 310.0, "niche_market_demand": "Medium"},
    {"primary_niche": "Parenting & Family", "benchmark_engagement_rate": 3.35, "benchmark_cpm_inr": 250.0, "niche_market_demand": "Medium"}
]


def generate_influencer_record(idx: int) -> dict:
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    full_name = f"{first_name} {last_name}"
    
    niche = random.choice(NICHES)
    sec_niche = random.choice(SECONDARY_NICHES[niche])
    
    city_info = random.choice(CITIES)
    city_name = city_info[0]
    
    # Username generation
    handle_styles = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}_{niche.split()[0].lower()}",
        f"the_{first_name.lower()}_{last_name.lower()}",
        f"{first_name.lower()}explores",
        f"{first_name.lower()}_official"
    ]
    username = f"@{random.choice(handle_styles)}_{random.randint(10, 99)}"
    
    # Follower distribution: log-normal distribution for realistic social media skew
    # Nano: 2k-10k, Micro: 10k-50k, Mid: 50k-500k, Macro: 500k-1M, Mega: >1M
    log_followers = np.random.normal(loc=10.5, scale=1.3)
    followers = int(np.exp(log_followers))
    followers = max(2000, min(followers, 2500000))
    
    # Social stats
    following = int(random.triangular(120, 2200, 450))
    posts_count = int(random.triangular(40, 2800, 350))
    post_freq_per_week = round(random.uniform(1.2, 10.5), 1)
    
    # Higher follower count usually exhibits lower engagement rate (power law)
    # Target engagement rate: Nano (4-8%), Micro (3-6%), Mid (2-4%), Mega (1-3%)
    if followers < 10000:
        base_er = random.uniform(0.045, 0.085)
    elif followers < 50000:
        base_er = random.uniform(0.030, 0.065)
    elif followers < 500000:
        base_er = random.uniform(0.020, 0.045)
    elif followers < 1000000:
        base_er = random.uniform(0.015, 0.032)
    else:
        base_er = random.uniform(0.009, 0.024)
        
    avg_total_engagements = int(followers * base_er)
    # Comments are typically 2% to 7% of total engagements
    comment_ratio = random.uniform(0.02, 0.07)
    avg_comments = max(3, int(avg_total_engagements * comment_ratio))
    avg_likes = max(10, avg_total_engagements - avg_comments)
    
    # Video views typically 0.5x to 3.5x followers for active creators
    avg_video_views = int(followers * random.uniform(0.4, 2.8))
    
    # Audience demographics
    audience_age = random.choices(AGE_GROUPS, weights=AGE_WEIGHTS)[0]
    
    if niche in ["Beauty & Skincare", "Fashion & Lifestyle", "Parenting & Family"]:
        audience_female_pct = round(random.uniform(0.58, 0.88), 2)
    elif niche in ["Gaming & Esports", "Tech & Gadgets", "Finance & Business"]:
        audience_female_pct = round(random.uniform(0.18, 0.42), 2)
    else:
        audience_female_pct = round(random.uniform(0.40, 0.60), 2)
        
    is_verified = (followers > 200000 and random.random() < 0.65) or (followers > 50000 and random.random() < 0.15)
    
    # Estimated pricing (INR):
    # Rule of thumb in Indian market: ~₹150 to ₹450 per 1,000 followers, adjusted for niche CPM and ER quality
    benchmark_cpm = next((b["benchmark_cpm_inr"] for b in BENCHMARKS if b["primary_niche"] == niche), 250.0)
    base_cost = (followers / 1000.0) * benchmark_cpm * (base_er / 0.03)
    # Add creator premium/discount variation (+/- 25%)
    variance = random.uniform(0.75, 1.25)
    cost_inr = round(max(2500.0, base_cost * variance), -2)
    
    return {
        "influencer_id": f"INF_{10000 + idx}",
        "username": username,
        "full_name": full_name,
        "primary_niche": niche,
        "secondary_niche": sec_niche,
        "followers_count": followers,
        "following_count": following,
        "posts_count": posts_count,
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "avg_video_views": avg_video_views,
        "location_city": city_name,
        "location_country": "India",
        "audience_top_country": "India",
        "audience_top_city": city_name if random.random() < 0.65 else random.choice(CITIES)[0],
        "audience_age_group": audience_age,
        "audience_gender_female_pct": audience_female_pct,
        "is_verified": is_verified,
        "avg_post_frequency_per_week": post_freq_per_week,
        "estimated_cost_per_post_inr": cost_inr
    }


def inject_controlled_anomalies(records: list) -> list:
    """
    Injects a small controlled percentage of missing values, duplicate IDs,
    casing irregularities, and invalid numeric rows to test PySpark data cleaning.
    """
    n = len(records)
    modified = [dict(r) for r in records]
    
    # 1. Duplicate records (~2.5%)
    num_duplicates = int(n * 0.025)
    for _ in range(num_duplicates):
        src_idx = random.randint(0, n - 1)
        dup = dict(modified[src_idx])
        modified.append(dup)
        
    # 2. Missing values (~3% of rows get null in optional columns)
    num_missing = int(n * 0.03)
    for _ in range(num_missing):
        target = random.choice(modified)
        field_to_null = random.choice(["secondary_niche", "avg_video_views", "location_city"])
        target[field_to_null] = None
        
    # 3. Casing & whitespace inconsistencies in categories (~2%)
    num_casing = int(n * 0.02)
    for _ in range(num_casing):
        target = random.choice(modified)
        if target.get("primary_niche"):
            choice = random.choice(["lower", "upper", "spaces"])
            if choice == "lower":
                target["primary_niche"] = target["primary_niche"].lower()
            elif choice == "upper":
                target["primary_niche"] = target["primary_niche"].upper()
            else:
                target["primary_niche"] = f"   {target['primary_niche']}   "
        if target.get("location_city"):
            target["location_city"] = target["location_city"].lower()
            
    # 4. Invalid numeric records (~0.5%) that PySpark must clean
    num_invalid = max(3, int(n * 0.005))
    for _ in range(num_invalid):
        target = random.choice(modified)
        anomaly_type = random.choice(["negative_followers", "zero_followers", "negative_likes"])
        if anomaly_type == "negative_followers":
            target["followers_count"] = -random.randint(100, 5000)
        elif anomaly_type == "zero_followers":
            target["followers_count"] = 0
        elif anomaly_type == "negative_likes":
            target["avg_likes"] = -random.randint(10, 500)
            
    return modified


def generate_benchmark_dataset(output_dir: str):
    """Generates benchmark reference dataset for PySpark broadcast joins."""
    benchmarks_df = pd.DataFrame(BENCHMARKS)
    
    csv_path = os.path.join(output_dir, "niche_benchmarks.csv")
    json_path = os.path.join(output_dir, "niche_benchmarks.json")
    
    benchmarks_df.to_csv(csv_path, index=False)
    benchmarks_df.to_json(json_path, orient="records", indent=2)
    print(f"[OK] Generated benchmark dataset ({len(BENCHMARKS)} niches):")
    print(f"     CSV:  {csv_path}")
    print(f"     JSON: {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Instagram influencer data for InfluenceIQ.")
    parser.add_argument("--count", type=int, default=2500, help="Number of distinct influencer profiles (default: 2500)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--format", type=str, choices=["all", "csv", "json"], default="all", help="Output format")
    parser.add_argument("--output-raw-dir", type=str, default="data/raw", help="Output directory for raw data")
    parser.add_argument("--output-bench-dir", type=str, default="data/benchmarks", help="Output directory for benchmarks")
    
    args = parser.parse_args()
    
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    # Resolve paths relative to project root or current working dir
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_dir = os.path.join(base_dir, args.output_raw_dir)
    bench_dir = os.path.join(base_dir, args.output_bench_dir)
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(bench_dir, exist_ok=True)
    
    print(f"--- Generating {args.count} synthetic influencer records (seed={args.seed}) ---")
    raw_records = [generate_influencer_record(i) for i in range(1, args.count + 1)]
    
    print(f"[+] Injecting controlled anomalies (duplicates, nulls, invalid values, bad casing)...")
    anomalous_records = inject_controlled_anomalies(raw_records)
    print(f"[+] Total raw rows with anomalies: {len(anomalous_records)}")
    
    df_raw = pd.DataFrame(anomalous_records)
    
    # Save raw datasets
    csv_raw_path = os.path.join(raw_dir, "influencers_raw.csv")
    json_raw_path = os.path.join(raw_dir, "influencers_raw.json")
    
    if args.format in ["all", "csv"]:
        df_raw.to_csv(csv_raw_path, index=False)
        print(f"[OK] Saved raw CSV:  {csv_raw_path} ({os.path.getsize(csv_raw_path):,} bytes)")
        
    if args.format in ["all", "json"]:
        df_raw.to_json(json_raw_path, orient="records", indent=2)
        print(f"[OK] Saved raw JSON: {json_raw_path} ({os.path.getsize(json_raw_path):,} bytes)")
        
    # Generate reference benchmarks
    generate_benchmark_dataset(bench_dir)
    print("[SUCCESS] Data generation complete.")


if __name__ == "__main__":
    main()
