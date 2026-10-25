"""Optional PostgreSQL storage for imported, provenance-recorded creator data."""
import json
import hashlib
import os
from pathlib import Path
import psycopg
from psycopg.types.json import Jsonb
from .provenance import provenance_fields_present, sha256_file

SCHEMA = """CREATE TABLE IF NOT EXISTS creators (creator_id TEXT PRIMARY KEY, handle TEXT NOT NULL, platform TEXT NOT NULL, followers BIGINT, engagement_rate DOUBLE PRECISION, primary_topic TEXT, bio TEXT, country TEXT, language TEXT, source_record JSONB NOT NULL)"""
REELS_SCHEMA = """CREATE TABLE IF NOT EXISTS reels (reel_id TEXT PRIMARY KEY, creator_id TEXT NOT NULL REFERENCES creators(creator_id), topic TEXT, published_at DATE, analysis_date DATE, views BIGINT, comments BIGINT, url TEXT NOT NULL, source_record JSONB NOT NULL)"""
SNAPSHOT_SCHEMA = """CREATE TABLE IF NOT EXISTS dataset_snapshot (snapshot_id SMALLINT PRIMARY KEY CHECK (snapshot_id = 1), manifest JSONB NOT NULL, creator_count INTEGER NOT NULL, reel_count INTEGER NOT NULL, snapshot_sha256 TEXT NOT NULL, loaded_at TIMESTAMPTZ NOT NULL DEFAULT now())"""


def _snapshot_digest(creators: list[dict], reels: list[dict]) -> str:
    digest = hashlib.sha256()
    for label, rows, key in (("creators", creators, "creator_id"), ("reels", reels, "video_id")):
        digest.update(label.encode("utf-8") + b"\0")
        for row in sorted(rows, key=lambda item: str(item[key])):
            canonical = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            digest.update(canonical.encode("utf-8") + b"\n")
    return digest.hexdigest()

def load_creators(path: Path, database_url: str | None = None) -> int:
    manifest_path = path.parent / "dataset_manifest.json"
    if not manifest_path.is_file(): raise FileNotFoundError("Missing dataset provenance manifest")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    if not provenance_fields_present(manifest): raise ValueError("Dataset provenance is incomplete")
    if sha256_file(path) != manifest.get("imported_file_sha256"):
        raise ValueError("Creator data hash does not match provenance manifest")
    reels_path = path.parent / manifest["reels_file"] if manifest.get("reels_file") else None
    if reels_path is not None:
        if not reels_path.is_file(): raise FileNotFoundError("Manifest declares Reel records but reels.jsonl is missing")
        if sha256_file(reels_path) != manifest.get("reels_file_sha256"):
            raise ValueError("Reel data hash does not match provenance manifest")
    elif manifest.get("reel_count"):
        raise ValueError("Manifest declares Reel rows without a Reel data file")
    url = database_url or os.environ.get("DATABASE_URL", "postgresql://influence:influence@localhost:55432/influence")
    with psycopg.connect(url) as conn:
        conn.execute(SCHEMA)
        conn.execute(REELS_SCHEMA)
        conn.execute(SNAPSHOT_SCHEMA)
        # This table pair represents the one currently active imported dataset.
        # Replace it in one transaction so data from two source snapshots cannot mix.
        conn.execute("DELETE FROM reels")
        conn.execute("DELETE FROM creators")
        count=0
        creator_rows=[]
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                row=json.loads(line)
                conn.execute("""INSERT INTO creators (creator_id, handle, platform, followers, engagement_rate, primary_topic, bio, country, language, source_record) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (row["creator_id"],row["handle"],row["platform"],row.get("followers"),row.get("engagement_rate"),row.get("primary_topic"),row.get("bio"),row.get("country"),row.get("language"),Jsonb(row)))
                creator_rows.append(row)
                count+=1
        if count != manifest.get("record_count"):
            raise ValueError("PostgreSQL creator row count does not match the provenance manifest")
        reel_rows=[]
        reel_count=0
        if reels_path is not None:
            with reels_path.open(encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip(): continue
                    row=json.loads(line)
                    conn.execute("""INSERT INTO reels (reel_id, creator_id, topic, published_at, analysis_date, views, comments, url, source_record) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (str(row["video_id"]), row["creator_id"], row.get("topic"), row.get("publication_date"), row.get("analysis_date"), row.get("views"), row.get("comments"), row["url"], Jsonb(row)))
                    reel_rows.append(row)
                    reel_count+=1
            if reel_count != manifest.get("reel_count"):
                raise ValueError("PostgreSQL Reel row count does not match the provenance manifest")
        conn.execute("""INSERT INTO dataset_snapshot (snapshot_id, manifest, creator_count, reel_count, snapshot_sha256)
                        VALUES (1, %s, %s, %s, %s)
                        ON CONFLICT (snapshot_id) DO UPDATE SET manifest=EXCLUDED.manifest,
                        creator_count=EXCLUDED.creator_count, reel_count=EXCLUDED.reel_count,
                        snapshot_sha256=EXCLUDED.snapshot_sha256, loaded_at=now()""",
                     (Jsonb(manifest), count, reel_count, _snapshot_digest(creator_rows, reel_rows)))
        return count


def _read_validated_snapshot(conn) -> tuple[list[dict], dict, list[dict], str]:
    snapshot = conn.execute("SELECT manifest, creator_count, reel_count, snapshot_sha256 FROM dataset_snapshot WHERE snapshot_id=1").fetchone()
    if snapshot is None:
        raise ValueError("PostgreSQL has no loaded dataset snapshot; run python -m influencematch.db first")
    manifest, expected_creators, expected_reels, expected_digest = snapshot
    creators = [row[0] for row in conn.execute("SELECT source_record FROM creators ORDER BY creator_id").fetchall()]
    reels = [row[0] for row in conn.execute("SELECT source_record FROM reels ORDER BY reel_id").fetchall()]
    if len(creators) != expected_creators or len(creators) != manifest.get("record_count"):
        raise ValueError("PostgreSQL creator row count does not match the loaded snapshot")
    if len(reels) != expected_reels or len(reels) != manifest.get("reel_count", 0):
        raise ValueError("PostgreSQL Reel row count does not match the loaded snapshot")
    if _snapshot_digest(creators, reels) != expected_digest:
        raise ValueError("PostgreSQL source records do not match the loaded snapshot digest")
    if not provenance_fields_present(manifest):
        raise ValueError("PostgreSQL dataset provenance is incomplete")
    return creators, manifest, reels, expected_digest


def read_dataset(database_url: str | None = None) -> tuple[list[dict], dict]:
    """Read and integrity-check the currently loaded source snapshot."""
    url = database_url or os.environ.get("DATABASE_URL", "postgresql://influence:influence@localhost:55432/influence")
    with psycopg.connect(url) as conn:
        creators, manifest, _, snapshot_digest = _read_validated_snapshot(conn)
    manifest = dict(manifest)
    manifest["database_snapshot_sha256"] = snapshot_digest
    return creators, manifest


def read_analytics_summary(database_url: str | None = None) -> dict:
    """Compute provenance-bound descriptive summaries using PostgreSQL SQL."""
    url = database_url or os.environ.get("DATABASE_URL", "postgresql://influence:influence@localhost:55432/influence")
    with psycopg.connect(url) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        _, manifest, _, snapshot_digest = _read_validated_snapshot(conn)
        followers = conn.execute("""
            SELECT count(*) AS creator_count, count(followers) AS followers_count,
                   min(followers) AS minimum, percentile_cont(0.5) WITHIN GROUP (ORDER BY followers) AS median,
                   max(followers) AS maximum
            FROM creators
        """).fetchone()
        niche_rows = conn.execute("""
            SELECT lower(n.value) AS niche, count(*) AS creator_count
            FROM creators c
            CROSS JOIN LATERAL jsonb_array_elements_text(
                CASE WHEN jsonb_typeof(c.source_record->'niches') = 'array'
                     THEN c.source_record->'niches' ELSE '[]'::jsonb END
            ) AS n(value)
            GROUP BY lower(n.value) ORDER BY lower(n.value)
        """).fetchall()
        metric_rows = conn.execute("""
            SELECT m.key, count(*) AS creator_count
            FROM creators c
            CROSS JOIN LATERAL jsonb_each(
                CASE WHEN jsonb_typeof(c.source_record->'source_metrics') = 'object'
                     THEN c.source_record->'source_metrics' ELSE '{}'::jsonb END
            ) AS m(key, value)
            GROUP BY m.key ORDER BY m.key
        """).fetchall()
        reel_rows = conn.execute("""
            SELECT topic, count(*) AS post_count, count(DISTINCT creator_id) AS creator_count,
                   avg(views)::double precision AS mean_views,
                   percentile_cont(0.5) WITHIN GROUP (ORDER BY views) AS median_views,
                   avg(comments)::double precision AS mean_comments,
                   percentile_cont(0.5) WITHIN GROUP (ORDER BY comments) AS median_comments,
                   bool_or((source_record->>'views_are_approximate')::boolean) AS views_are_approximate,
                   bool_or((source_record->>'comments_are_approximate')::boolean) AS comments_are_approximate
            FROM reels WHERE topic IS NOT NULL
            GROUP BY topic ORDER BY count(*) DESC, topic
        """).fetchall()
        total_reels = conn.execute("SELECT count(*) FROM reels").fetchone()[0]

    dataset_key = manifest.get("dataset_key")
    return {
        "dataset": {key: manifest.get(key) for key in ("dataset_name", "dataset_key", "source_url", "license_id", "source_collection_date", "retrieved_at_utc")},
        "database_snapshot_sha256": snapshot_digest,
        "sql_backend": "PostgreSQL",
        "creator_count": int(followers[0]),
        "follower_summary": {
            "known_count": int(followers[1]), "minimum": followers[2], "median": followers[3], "maximum": followers[4],
            "values_are_approximate": dataset_key == "zenodo_23301344_educational_reels",
        },
        "niche_creator_counts": [{"niche": row[0], "creator_count": int(row[1])} for row in niche_rows],
        "source_metric_coverage": [{"field": row[0], "creator_count": int(row[1])} for row in metric_rows],
        "reel_count": int(total_reels),
        "reel_topic_summary": [{
            "topic": row[0], "post_count": int(row[1]), "creator_count": int(row[2]),
            "mean_views": row[3], "median_views": row[4], "mean_comments": row[5], "median_comments": row[6],
            "views_are_approximate": row[7], "comments_are_approximate": row[8],
        } for row in reel_rows],
        "limits": ["Descriptive summaries of the loaded historical source snapshot only", "Not current platform metrics or campaign outcomes", "Source-specific labels and measurement limitations are retained"],
    }

if __name__ == "__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--file", type=Path, default=Path("data/active/creators.jsonl")); args=ap.parse_args()
    loaded=load_creators(args.file)
    manifest=json.loads((args.file.parent / "dataset_manifest.json").read_text(encoding="utf-8"))
    print(f"Loaded {loaded} creator and {manifest.get('reel_count', 0)} Reel records into PostgreSQL")
