"""Portable JSON export for actual InfluenceMatch recommendations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from influencematch.engagement_context import engagement_context


DATASET_EXPORT_FIELDS = (
    "dataset_name", "dataset_key", "source_url", "license_id", "attribution",
    "source_collection_date", "retrieved_at_utc", "imported_file_sha256",
    "reels_file_sha256", "database_snapshot_sha256",
)


def build_recommendation_export(
    manifest: dict[str, Any],
    data_status: str,
    query: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build an auditable export without inventing or modifying recommendation scores."""
    return {
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).isoformat(),
        "query": query,
        "dataset": {key: manifest.get(key) for key in DATASET_EXPORT_FIELDS},
        "data_status": data_status,
        "limitations": manifest.get("limitations", []),
        "result_count": len(results),
        "results": [
            {**result, "engagement_reference": engagement_context(result)}
            for result in results
        ],
    }
