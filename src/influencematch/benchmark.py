"""Repeatable local Spark ETL timing over the imported authentic dataset."""
import argparse
import json
import os
import platform
import statistics
import time
from pathlib import Path

from .pipeline import run
from .provenance import sha256_file


def benchmark(raw: Path, output_root: Path, repeat: int = 3, master: str = "local[2]") -> dict:
    if repeat < 1:
        raise ValueError("repeat must be positive")
    manifest = json.loads((raw / "dataset_manifest.json").read_text(encoding="utf-8"))
    data_file = raw / "creators.jsonl"
    if sha256_file(data_file) != manifest.get("imported_file_sha256"):
        raise ValueError("Creator file hash does not match its provenance manifest")
    reels_file = raw / manifest["reels_file"] if manifest.get("reels_file") else None
    if reels_file is not None:
        if not reels_file.is_file() or sha256_file(reels_file) != manifest.get("reels_file_sha256"):
            raise ValueError("Reel data file does not match its provenance manifest")
    timings = []
    for iteration in range(repeat):
        start = time.perf_counter()
        count = run(raw, output_root / f"iteration_{iteration + 1}", master)
        elapsed = time.perf_counter() - start
        reel_count = manifest.get("reel_count", 0)
        total_rows = count + reel_count
        timings.append({"iteration": iteration + 1, "creator_rows": count, "reel_rows": reel_count,
                        "total_rows_written": total_rows, "wall_seconds": elapsed,
                        "total_rows_per_second_including_startup": total_rows / elapsed})
    seconds = [item["wall_seconds"] for item in timings]
    return {
        "benchmark_type": "local end-to-end Spark creator and optional Reel JSONL read, Parquet write, count, and manifest copy; includes Spark startup",
        "not_representative_of_large_scale_cluster_throughput": True,
        "source_name": manifest.get("dataset_name"), "source_url": manifest.get("source_url"),
        "source_sha256": sha256_file(data_file), "source_rows": manifest.get("record_count"),
        "reels_sha256": sha256_file(reels_file) if reels_file else None,
        "reel_rows": manifest.get("reel_count", 0),
        "host_platform": platform.platform(), "python": platform.python_version(),
        "logical_cpus": os.cpu_count(), "spark_master": master,
        "iterations": timings, "median_wall_seconds": statistics.median(seconds),
    }


if __name__ == "__main__":
    local_data_home = Path(os.environ.get("LOCALAPPDATA", os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))))
    default_output = local_data_home / "InfluenceMatch" / "benchmarks"
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("data/active"))
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--master", default="local[2]")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = benchmark(args.raw, args.output, args.repeat, args.master)
    rendered = json.dumps(report, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
