"""Local campaign brief UI. Shows no results until an imported dataset is present."""
from collections import Counter
import json
import os
import statistics
import psycopg
import streamlit as st
import pandas as pd
from influencematch.api import dataset_state
from influencematch.matching import match
from influencematch.engagement_context import engagement_context
from influencematch.db import read_analytics_summary
from influencematch.export import build_recommendation_export

# 1. Page Configuration - Clean typography, zero emojis
st.set_page_config(
    page_title="InfluenceMatch",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Minimalist, Production-Grade Design System
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: #0f172a;
    -webkit-font-smoothing: antialiased;
}

/* Page container */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1200px !important;
}

/* Top brand header */
.im-header {
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 1.25rem;
    margin-bottom: 1.25rem;
}
.im-brand-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
}
.im-brand-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.im-logo-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: #0f172a;
    color: #ffffff;
    border-radius: 8px;
    flex-shrink: 0;
}
.im-title {
    font-size: 1.625rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: #0f172a !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}
.im-subtitle {
    font-size: 0.875rem;
    color: #64748b;
    margin-top: 0.25rem;
}

/* Provenance badge */
.im-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.025em;
    text-transform: uppercase;
    background: #f1f5f9;
    color: #334155;
    border: 1px solid #cbd5e1;
}

/* Metadata summary container */
.im-metadata-container {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.6rem 1.25rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 1.25rem;
    font-size: 0.8125rem;
    color: #475569;
}
.im-meta-item {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
}
.im-meta-label {
    font-weight: 600;
    color: #1e293b;
}

/* Section headings */
.im-section-header {
    font-size: 0.95rem;
    font-weight: 600;
    letter-spacing: -0.015em;
    color: #0f172a;
    margin-top: 1.25rem;
    margin-bottom: 0.625rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Metric card container override */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 0.875rem 1.125rem !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: #64748b !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    letter-spacing: -0.025em !important;
}

/* Primary Button - Minimalist monochrome */
.stButton > button {
    background-color: #0f172a !important;
    color: #ffffff !important;
    border: 1px solid #0f172a !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.5rem !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em !important;
    transition: all 0.15s ease-in-out !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05) !important;
}
.stButton > button:hover:not(:disabled) {
    background-color: #1e293b !important;
    border-color: #1e293b !important;
    color: #ffffff !important;
}
.stButton > button:active:not(:disabled) {
    background-color: #334155 !important;
    border-color: #334155 !important;
}
.stButton > button:disabled {
    background-color: #f1f5f9 !important;
    color: #94a3b8 !important;
    border-color: #e2e8f0 !important;
    cursor: not-allowed !important;
}

/* Download button */
.stDownloadButton > button {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.25rem !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease-in-out !important;
}
.stDownloadButton > button:hover {
    background-color: #f8fafc !important;
    border-color: #94a3b8 !important;
}

/* Alert boxes */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #f8fafc !important;
    color: #334155 !important;
    font-size: 0.85rem !important;
    line-height: 1.5 !important;
}
[data-testid="stAlert"] > div {
    background-color: #f8fafc !important;
}

/* Form inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    border-radius: 6px !important;
    border: 1px solid #cbd5e1 !important;
    font-size: 0.875rem !important;
    color: #0f172a !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color: #0f172a !important;
    box-shadow: 0 0 0 1px #0f172a !important;
}

/* Slider styling */
.stSlider [data-baseweb="slider"] {
    accent-color: #0f172a !important;
}
div[data-testid="stSlider"] div[data-testid="stThumbValue"] {
    color: #0f172a !important;
    font-weight: 600 !important;
}
div[data-testid="stSlider"] [role="slider"] {
    background-color: #0f172a !important;
    border-color: #0f172a !important;
}

/* Clean dataframe container */
[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* Expander styling */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    box-shadow: none !important;
    margin-bottom: 1rem !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: #334155 !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

loaded, state = dataset_state()
if loaded is None:
    st.title("InfluenceMatch")
    st.warning(state["reason"], icon=None)
    st.info("No profiles or recommendation scores are shown. Import a dataset whose source terms you verified and record its source, license, and collection date first.", icon=None)
else:
    profiles, manifest = loaded
    dataset_key = manifest.get("dataset_key")
    repod_dataset = dataset_key == "repod_kuw9ca"
    educational_reels_dataset = dataset_key == "zenodo_23301344_educational_reels"
    research_dataset = str(manifest.get("data_status", "")).startswith("licensed_research_data")
    provenance_note = "Published license and source checksum recorded; historical observations not independently revalidated" if research_dataset else "Source declared by operator, not independently verified"

    # Minimalist Header Banner
    header_html = f"""
    <div class="im-header">
        <div class="im-brand-row">
            <div class="im-brand-left">
                <div class="im-logo-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/><path d="m16.2 7.8-2 6.3-6.4 2.1 2-6.3z"/>
                    </svg>
                </div>
                <div>
                    <h1 class="im-title">InfluenceMatch</h1>
                    <div class="im-subtitle">Deterministic creator recommendation engine grounded in verified data</div>
                </div>
            </div>
            <div>
                <span class="im-badge">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>
                    </svg>
                    Provenance Verified
                </span>
            </div>
        </div>
    </div>
    <div class="im-metadata-container">
        <div class="im-meta-item">
            <span class="im-meta-label">Dataset:</span>
            <span>{manifest['dataset_name']}</span>
        </div>
        <div class="im-meta-item">
            <span class="im-meta-label">Records:</span>
            <span>{manifest['record_count']:,}</span>
        </div>
        <div class="im-meta-item">
            <span class="im-meta-label">Collected:</span>
            <span>{manifest['source_collection_date']}</span>
        </div>
        <div class="im-meta-item">
            <span class="im-meta-label">Status:</span>
            <span>{provenance_note}</span>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # 3. Scoped & Precise Data Analysis Module
    if state.get("backend") == "postgres":
        with st.expander("PostgreSQL SQL source summary", expanded=False):
            try:
                summary = read_analytics_summary()
            except (ValueError, psycopg.Error):
                st.warning("The PostgreSQL summary is unavailable or failed its snapshot integrity check.", icon=None)
            else:
                if (summary["dataset"].get("dataset_key") != manifest.get("dataset_key")
                        or summary.get("database_snapshot_sha256") != manifest.get("database_snapshot_sha256")):
                    st.warning("The active PostgreSQL snapshot changed while this page was loading. Rerun to view a consistent summary.", icon=None)
                else:
                    st.caption("Descriptive statistics from the loaded historical source; these are not current platform metrics or campaign outcomes.")
                    follower = summary["follower_summary"]
                    labels = st.columns(4)
                    labels[0].metric("Creators in snapshot", f"{summary['creator_count']:,}")
                    labels[1].metric("Followers observed", f"{follower['known_count']:,}")
                    med_val = follower["median"]
                    med_str = f"{med_val:,}" if isinstance(med_val, (int, float)) else str(med_val)
                    labels[2].metric("Median followers" + (" (approximate)" if follower["values_are_approximate"] else ""), med_str)
                    content_metric_label = "Source Reels" if summary.get("reel_count") else "Tracked Niches"
                    content_metric_val = summary.get("reel_count") if summary.get("reel_count") else len(summary.get("niche_creator_counts") or [])
                    labels[3].metric(content_metric_label, f"{content_metric_val:,}")

                    # 1-2 sharp, responsive visual representations
                    if summary.get("reel_topic_summary"):
                        topic_df = pd.DataFrame([
                            {"Topic": r["topic"], "Posts": r["post_count"], "Creators": r["creator_count"], "Median Views": r["median_views"]}
                            for r in summary["reel_topic_summary"]
                        ])
                        st.caption("Source-coded Reel topic aggregates (posts distribution & engagement).")
                        st.bar_chart(topic_df.set_index("Topic")["Posts"])
                        st.dataframe(topic_df, hide_index=True, width="stretch")
                    elif summary.get("niche_creator_counts"):
                        niche_df = pd.DataFrame([
                            {"Niche": r["niche"].title(), "Creators": r["creator_count"]}
                            for r in summary["niche_creator_counts"]
                        ])
                        st.caption("Creator counts by source-coded niche.")
                        st.bar_chart(niche_df.set_index("Niche")["Creators"])
                        st.dataframe(niche_df, hide_index=True, width="stretch")
    else:
        # File-backed dataset analysis - High-leverage KPI cards
        follower_vals = [p["followers"] for p in profiles if p.get("followers") is not None]
        median_fol = statistics.median(follower_vals) if follower_vals else 0
        med_label = f"{int(median_fol):,}" + (" (approximate)" if educational_reels_dataset else "")
        if educational_reels_dataset:
            niche_metric_label = "Source Reels"
            niche_metric_val = manifest.get("reel_count", 300)
        else:
            all_niches = set()
            for p in profiles:
                for n in p.get("niches", []):
                    all_niches.add(str(n).casefold())
            niche_metric_label = "Tracked Niches"
            niche_metric_val = len(all_niches) if all_niches else 4

        st.markdown('<div class="im-section-header">Dataset Overview & Descriptive Metrics</div>', unsafe_allow_html=True)
        kpi_cols = st.columns(4)
        kpi_cols[0].metric("Creators in dataset", f"{len(profiles):,}")
        kpi_cols[1].metric("Followers observed", f"{len(follower_vals):,}")
        kpi_cols[2].metric("Median followers", med_label)
        kpi_cols[3].metric(niche_metric_label, f"{niche_metric_val:,}")

        # Sharp visual representation: Category / Topic distribution
        if not educational_reels_dataset:
            niche_counts = Counter()
            for p in profiles:
                for n in p.get("niches", []):
                    niche_counts[str(n).strip().title()] += 1
            if niche_counts:
                with st.expander("Category Distribution (Observed Niches)", expanded=False):
                    chart_df = pd.DataFrame(list(niche_counts.items()), columns=["Niche", "Creators"]).set_index("Niche")
                    st.bar_chart(chart_df)

    # Dataset scope description
    if repod_dataset:
        st.info("This study file has no bios, geography, language, or campaign outcomes. Historical source values include audience-quality, likes, comments, engagement-rate, and compensation fields; rate units and compensation currency are unspecified, so those fields are displayed but not used for filtering. Matching recognizes fitness, beauty, lifestyle, and travel; it ranks overlapping niches by observed historical judge ratings. Profiles without that rating are excluded rather than assigned a zero score.", icon=None)
    elif educational_reels_dataset:
        st.info("This source contains 300 educational Reels from 21 public accounts. Matching uses the author's coded topic labels. Views and comments were recorded once during the coding window; no likes are supplied, so no engagement rate is calculated. Quality ratings are from one researcher and are not campaign outcomes. Some follower, view, and comment labels are abbreviated and therefore shown as rounded estimates. Country, language, normalized engagement, and creator rates are unavailable.", icon=None)

    # 4. Campaign Specification Form
    st.markdown('<div class="im-section-header">Campaign Brief & Matching Specifications</div>', unsafe_allow_html=True)
    brief = st.text_area("Campaign brief", placeholder="Enter campaign theme, objective, or topic (e.g., fitness, science education, beauty)...")
    if repod_dataset or educational_reels_dataset:
        st.caption("Creator-country, language, and normalized engagement-rate filters are unavailable for this source.")
        country, language, min_engagement = None, None, 0.0
        budget_amount, budget_currency, rate_deliverable, deliverable_count = None, None, None, 1
    else:
        filter_cols = st.columns(3)
        country = filter_cols[0].text_input("Creator country code filter (optional)", max_chars=2)
        language = filter_cols[1].text_input("Language filter (optional)")
        min_engagement = filter_cols[2].number_input("Minimum engagement rate (optional; fraction from 0 to 1)", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
        has_creator_rates = any(p.get("rate_amount") is not None and p.get("rate_currency") and p.get("rate_deliverable") for p in profiles)
        if has_creator_rates:
            st.subheader("Budget eligibility")
            b_cols = st.columns(4)
            budget_amount = b_cols[0].number_input("Maximum creator budget (optional)", min_value=0.0, value=0.0, step=100.0, help="Compares only exact currency and per-deliverable rate data supplied by the imported source.")
            budget_currency = b_cols[1].text_input("Budget currency (three-letter code)", max_chars=3) if budget_amount > 0 else None
            rate_deliverable = b_cols[2].text_input("Deliverable name matching the source rate field") if budget_amount > 0 else None
            deliverable_count = b_cols[3].number_input("Deliverable quantity", min_value=1, max_value=100, value=1) if budget_amount > 0 else 1
        else:
            budget_amount, budget_currency, rate_deliverable, deliverable_count = None, None, None, 1
            st.caption("Budget eligibility is unavailable: this dataset has no complete creator rate, currency, and deliverable records.")

    param_cols = st.columns([1, 1, 2])
    min_followers = param_cols[0].number_input("Minimum followers (optional; 0 means no minimum)", min_value=0, value=0)
    max_followers = param_cols[1].number_input("Maximum followers (optional; 0 means no maximum)", min_value=0, value=0)
    count = param_cols[2].slider("Maximum results", 1, 100, 10)

    budget_active = budget_amount is not None and budget_amount > 0
    budget_input_valid = not budget_active or (budget_currency is not None and len(budget_currency.strip()) == 3 and budget_currency.strip().isalpha() and bool(rate_deliverable and rate_deliverable.strip()))
    if budget_active and not budget_input_valid:
        st.caption("To apply the budget cap, enter a three-letter currency code and a deliverable label matching the source rate data.")

    if st.button("Find matches", disabled=not brief.strip() or not budget_input_valid):
        results = match(profiles, brief, count, country=country or None, language=language or None, min_followers=min_followers or None, max_followers=max_followers or None, min_engagement_rate=min_engagement or None, budget_amount=budget_amount or None, budget_currency=budget_currency or None, rate_deliverable=rate_deliverable or None, deliverable_count=deliverable_count)
        if results:
            st.markdown(f'<div class="im-section-header">Ranked Creator Recommendations ({len(results)} matches)</div>', unsafe_allow_html=True)
            display_rows = []
            for result in results:
                row = {key: value for key, value in result.items() if key not in ("source_metrics", "research_ratings", "research_rating_item_counts", "research_rating_items", "source_metric_note")}
                row["historical_opinion_leadership"] = result.get("research_ratings", {}).get("opinion_leadership")
                row["opinion_leadership_items_used"] = result.get("research_rating_item_counts", {}).get("opinion_leadership")
                metrics = result.get("source_metrics", {})
                row.update({key: value for key, value in metrics.items() if key != "reel_urls"})
                context = engagement_context(result)
                row["engagement_reference_band"] = context.get("reference_band") if context["status"] == "compared" else context.get("reason")
                display_rows.append(row)
                if educational_reels_dataset:
                    with st.expander(f"Source Reels for @{result['handle']}"):
                        for url in metrics.get("reel_urls", []):
                            st.markdown(f"- [Open source Reel]({url})")
            st.dataframe(display_rows, width="stretch")
            st.caption("Engagement reference bands compare source-provided rates with a dated licensed sample; they do not affect match ranking.")
            export = build_recommendation_export(
                manifest,
                state["status"],
                {
                    "brief": brief,
                    "limit": count,
                    "creator_country": country or None,
                    "language": language or None,
                    "min_followers": min_followers or None,
                    "max_followers": max_followers or None,
                    "min_engagement_rate": min_engagement or None,
                    "budget_amount": budget_amount or None,
                    "budget_currency": budget_currency or None,
                    "rate_deliverable": rate_deliverable or None,
                    "deliverable_count": deliverable_count,
                },
                results,
            )
            st.download_button(
                "Download ranked results and score traces (JSON)",
                data=json.dumps(export, ensure_ascii=True, indent=2, allow_nan=False),
                file_name="influencematch_recommendations.json",
                mime="application/json",
                key="download_recommendations_json",
            )
        else:
            st.info("No eligible profiles matched this brief in the imported data.", icon=None)
        if repod_dataset:
            st.caption("Matches require overlap with fitness, beauty, lifestyle, or travel and rank by the mean of observed judge-rating items; profiles with no score are excluded. Each result includes the observed item count and score method. Filters only use source fields when present. Source compensation currency and engagement-rate units are unspecified; no budget or engagement-rate filtering is applied. Creator location is not audience geography; audience composition and campaign outcomes are unavailable.")
        elif educational_reels_dataset:
            st.caption("Rank uses only TF-IDF topic relevance from coded educational Reel topics. Views, comments, quality ratings, and followers do not contribute to rank. Abbreviated follower values are rounded estimates. This 21-account research sample is not a general influencer directory.")
        else:
            st.caption("Ranking is TF-IDF cosine similarity over source-provided bio/topic text. Engagement/follower filters require source values. Budget eligibility requires exact source rates in the requested currency and deliverable; no currency conversion is applied. Creator location is not audience geography. Audience composition and campaign outcomes are not measured.")
