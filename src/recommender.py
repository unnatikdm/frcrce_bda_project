"""
InfluenceIQ - Explainable Influencer Recommendation Engine
Implements multi-criteria decision scoring with configurable weights,
hard eligibility filtering, sub-score normalization, and transparent explainability.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
import pandas as pd
import numpy as np


DEFAULT_WEIGHTS = {
    "niche_relevance": 0.30,
    "engagement_quality": 0.25,
    "budget_fit": 0.20,
    "location_match": 0.15,
    "reach_fit": 0.10
}


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Ensures recommendation weights sum exactly to 1.0 (100%).
    Handles zero-sum edge cases safely.
    """
    total = sum(weights.values())
    if total <= 0:
        return {k: 1.0 / len(weights) for k in weights}
    return {k: v / total for k, v in weights.items()}


def calculate_sub_scores(
    row: pd.Series,
    target_niche: str,
    campaign_budget: float,
    preferred_location: str,
    min_followers: int,
    max_followers: int
) -> Dict[str, float]:
    """
    Calculates individual normalized dimension scores (0.0 to 1.0).
    """
    # 1. Niche Relevance Score
    primary = str(row.get("primary_niche", "")).strip().lower()
    secondary = str(row.get("secondary_niche", "")).strip().lower()
    target = target_niche.strip().lower()

    if target in ["all", "any"]:
        niche_score = 1.0
    elif primary == target:
        niche_score = 1.0
    elif target in secondary:
        niche_score = 0.75
    else:
        niche_score = 0.30

    # 2. Engagement Quality Score
    er = float(row.get("engagement_rate", 0.0))
    benchmark_er = float(row.get("benchmark_engagement_rate", 3.0))
    benchmark_er = max(benchmark_er, 0.5)

    # Ratio of ER to niche benchmark: 1.5x benchmark yields max score
    rel_er = er / benchmark_er
    eng_score = min(1.0, rel_er / 1.5)

    # Conversational depth bonus from comment-to-like ratio (deep engagement)
    comm_ratio = float(row.get("comment_to_like_ratio", 0.0))
    if comm_ratio >= 0.04:
        eng_score = min(1.0, eng_score + 0.10)
    elif comm_ratio >= 0.02:
        eng_score = min(1.0, eng_score + 0.05)

    # 3. Budget Fit Score
    cost = float(row.get("estimated_cost_per_post_inr", 0.0))
    if campaign_budget <= 0:
        budget_score = 0.0
    elif cost > campaign_budget:
        budget_score = max(0.0, 1.0 - ((cost - campaign_budget) / campaign_budget))
    else:
        # Sweet spot: spending 40% to 90% of budget gives maximum ROI & buffer
        ratio = cost / campaign_budget
        if 0.40 <= ratio <= 0.90:
            budget_score = 1.0
        elif ratio < 0.40:
            # Under-budget is fine, but may indicate lower reach than budget could buy
            budget_score = 0.70 + (ratio / 0.40) * 0.25
        else:
            # 90% to 100% of budget
            budget_score = 0.90

    # 4. Location Match Score
    city = str(row.get("location_city", "")).strip().lower()
    aud_city = str(row.get("audience_top_city", "")).strip().lower()
    pref_loc = preferred_location.strip().lower()

    if pref_loc in ["all", "any", "all india"]:
        loc_score = 0.85  # Neutral national reach
    else:
        score = 0.20  # Base score for same country
        if city == pref_loc:
            score += 0.50
        if aud_city == pref_loc:
            score += 0.30
        loc_score = min(1.0, score)

    # 5. Reach Fit Score
    followers = max(1, int(row.get("followers_count", 1)))
    min_f = max(1, min_followers)
    max_f = max(min_f + 1, max_followers)

    # Logarithmic scale normalization across follower spectrum
    log_f = math.log10(followers)
    log_min = math.log10(min_f)
    log_max = math.log10(max_f)

    if log_max > log_min:
        reach_score = max(0.0, min(1.0, (log_f - log_min) / (log_max - log_min)))
    else:
        reach_score = 0.5

    return {
        "niche_relevance": round(niche_score, 4),
        "engagement_quality": round(eng_score, 4),
        "budget_fit": round(budget_score, 4),
        "location_match": round(loc_score, 4),
        "reach_fit": round(reach_score, 4)
    }


def generate_recommendation_reasons(
    row: pd.Series,
    sub_scores: Dict[str, float],
    campaign_budget: float,
    preferred_location: str
) -> List[str]:
    """
    Generates human-readable, quantitative justifications for the recommendation.
    """
    reasons = []
    er = float(row.get("engagement_rate", 0.0))
    benchmark_er = float(row.get("benchmark_engagement_rate", 3.0))
    cost = float(row.get("estimated_cost_per_post_inr", 0.0))
    followers = int(row.get("followers_count", 0))
    niche = row.get("primary_niche", "General")
    city = row.get("location_city", "Unknown")

    # 1. Engagement justification
    rel = round(er / max(benchmark_er, 0.1), 1)
    if rel >= 1.2:
        reasons.append(f"⭐ **High Engagement**: {er}% ER is {rel}x the {niche} benchmark ({benchmark_er}%).")
    elif rel >= 0.9:
        reasons.append(f"📈 **Solid Engagement**: {er}% ER aligns with industry standards.")
    else:
        reasons.append(f"📊 **Consistent Activity**: Regular cadence with {er}% engagement.")

    # 2. Budget justification
    if campaign_budget > 0 and cost <= campaign_budget:
        savings = campaign_budget - cost
        pct_left = round((savings / campaign_budget) * 100)
        reasons.append(f"💰 **Budget Fit**: ₹{cost:,.0f} leaves ₹{savings:,.0f} ({pct_left}%) campaign reserve.")
    elif cost > campaign_budget:
        reasons.append(f"⚠️ **Slightly Above Budget**: ₹{cost:,.0f} requires ₹{cost - campaign_budget:,.0f} budget extension.")

    # 3. Location justification
    if preferred_location.lower() not in ["all", "any", "all india"]:
        if city.lower() == preferred_location.lower():
            reasons.append(f"📍 **Local Market Anchor**: Based directly in {city}.")
        elif str(row.get("audience_top_city", "")).lower() == preferred_location.lower():
            reasons.append(f"🎯 **Target Audience Focus**: Primary audience density is in {preferred_location}.")

    # 4. Quality & Conversational Depth
    comm_pct = round(float(row.get("comment_to_like_ratio", 0.0)) * 100, 1)
    if comm_pct >= 3.0:
        reasons.append(f"💬 **Active Discussion**: {comm_pct}% comment ratio reflects genuine comments over passive likes.")

    # 5. Tier / Scale justification
    tier = row.get("follower_tier", "")
    reasons.append(f"👥 **Audience Scale**: {followers:,} followers in the {tier} segment.")

    return reasons[:3]  # Return top 3 compelling reasons


def recommend_influencers(
    df: pd.DataFrame,
    target_niche: str = "All",
    campaign_budget: float = 100000.0,
    min_engagement_rate: float = 2.0,
    follower_range: Tuple[int, int] = (5000, 500000),
    preferred_location: str = "All",
    custom_weights: Optional[Dict[str, float]] = None,
    top_n: int = 15
) -> Tuple[pd.DataFrame, bool, str]:
    """
    Ranks influencers based on campaign criteria and weighted factor scores.
    Returns:
      (results_df, is_exact_match, explanation_message)
    """
    if df.empty:
        return pd.DataFrame(), False, "Influencer database is empty."

    weights = normalize_weights(custom_weights or DEFAULT_WEIGHTS)
    min_f, max_f = follower_range

    # Validation guards
    if campaign_budget <= 0:
        campaign_budget = 50000.0

    # Step 1: Campaign Eligibility Hard Filtering
    filtered = df.copy()

    # Niche filter
    if target_niche.lower() not in ["all", "any"]:
        filtered = filtered[filtered["primary_niche"].str.lower() == target_niche.lower()]

    # Followers range
    filtered = filtered[
        (filtered["followers_count"] >= min_f) &
        (filtered["followers_count"] <= max_f)
    ]

    # Min engagement rate
    filtered = filtered[filtered["engagement_rate"] >= min_engagement_rate]

    # Budget filter
    filtered = filtered[filtered["estimated_cost_per_post_inr"] <= campaign_budget]

    # Location filter (if strict location chosen)
    if preferred_location.lower() not in ["all", "any", "all india"]:
        loc_match = (
            (filtered["location_city"].str.lower() == preferred_location.lower()) |
            (filtered["audience_top_city"].str.lower() == preferred_location.lower())
        )
        # Apply location filter only if we still have candidates, else treat as preference
        if filtered[loc_match].shape[0] >= 3:
            filtered = filtered[loc_match]

    is_exact_match = True
    msg = f"Found {len(filtered)} eligible influencers matching all campaign constraints."

    # Step 2: Handle Zero Matches Gracefully (Relax constraints for actionable feedback)
    if filtered.empty:
        is_exact_match = False
        msg = (
            "No influencers met 100% of your constraints. "
            "Showing top near-miss recommendations with relaxed budget (+30%) and engagement thresholds."
        )
        # Relaxed filtering fallback
        relaxed = df.copy()
        if target_niche.lower() not in ["all", "any"]:
            relaxed = relaxed[relaxed["primary_niche"].str.lower() == target_niche.lower()]
        relaxed = relaxed[
            (relaxed["followers_count"] >= int(min_f * 0.7)) &
            (relaxed["followers_count"] <= int(max_f * 1.4)) &
            (relaxed["estimated_cost_per_post_inr"] <= campaign_budget * 1.35) &
            (relaxed["engagement_rate"] >= max(0.5, min_engagement_rate - 1.0))
        ]
        filtered = relaxed if not relaxed.empty else df.head(top_n).copy()

    # Step 3: Compute Sub-scores and Weighted Total Score
    results = []
    for _, row in filtered.iterrows():
        sub_scores = calculate_sub_scores(
            row, target_niche, campaign_budget, preferred_location, min_f, max_f
        )
        total_score = (
            weights["niche_relevance"] * sub_scores["niche_relevance"] +
            weights["engagement_quality"] * sub_scores["engagement_quality"] +
            weights["budget_fit"] * sub_scores["budget_fit"] +
            weights["location_match"] * sub_scores["location_match"] +
            weights["reach_fit"] * sub_scores["reach_fit"]
        ) * 100.0

        reasons = generate_recommendation_reasons(row, sub_scores, campaign_budget, preferred_location)

        record = dict(row)
        record["recommendation_score"] = round(total_score, 1)
        record["score_niche"] = round(sub_scores["niche_relevance"] * 100, 1)
        record["score_engagement"] = round(sub_scores["engagement_quality"] * 100, 1)
        record["score_budget"] = round(sub_scores["budget_fit"] * 100, 1)
        record["score_location"] = round(sub_scores["location_match"] * 100, 1)
        record["score_reach"] = round(sub_scores["reach_fit"] * 100, 1)
        record["recommendation_reasons"] = reasons
        results.append(record)

    ranked_df = pd.DataFrame(results)
    if not ranked_df.empty:
        ranked_df = ranked_df.sort_values(by="recommendation_score", ascending=False).reset_index(drop=True)
        ranked_df["rank"] = range(1, len(ranked_df) + 1)

    return ranked_df.head(top_n), is_exact_match, msg
