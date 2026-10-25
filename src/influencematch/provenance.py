"""Hashing and structural checks for local dataset provenance."""
import hashlib
from pathlib import Path

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def provenance_fields_present(manifest: dict) -> bool:
    required = ("dataset_name", "source_url", "license_id", "source_collection_date", "rights_attestation", "data_status", "record_count")
    return all(isinstance(manifest.get(key), str) and manifest[key].strip() for key in required[:-1]) and manifest.get("record_count", 0) > 0
