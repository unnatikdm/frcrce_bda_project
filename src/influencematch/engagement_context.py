"""Compare source-provided engagement rates with a dated, licensed reference."""
import json
from pathlib import Path


REFERENCE_PATH = Path(__file__).resolve().parents[2] / "data" / "reference" / "cheerful_engagement_benchmarks.json"


def _reference() -> dict:
    return json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))


def reference_band(rate_percent: float, band: dict) -> str:
    if rate_percent < band["p25_percent"]:
        return "below_p25"
    if rate_percent < band["median_percent"]:
        return "p25_to_median"
    if rate_percent < band["p75_percent"]:
        return "median_to_p75"
    return "at_or_above_p75"


def engagement_context(profile: dict) -> dict:
    """Return a descriptive quartile band, never a recommendation score."""
    followers = profile.get("followers")
    rate = profile.get("engagement_rate")
    if followers is None or rate is None:
        return {"status": "unavailable", "reason": "Source engagement rate or follower count is missing."}
    try:
        followers, rate = int(followers), float(rate)
    except (TypeError, ValueError):
        return {"status": "unavailable", "reason": "Source engagement rate or follower count is not numeric."}
    if followers < 1000:
        return {"status": "unavailable", "reason": "The reference sample includes accounts with at least 1,000 followers."}
    if not 0 <= rate <= 1:
        return {"status": "unavailable", "reason": "Engagement rate must be supplied as a fraction from 0 to 1."}

    reference = _reference()
    band = next((row for row in reference["follower_bands"]
                 if followers >= row["min"] and (row["max_exclusive"] is None or followers < row["max_exclusive"])), None)
    if band is None:
        return {"status": "unavailable", "reason": "No reference follower band matches this profile."}

    percent = rate * 100
    label = reference_band(percent, band)
    return {
        "status": "compared",
        "engagement_rate_percent": round(percent, 4),
        "reference_band": label,
        "follower_band": {key: band[key] for key in ("min", "max_exclusive")},
        "reference_quartiles_percent": {key: band[key] for key in ("p25_percent", "median_percent", "p75_percent")},
        "reference_accounts_in_band": band["accounts"],
        "reference": {key: reference[key] for key in ("source_name", "source_url", "license_id", "measurement_window", "source_sample_size", "retrieved_at")},
        "use_note": "Descriptive comparison only; excluded from recommendation ranking and not a campaign outcome.",
    }
