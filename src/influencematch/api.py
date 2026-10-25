"""API over user-supplied, provenance-recorded creator data only."""
import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
try:
    import psycopg
    from .db import read_analytics_summary, read_dataset as read_postgres_dataset
except ImportError:
    psycopg = None
    read_analytics_summary = None
    read_postgres_dataset = None

from .matching import match
from .provenance import provenance_fields_present, sha256_file
from .engagement_context import engagement_context

DATA = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent.parent / "data")) / "active"
app = FastAPI(title="InfluenceMatch Local API", version="0.2.0", description="Uses only user-supplied data with declared provenance")
class Brief(BaseModel):
    brief: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100)
    creator_country: str | None = Field(default=None, min_length=2, max_length=2)
    language: str | None = Field(default=None, min_length=2, max_length=12)
    min_followers: int | None = Field(default=None, ge=0)
    max_followers: int | None = Field(default=None, ge=0)
    min_engagement_rate: float | None = Field(default=None, ge=0, le=1)
    max_engagement_rate: float | None = Field(default=None, ge=0, le=1)
    budget_amount: float | None = Field(default=None, gt=0)
    budget_currency: str | None = Field(default=None, min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    rate_deliverable: str | None = Field(default=None, min_length=2, max_length=80)
    deliverable_count: int = Field(default=1, ge=1, le=100)

    @model_validator(mode="after")
    def budget_fields_are_complete(self):
        fields = (self.budget_amount is not None, self.budget_currency is not None, self.rate_deliverable is not None)
        if any(fields) and not all(fields):
            raise ValueError("budget_amount, budget_currency, and rate_deliverable must be provided together")
        return self

def dataset_state():
    backend = os.environ.get("INFLUENCEMATCH_DATA_BACKEND", "files").strip().casefold()
    if backend == "postgres":
        if psycopg is None or read_postgres_dataset is None:
            return None, {"status": "backend_unavailable", "reason": "PostgreSQL driver psycopg is not installed.", "profiles_loaded": 0, "backend": "postgres"}
        try:
            profiles, manifest = read_postgres_dataset()
        except ValueError as exc:
            reason = str(exc)
            status = "unavailable" if "no loaded dataset snapshot" in reason else "invalid"
            return None, {"status": status, "reason": reason, "profiles_loaded": 0, "backend": "postgres"}
        except psycopg.errors.UndefinedTable:
            return None, {"status": "unavailable", "reason": "PostgreSQL has no loaded dataset snapshot; run python -m influencematch.db first.", "profiles_loaded": 0, "backend": "postgres"}
        except psycopg.Error:
            return None, {"status": "backend_unavailable", "reason": "PostgreSQL is unavailable; check DATABASE_URL and confirm the local service is running.", "profiles_loaded": 0, "backend": "postgres"}
        licensed_research = str(manifest.get("data_status", "")).startswith("licensed_research_data")
        status = "available" if licensed_research else "available_unverified"
        reason = ("Published license and source checksum are recorded; historical observations are not independently revalidated." if licensed_research else "Source and rights were declared by the operator but not independently verified.")
        return (profiles, manifest), {"status": status, "reason": reason, "profiles_loaded": len(profiles), "dataset_name": manifest.get("dataset_name"), "source_url": manifest.get("source_url"), "license_id": manifest.get("license_id"), "source_collection_date": manifest.get("source_collection_date"), "database_snapshot_sha256": manifest.get("database_snapshot_sha256"), "backend": "postgres"}
    if backend != "files":
        return None, {"status": "invalid", "reason": "INFLUENCEMATCH_DATA_BACKEND must be 'files' or 'postgres'.", "profiles_loaded": 0}
    data_root = Path(os.environ["DATA_DIR"]) / "active" if "DATA_DIR" in os.environ else DATA
    manifest_path, data_path = data_root / "dataset_manifest.json", data_root / "creators.jsonl"
    if not manifest_path.is_file() or not data_path.is_file():
        return None, {"status": "unavailable", "reason": "No imported real dataset is available. Import a permitted dataset with source and license metadata.", "profiles_loaded": 0}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not provenance_fields_present(manifest):
            return None, {"status": "invalid", "reason": "Dataset provenance is incomplete.", "profiles_loaded": 0}
        digest = sha256_file(data_path)
        if manifest.get("imported_file_sha256") != digest:
            return None, {"status": "invalid", "reason": "Imported data hash does not match its provenance manifest.", "profiles_loaded": 0}
        profiles = [json.loads(line) for line in data_path.open(encoding="utf-8") if line.strip()]
        if len(profiles) != manifest.get("record_count"):
            return None, {"status": "invalid", "reason": "Imported record count does not match its provenance manifest.", "profiles_loaded": 0}
        if manifest.get("reels_file"):
            reels_relative = Path(str(manifest["reels_file"]))
            data_root_resolved = data_root.resolve()
            reels_path = data_root / reels_relative
            if reels_relative.is_absolute() or ".." in reels_relative.parts or not reels_path.resolve().is_relative_to(data_root_resolved):
                return None, {"status": "invalid", "reason": "Declared Reel file path escapes the imported dataset directory.", "profiles_loaded": 0}
            if reels_path.is_symlink() or not reels_path.is_file():
                return None, {"status": "invalid", "reason": "Dataset declares a missing or linked Reel file.", "profiles_loaded": 0}
            if sha256_file(reels_path) != manifest.get("reels_file_sha256"):
                return None, {"status": "invalid", "reason": "Reel data hash does not match its provenance manifest.", "profiles_loaded": 0}
            reel_count = sum(1 for line in reels_path.open(encoding="utf-8") if line.strip())
            if reel_count != manifest.get("reel_count"):
                return None, {"status": "invalid", "reason": "Reel record count does not match its provenance manifest.", "profiles_loaded": 0}
        elif manifest.get("reel_count"):
            return None, {"status": "invalid", "reason": "Dataset declares Reel records but no Reel file.", "profiles_loaded": 0}
        licensed_research = str(manifest.get("data_status", "")).startswith("licensed_research_data")
        status = "available" if licensed_research else "available_unverified"
        reason = ("Published license and file checksum are recorded; source observations are historical and not independently revalidated." if licensed_research else "Source and rights were declared by the operator but not independently verified.")
        return (profiles, manifest), {"status": status, "reason": reason, "profiles_loaded": len(profiles), "dataset_name": manifest.get("dataset_name"), "source_url": manifest.get("source_url"), "license_id": manifest.get("license_id"), "source_collection_date": manifest.get("source_collection_date"), "creator_file_sha256": manifest.get("imported_file_sha256")}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None, {"status": "invalid", "reason": "Dataset files or provenance manifest are unreadable.", "profiles_loaded": 0}

@app.get("/health")
def health():
    _, state = dataset_state()
    return {"service": "ok", "dataset": state}

@app.get("/dataset")
def dataset(): return dataset_state()[1]

@app.get("/analytics/summary")
def analytics_summary():
    if os.environ.get("INFLUENCEMATCH_DATA_BACKEND", "files").strip().casefold() != "postgres":
        raise HTTPException(status_code=409, detail="SQL summaries require INFLUENCEMATCH_DATA_BACKEND=postgres and a loaded PostgreSQL snapshot.")
    if read_analytics_summary is None or psycopg is None:
        raise HTTPException(status_code=503, detail="PostgreSQL analytics driver is not installed.")
    try:
        return read_analytics_summary()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="PostgreSQL analytics are unavailable; verify the database service and loaded snapshot.") from exc

@app.get("/creators")
def creators(limit: int = 100):
    loaded, state = dataset_state()
    if loaded is None: raise HTTPException(status_code=503, detail=state)
    return loaded[0][:max(0, min(limit, 1000))]

@app.post("/match")
def recommend(request: Brief):
    loaded, state = dataset_state()
    if loaded is None: raise HTTPException(status_code=503, detail=state)
    licensed_research = str(loaded[1].get("data_status", "")).startswith("licensed_research_data")
    dataset_key = loaded[1].get("dataset_key")
    if licensed_research and (request.creator_country or request.language or request.min_engagement_rate is not None or request.max_engagement_rate is not None):
        raise HTTPException(status_code=422, detail="This dataset has no creator country, language, or normalized engagement-rate values; remove those filters.")
    if request.budget_amount is not None and not any(p.get("rate_amount") is not None and p.get("rate_currency") and p.get("rate_deliverable") for p in loaded[0]):
        raise HTTPException(status_code=422, detail="This dataset has no complete per-deliverable creator rates; remove the budget filter or import verified rate amount, currency, and deliverable fields.")
    results = match(loaded[0], request.brief, request.limit, country=request.creator_country, language=request.language, min_followers=request.min_followers, max_followers=request.max_followers, min_engagement_rate=request.min_engagement_rate, max_engagement_rate=request.max_engagement_rate, budget_amount=request.budget_amount, budget_currency=request.budget_currency, rate_deliverable=request.rate_deliverable, deliverable_count=request.deliverable_count)
    for result in results:
        result["engagement_reference"] = engagement_context(result)
    if dataset_key == "zenodo_23301344_educational_reels":
        note = ("Recommendations use TF-IDF cosine similarity over topics coded on 300 observed educational Reels, aggregated by account. "
                "Views, comments, and the three single-researcher quality ratings are descriptive source metrics, not rank inputs or campaign outcomes. "
                "Follower labels may be rounded estimates. Country, language, normalized engagement rate, and per-creator price are unavailable.")
    elif licensed_research:
        note = "RepOD matches require niche overlap with fitness, beauty, lifestyle, or travel and rank by historical judge-rated opinion leadership, calculated as the mean of observed source items. Each result includes its rating-item count and score explanation; profiles without that rating are excluded rather than assigned a zero. Source compensation currency and engagement-rate units are unspecified, so those values are not used for budget or engagement-rate filtering. Creator location is not audience geography; audience composition and campaign outcomes are unavailable."
    else:
        note = "Ranking is TF-IDF cosine similarity over source-provided bio/topic text. Engagement, follower, and exact-currency per-deliverable budget constraints are optional eligibility filters, not score inputs. Creator location is not audience geography. Audience composition and campaign outcomes are not measured."
    dataset_info = {k: loaded[1].get(k) for k in ("dataset_name", "source_url", "license_id", "source_collection_date", "retrieved_at_utc", "imported_file_sha256", "reels_file_sha256", "database_snapshot_sha256")}
    return {"data_status": state["status"], "dataset": dataset_info, "results": results, "result_count": len(results), "note": note}
