import json

from influencematch.engagement_context import REFERENCE_PATH, engagement_context, reference_band


def test_classifier_uses_published_benchmark_percentiles():
    reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    band = next(row for row in reference["follower_bands"] if row["min"] == 10_000)
    assert reference_band(band["p25_percent"], band) == "p25_to_median"
    assert reference_band(band["median_percent"], band) == "median_to_p75"
    assert reference_band(band["p75_percent"], band) == "at_or_above_p75"


def test_context_does_not_impute_missing_or_out_of_scope_metrics():
    assert engagement_context({})["status"] == "unavailable"

