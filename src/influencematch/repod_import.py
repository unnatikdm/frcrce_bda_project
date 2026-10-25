"""Fetch and normalize the CC BY RepOD influencer research dataset.

Only the ODS file is accepted because its published MD5 is verified here. The
repository's TSV artifact currently disagrees with its published checksum.
"""
import hashlib
import json
from collections import Counter
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from odf.opendocument import load
from odf.table import Table, TableCell, TableRow
from odf.text import P

URL = "https://repod.icm.edu.pl/api/access/datafile/98231"
SOURCE_PAGE = "https://repod.icm.edu.pl/dataset.xhtml?persistentId=doi%3A10.18150%2FKUW9CA"
EXPECTED_MD5 = "a51bf1ea9b2caf6094bb4977a5411047"
SOURCE_CACHE = Path("data/source/repod_kuw9ca/source.ods")
RATING_COMPONENTS = {
    "opinion_leadership": [
        "OpinionLeadership_modelforothers_a", "OpinionLeadership_stepahead_a",
        "OpinionLeadership_picturesnewideas_a", "OpinionLeadership_persuadespeople_a",
        "OpinionLeadership_inluencespeople_a", "OpinionLeadership_sourceofinformation_a",
    ],
    "authenticity": ["Authenticity_genuine_a", "Authenticity_seemsreal_a", "Authenticity_authentic_a"],
    "inspiration": ["Inspiration_inspires_a", "Inspiration_stimulatesthinking_a", "Inspiration_givesnewideas_a"],
    "content_expertise": ["ContentsExpertise_contentsexpertise_a", "ContentsExpertise_interestingissues_a", "ContentsExpertise_knowledge_a"],
    "intention_recommendation": ["IntentionRecommend_sendinginformationtopeople_a", "IntentionRecommend_likelyrecommend_a"],
}


def _value(cell):
    parts = []
    for paragraph in cell.getElementsByType(P):
        parts.extend(node.data for node in paragraph.childNodes if hasattr(node, "data"))
    return "".join(parts)


def _number(value, label, source_errors):
    value = str(value or "").strip()
    if not value:
        return None
    if value.startswith("#"):
        source_errors[label] += 1
        return None
    try:
        return float(value.replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"RepOD source metric {label} is not numeric; refusing conversion") from exc


def import_repod(destination: Path = Path("data/active")) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    raw_path = destination / "repod_source.ods"
    if SOURCE_CACHE.is_file():
        raw = SOURCE_CACHE.read_bytes()
    else:
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        raw = response.content
    digest = hashlib.md5(raw).hexdigest()
    if digest != EXPECTED_MD5:
        raise ValueError(f"RepOD ODS checksum mismatch: expected {EXPECTED_MD5}, got {digest}")
    raw_path.write_bytes(raw)

    doc = load(str(raw_path))
    sheets = doc.spreadsheet.getElementsByType(Table)
    if not sheets:
        raise ValueError("RepOD workbook has no data sheet")
    rows = sheets[0].getElementsByType(TableRow)
    headers = [_value(c) for c in rows[0].getElementsByType(TableCell)]
    indices = {name: i for i, name in enumerate(headers) if name}
    required = {"Name", "Number_followers", "Fitness", "Beauty", "Lifestyle", "Travel"}
    if not required.issubset(indices):
        raise ValueError("RepOD schema changed; expected creator and niche columns were not found")

    data_path = destination / "creators.jsonl"
    temporary_data_path = destination / "creators.jsonl.tmp"
    count = 0
    excluded_missing_identifier = 0
    source_errors = Counter()
    source_metric_counts = Counter()
    rating_profile_counts = Counter()
    try:
      with temporary_data_path.open("w", encoding="utf-8", newline="\n") as out:
        for cells_row in rows[1:]:
            values = [_value(c) for c in cells_row.getElementsByType(TableCell)]
            if not any(values):
                continue
            get = lambda name: values[indices[name]] if indices[name] < len(values) else ""
            handle = get("Name").strip().lstrip("@")
            if not handle:
                excluded_missing_identifier += 1
                continue
            niches = [name.casefold() for name in ("Fitness", "Beauty", "Lifestyle", "Travel") if get(name).strip() == "1"]
            followers_raw = get("Number_followers").strip()
            try:
                followers = int(float(followers_raw.replace(",", "."))) if followers_raw else None
            except ValueError as exc:
                raise ValueError("RepOD follower count is not numeric; refusing conversion") from exc
            ratings = {}
            rating_item_counts = {}
            rating_items = {}
            for construct, columns in RATING_COMPONENTS.items():
                items = [_number(get(source), source, source_errors) for source in columns]
                present_items = [number for number in items if number is not None]
                if present_items:
                    ratings[construct] = sum(present_items) / len(present_items)
                    rating_item_counts[construct] = len(present_items)
                    rating_items[construct] = {
                        column: number for column, number in zip(columns, items) if number is not None
                    }
                    rating_profile_counts[construct] += 1
            source_metric_fields = {
                "engagement_rate_source_value": "Aver_engage_rate",
                "average_comments_per_post": "Aver_number_comment_perpost",
                "average_likes_per_post": "Aver_number_likes_perpost",
                "audience_quality_score": "Aver_audience_qualityscore",
                "compensation_source_value": "Aver_median_income",
                "number_posts": "Number_posts",
            }
            source_metrics = {}
            for dest, source in source_metric_fields.items():
                number = _number(get(source), source, source_errors)
                if number is not None:
                    source_metrics[dest] = number
                    source_metric_counts[dest] += 1
            record = {
                "creator_id": handle, "handle": handle, "platform": "instagram",
                "bio": "", "primary_topic": " ".join(niches), "niches": niches,
                "followers": followers, "engagement_rate": None,
                "country": "", "language": "", "profile_url": "", "observed_at": "",
                "research_ratings": ratings,
                "research_rating_item_counts": rating_item_counts,
                "research_rating_items": rating_items,
                "source_metrics": source_metrics,
                "source_metric_note": "Source values are preserved as published; the dataset does not specify engagement-rate units or compensation currency, so those values are not used for eligibility or budget filtering.",
                "data_note": "Research observations, not current account metrics or campaign outcomes",
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
      if count == 0:
          raise ValueError("RepOD source contains no creator records")
      os.replace(temporary_data_path, data_path)
    except Exception:
        temporary_data_path.unlink(missing_ok=True)
        raise
    manifest = {
        "dataset_name": "Judge-rated dataset of nano- and micro-influencers",
        "dataset_key": "repod_kuw9ca",
        "source_url": SOURCE_PAGE, "license_id": "CC-BY-4.0",
        "source_collection_date": "Not disclosed; source describes a three-month observation period",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file_md5": digest, "source_file_sha256": hashlib.sha256(raw).hexdigest(),
        "imported_file": "creators.jsonl", "record_count": count,
        "source_observation_count": count + excluded_missing_identifier,
        "excluded_missing_creator_identifier": excluded_missing_identifier,
        "source_formula_error_cells": dict(source_errors),
        "source_metric_non_null_counts": dict(source_metric_counts),
        "research_rating_components": RATING_COMPONENTS,
        "research_rating_non_null_profile_counts": dict(rating_profile_counts),
        "rights_attestation": "Source file is explicitly CC BY 4.0; attribution required.",
        "data_status": "licensed_research_data; observations are historical and dates not disclosed",
        "attribution": "Korzyński, Paweł; Protsiuk, Olga (2026), RepOD, DOI 10.18150/KUW9CA",
        "limitations": ["No bios or post text", "Exact observation dates are not disclosed", "No current metrics or campaign outcomes", "Engagement-rate scale and compensation currency are unspecified; preserved values are not used for filtering", "TSV file checksum differs from repository metadata; verified ODS version used"],
    }
    manifest["imported_file_sha256"] = hashlib.sha256(data_path.read_bytes()).hexdigest()
    temporary_manifest_path = destination / "dataset_manifest.json.tmp"
    temporary_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary_manifest_path, destination / "dataset_manifest.json")
    return manifest


if __name__ == "__main__":
    print(json.dumps(import_repod(), indent=2, ensure_ascii=True))
