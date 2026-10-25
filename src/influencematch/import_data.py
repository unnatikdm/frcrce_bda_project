"""Import a user-provided, rights-cleared creator dataset with provenance.

This tool does not fetch, scrape, or certify source data. The operator must verify
source terms and attest to authorized use before importing any personal data.
"""
import argparse
import csv
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from .provenance import sha256_file

REQUIRED = {"creator_id", "handle", "platform"}

def _rows(path: Path):
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as stream:
            yield from csv.DictReader(stream)
    elif path.suffix.lower() in {".jsonl", ".ndjson"}:
        with path.open(encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if line.strip():
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"Invalid JSON on line {number}: {exc}") from exc
    else:
        raise ValueError("Input must be a CSV or JSONL file")

def import_creators(source: Path, destination: Path, *, source_name: str, source_url: str, license_id: str, source_date: str, rights_confirmed: bool) -> dict:
    if not rights_confirmed:
        raise ValueError("Import refused: verify the source terms and pass --rights-confirmed")
    if not all(value.strip() for value in (source_name, source_url, license_id)):
        raise ValueError("Source name, source URL, and license identifier are required")
    try:
        parsed_date = date.fromisoformat(source_date)
    except ValueError as exc:
        raise ValueError("source-date must be an ISO date (YYYY-MM-DD)") from exc
    if parsed_date > date.today():
        raise ValueError("source-date cannot be in the future")
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "creators.jsonl"
    if source.resolve() == output.resolve():
        raise ValueError("Source and output paths must be different")
    seen, count = set(), 0
    with output.open("w", encoding="utf-8", newline="\n") as out:
        for line_number, raw in enumerate(_rows(source), 1):
            if not isinstance(raw, dict):
                raise ValueError(f"Record {line_number} must be an object")
            missing = REQUIRED - raw.keys()
            if missing:
                raise ValueError(f"Record {line_number} is missing required fields: {', '.join(sorted(missing))}")
            row = {str(k): v for k, v in raw.items()}
            creator_id = str(row["creator_id"]).strip()
            handle = str(row["handle"]).strip().lstrip("@")
            platform = str(row["platform"]).strip().lower()
            if not creator_id or not handle:
                raise ValueError(f"Record {line_number} has an empty creator_id or handle")
            if creator_id in seen:
                raise ValueError(f"Duplicate creator_id at record {line_number}: {creator_id}")
            if platform != "instagram":
                raise ValueError(f"Record {line_number} platform must be instagram; got {platform!r}")
            seen.add(creator_id)
            row["creator_id"], row["handle"], row["platform"] = creator_id, handle, platform
            if row.get("followers") not in (None, ""):
                row["followers"] = int(row["followers"])
                if row["followers"] < 0: raise ValueError(f"Record {line_number} followers cannot be negative")
            else: row["followers"] = None
            if row.get("engagement_rate") not in (None, ""):
                row["engagement_rate"] = float(row["engagement_rate"])
                if not 0 <= row["engagement_rate"] <= 1: raise ValueError(f"Record {line_number} engagement_rate must be a fraction from 0 to 1")
            else: row["engagement_rate"] = None
            if row.get("rate_amount") not in (None, ""):
                row["rate_amount"] = float(row["rate_amount"])
                if not math.isfinite(row["rate_amount"]) or row["rate_amount"] < 0:
                    raise ValueError(f"Record {line_number} rate_amount must be finite and non-negative")
            else: row["rate_amount"] = None
            row["rate_currency"] = str(row.get("rate_currency") or "").strip().upper()
            row["rate_deliverable"] = str(row.get("rate_deliverable") or "").strip().casefold()
            quote_fields = (row["rate_amount"] is not None, bool(row["rate_currency"]), bool(row["rate_deliverable"]))
            if any(quote_fields) and not all(quote_fields):
                raise ValueError(f"Record {line_number} rate amount, currency, and deliverable must be supplied together")
            if row["rate_currency"] and (len(row["rate_currency"]) != 3 or not row["rate_currency"].isalpha()):
                raise ValueError(f"Record {line_number} rate_currency must be a three-letter currency code")
            for key in ("bio", "primary_topic", "country", "language", "profile_url", "observed_at"):
                if row.get(key) is None: row[key] = ""
                else: row[key] = str(row[key])
            out.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
            count += 1
    if not count:
        output.unlink(missing_ok=True)
        raise ValueError("Source contains no creator records")
    manifest = {
        "dataset_name": source_name, "source_url": source_url, "license_id": license_id,
        "source_collection_date": parsed_date.isoformat(),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file_sha256": sha256_file(source),
        "imported_file": "creators.jsonl", "imported_file_sha256": sha256_file(output),
        "record_count": count, "platform_filter": "instagram",
        "rights_attestation": "Operator confirmed the source terms permit this use; not independently verified by this software.",
        "data_status": "user_supplied_source_declared_not_independently_verified",
    }
    (destination / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest

def main():
    parser = argparse.ArgumentParser(description="Import a permitted Instagram creator CSV/JSONL and record provenance")
    parser.add_argument("source", type=Path)
    parser.add_argument("--destination", type=Path, default=Path("data/active"))
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--license", dest="license_id", required=True)
    parser.add_argument("--source-date", required=True, help="Dataset collection/snapshot date, YYYY-MM-DD")
    parser.add_argument("--rights-confirmed", action="store_true", help="Confirm you verified the source terms and are authorized to use the data")
    args = parser.parse_args()
    print(json.dumps(import_creators(args.source, args.destination, source_name=args.source_name, source_url=args.source_url, license_id=args.license_id, source_date=args.source_date, rights_confirmed=args.rights_confirmed), indent=2))

if __name__ == "__main__": main()
