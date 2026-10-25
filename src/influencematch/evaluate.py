"""Descriptive research-proxy evaluation; not a campaign-effectiveness test."""
import argparse
import json
import math
from pathlib import Path
from statistics import fmean, pstdev

from scipy.stats import spearmanr
from sklearn.model_selection import KFold

from .provenance import sha256_file

NICHES = ("fitness", "beauty", "lifestyle", "travel")


def evaluate(data_dir: Path = Path("data/active")) -> dict:
    records_path = data_dir / "creators.jsonl"
    manifest_path = data_dir / "dataset_manifest.json"
    if not records_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Import the licensed RepOD dataset before evaluation")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256_file(records_path) != manifest.get("imported_file_sha256"):
        raise ValueError("Creator file hash does not match its manifest")
    profiles = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(profiles) != manifest.get("record_count"):
        raise ValueError("Creator count does not match its provenance manifest")

    def correlation(rows):
        pairs = [(p.get("research_ratings", {}).get("opinion_leadership"),
                  p.get("research_ratings", {}).get("intention_recommendation")) for p in rows]
        pairs = [(float(x), float(y)) for x, y in pairs if x is not None and y is not None]
        if len(pairs) < 3:
            return {"n": len(pairs), "spearman_rho": None, "p_value": None, "status": "insufficient observations"}
        stat = spearmanr([x for x, _ in pairs], [y for _, y in pairs])
        return {"n": len(pairs), "spearman_rho": float(stat.statistic), "p_value": float(stat.pvalue),
                "status": "computed from study ratings"}

    def ranking_quality(rows, k=10):
        eligible = []
        for profile in rows:
            ratings = profile.get("research_ratings", {})
            target = ratings.get("intention_recommendation")
            opinion = ratings.get("opinion_leadership")
            followers = profile.get("followers")
            if target is not None and opinion is not None and followers is not None:
                eligible.append((profile["creator_id"], float(target), float(opinion), float(followers)))
        if not eligible:
            return {"n": 0, "k": 0, "opinion_leadership_ndcg": None, "follower_count_baseline_ndcg": None}
        cutoff = min(k, len(eligible))

        def ndcg(key):
            ranked = sorted(eligible, key=lambda item: (-item[key], item[0]))[:cutoff]
            ideal = sorted(eligible, key=lambda item: (-item[1], item[0]))[:cutoff]
            dcg = sum((2 ** item[1] - 1) / math.log2(index + 2) for index, item in enumerate(ranked))
            idcg = sum((2 ** item[1] - 1) / math.log2(index + 2) for index, item in enumerate(ideal))
            return dcg / idcg if idcg else None

        return {"n": len(eligible), "k": cutoff, "opinion_leadership_ndcg": ndcg(2),
                "follower_count_baseline_ndcg": ndcg(3), "relevance": "judge-rated intention to recommend; graded gain 2^rating - 1"}

    def candidate_fold_quality(rows, k=10, folds=5):
        eligible = []
        for profile in rows:
            ratings = profile.get("research_ratings", {})
            target = ratings.get("intention_recommendation")
            opinion = ratings.get("opinion_leadership")
            followers = profile.get("followers")
            if target is not None and opinion is not None and followers is not None:
                eligible.append((profile["creator_id"], float(target), float(opinion), float(followers)))
        if len(eligible) < folds:
            return {"n": len(eligible), "folds": 0, "status": "insufficient eligible creators"}

        splitter = KFold(n_splits=folds, shuffle=True, random_state=42)
        fold_results = []
        for fold_number, (_, heldout_indices) in enumerate(splitter.split(eligible), start=1):
            fold_candidates = [eligible[index] for index in heldout_indices]
            cutoff = min(k, len(fold_candidates))

            def ndcg(key):
                ranked = sorted(fold_candidates, key=lambda item: (-item[key], item[0]))[:cutoff]
                ideal = sorted(fold_candidates, key=lambda item: (-item[1], item[0]))[:cutoff]
                dcg = sum((2 ** item[1] - 1) / math.log2(index + 2) for index, item in enumerate(ranked))
                idcg = sum((2 ** item[1] - 1) / math.log2(index + 2) for index, item in enumerate(ideal))
                return dcg / idcg if idcg else None

            fold_results.append({
                "fold": fold_number,
                "n": len(fold_candidates),
                "k": cutoff,
                "opinion_leadership_ndcg": ndcg(2),
                "follower_count_baseline_ndcg": ndcg(3),
            })

        opinion_values = [item["opinion_leadership_ndcg"] for item in fold_results if item["opinion_leadership_ndcg"] is not None]
        follower_values = [item["follower_count_baseline_ndcg"] for item in fold_results if item["follower_count_baseline_ndcg"] is not None]
        return {
            "n": len(eligible),
            "folds": len(fold_results),
            "splitter": "KFold(shuffle=True, random_state=42); each creator occurs in one candidate fold",
            "opinion_leadership_ndcg_mean": fmean(opinion_values) if opinion_values else None,
            "opinion_leadership_ndcg_population_std": pstdev(opinion_values) if len(opinion_values) > 1 else 0.0 if opinion_values else None,
            "follower_count_baseline_ndcg_mean": fmean(follower_values) if follower_values else None,
            "follower_count_baseline_ndcg_population_std": pstdev(follower_values) if len(follower_values) > 1 else 0.0 if follower_values else None,
            "fold_results": fold_results,
            "scope": "This is a candidate-fold stability diagnostic, not model cross-validation: no model is fitted. Each fold ranks only its included creators using their observed opinion-leadership ratings and evaluates against their intention-to-recommend ratings from the same historical study. It is not independent outcome or campaign validation.",
        }

    return {
        "evaluation_type": "within-dataset descriptive proxy; not independent or campaign-outcome validation",
        "dataset_name": manifest.get("dataset_name"), "source_url": manifest.get("source_url"),
        "license_id": manifest.get("license_id"), "source_collection_date": manifest.get("source_collection_date"),
        "retrieved_at_utc": manifest.get("retrieved_at_utc"), "input_sha256": sha256_file(records_path),
        "records_loaded": len(profiles),
        "comparison": "Spearman correlation: judge-rated opinion leadership vs judge-rated intention to recommend",
        "overall": correlation(profiles),
        "by_niche": {niche: correlation([p for p in profiles if niche in p.get("niches", [])]) for niche in NICHES},
        "ranking_evaluation": {
            "metric": "NDCG@10, target judge-rated intention to recommend",
            "scope": "Same-sample retrospective ranking proxy, not a held-out evaluation",
            "overall": ranking_quality(profiles),
            "by_niche": {niche: ranking_quality([p for p in profiles if niche in p.get("niches", [])]) for niche in NICHES},
            "candidate_fold_diagnostic": candidate_fold_quality(profiles),
        },
        "limitations": ["Same research sample supplies ranking and proxy target", "Judge ratings are not observed campaign outcomes", "No causal or predictive claim", "Three-month observation window has no disclosed exact dates"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/active"))
    parser.add_argument("--report", type=Path, help="write the evaluation JSON report to this path")
    args = parser.parse_args()
    output = json.dumps(evaluate(args.data), indent=2, ensure_ascii=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
