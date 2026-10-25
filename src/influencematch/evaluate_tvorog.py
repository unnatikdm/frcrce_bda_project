"""Leave-one-Reel-out content-topic retrieval proxy; not campaign validation."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .provenance import sha256_file


def evaluate(data_dir: Path = Path("data/active")) -> dict:
    manifest_path = data_dir / "dataset_manifest.json"
    creators_path = data_dir / "creators.jsonl"
    reels_path = data_dir / "reels.jsonl"
    if not all(path.is_file() for path in (manifest_path, creators_path, reels_path)):
        raise FileNotFoundError("Import the checksum-verified Zenodo educational Reels dataset first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256_file(creators_path) != manifest.get("imported_file_sha256"):
        raise ValueError("Creator records do not match their provenance manifest")
    if sha256_file(reels_path) != manifest.get("reels_file_sha256"):
        raise ValueError("Reel records do not match their provenance manifest")
    creators = [json.loads(line) for line in creators_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    reels = [json.loads(line) for line in reels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(creators) != manifest.get("record_count") or len(reels) != manifest.get("reel_count"):
        raise ValueError("Imported creator or Reel count does not match the provenance manifest")

    all_topics: dict[str, Counter] = defaultdict(Counter)
    followers = {}
    for profile in creators:
        followers[profile["creator_id"]] = profile.get("followers") or 0
    for reel in reels:
        all_topics[reel["creator_id"]][reel["topic"].casefold()] += 1

    def summary(ranks: list[int]) -> dict:
        return {
            "queries": len(ranks),
            "mrr": sum(1 / rank for rank in ranks) / len(ranks) if ranks else None,
            "recall_at_1": sum(rank <= 1 for rank in ranks) / len(ranks) if ranks else None,
            "recall_at_3": sum(rank <= 3 for rank in ranks) / len(ranks) if ranks else None,
            "recall_at_5": sum(rank <= 5 for rank in ranks) / len(ranks) if ranks else None,
        }

    model_ranks = []
    follower_ranks = []
    by_topic: dict[str, list[int]] = defaultdict(list)
    for held_out in reels:
        query_topic = str(held_out["topic"]).casefold()
        target = held_out["creator_id"]
        account_ids = sorted(all_topics)
        documents = []
        for account_id in account_ids:
            counts = all_topics[account_id].copy()
            if account_id == target:
                counts[query_topic] -= 1
                if counts[query_topic] <= 0:
                    del counts[query_topic]
            documents.append(" ".join(topic for topic, count in counts.items() for _ in range(count)))
        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            matrix = vectorizer.fit_transform(documents + [query_topic])
        except ValueError:
            continue
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        ranked_model = sorted(zip(account_ids, scores), key=lambda item: (-item[1], item[0]))
        ranked_followers = sorted(account_ids, key=lambda account_id: (-followers[account_id], account_id))
        model_rank = next(index for index, (account_id, _) in enumerate(ranked_model, 1) if account_id == target)
        follower_rank = ranked_followers.index(target) + 1
        model_ranks.append(model_rank)
        follower_ranks.append(follower_rank)
        by_topic[query_topic].append(model_rank)

    if len(model_ranks) != len(reels):
        raise ValueError(f"Only {len(model_ranks)} of {len(reels)} Reels had usable topic text")
    return {
        "evaluation_type": "within-dataset leave-one-Reel-out topical retrieval proxy; not creator-level holdout or campaign validation",
        "dataset_name": manifest.get("dataset_name"),
        "source_url": manifest.get("source_url"),
        "license_id": manifest.get("license_id"),
        "source_collection_window": manifest.get("source_collection_window"),
        "creator_sha256": sha256_file(creators_path),
        "reel_sha256": sha256_file(reels_path),
        "accounts": len(creators),
        "reels_evaluated": len(reels),
        "ranking_method": "TF-IDF cosine similarity over each account's remaining source-coded Reel topic labels",
        "baseline_method": "descending source follower count; abbreviated source values converted to rounded estimates",
        "tfidf_topic_retrieval": summary(model_ranks),
        "follower_count_baseline": summary(follower_ranks),
        "tfidf_by_topic": {topic: summary(ranks) for topic, ranks in sorted(by_topic.items())},
        "limitations": [
            "The 300 Reel topics were coded by one researcher; this evaluates retrieval of that coding, not audience or business relevance.",
            "The held-out Reel's account remains represented by that account's other Reels, so this is not generalization to unseen creators.",
            "Follower counts are rounded estimates where the workbook uses abbreviated labels.",
            "Views and comments are not used as relevance labels; there are no observed campaign outcomes.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/active"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = evaluate(args.data)
    rendered = json.dumps(report, indent=2, ensure_ascii=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
