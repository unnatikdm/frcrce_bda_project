"""Explainable text matching over an imported, source-declared real dataset."""
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def match(profiles: list[dict], brief: str, limit: int = 10, *, country: str | None = None, language: str | None = None, min_followers: int | None = None, max_followers: int | None = None, min_engagement_rate: float | None = None, max_engagement_rate: float | None = None, budget_amount: float | None = None, budget_currency: str | None = None, rate_deliverable: str | None = None, deliverable_count: int = 1) -> list[dict]:
    if not profiles or not brief.strip(): return []
    candidates = []
    for profile in profiles:
        if country and str(profile.get("country", "")).casefold() != country.casefold(): continue
        if language and str(profile.get("language", "")).casefold() != language.casefold(): continue
        followers = profile.get("followers")
        if min_followers is not None and (followers is None or int(followers) < min_followers): continue
        if max_followers is not None and (followers is None or int(followers) > max_followers): continue
        engagement = profile.get("engagement_rate")
        if min_engagement_rate is not None and (engagement is None or float(engagement) < min_engagement_rate): continue
        if max_engagement_rate is not None and (engagement is None or float(engagement) > max_engagement_rate): continue
        if budget_amount is not None:
            rate = profile.get("rate_amount")
            if rate is None or not profile.get("rate_currency") or not profile.get("rate_deliverable"):
                continue
            if str(profile["rate_currency"]).strip().casefold() != str(budget_currency).strip().casefold(): continue
            if str(profile["rate_deliverable"]).strip().casefold() != str(rate_deliverable).strip().casefold(): continue
            if float(rate) * deliverable_count > budget_amount: continue
        candidates.append(profile)
    if not candidates: return []
    # The CC BY RepOD research file has no bios. For it, match only the four
    # explicitly coded niches and rank by the study's judge-rated measure.
    niche_terms = {"fitness", "beauty", "lifestyle", "travel"}
    requested_niches = niche_terms & set(brief.casefold().replace("/", " ").replace(",", " ").split())
    if requested_niches and any(p.get("niches") for p in candidates):
        ranked = []
        for profile in candidates:
            overlap = requested_niches & {str(n).casefold() for n in profile.get("niches", [])}
            if overlap:
                ratings = profile.get("research_ratings", {})
                observed_score = ratings.get("opinion_leadership")
                observed_items = profile.get("research_rating_items", {}).get("opinion_leadership", {})
                item_count = profile.get("research_rating_item_counts", {}).get("opinion_leadership")
                if observed_score is None or not observed_items:
                    continue
                item_values = [float(value) for value in observed_items.values()]
                if item_count != len(item_values):
                    raise ValueError(f"{profile.get('creator_id')} has an inconsistent opinion-leadership item count")
                score = sum(item_values) / len(item_values)
                if not math.isclose(score, float(observed_score), rel_tol=1e-12, abs_tol=1e-12):
                    raise ValueError(f"{profile.get('creator_id')} opinion-leadership mean does not match its observed items")
                ranked.append((profile, score, sorted(overlap)))
        ranked.sort(key=lambda x: (-x[1], x[0]["creator_id"]))
        results = []
        for profile, score, terms in ranked[:limit]:
            observed_items = profile.get("research_rating_items", {}).get("opinion_leadership", {})
            numerator = sum(observed_items.values()) if observed_items else None
            results.append({**profile, "match_score": round(score, 4), "matched_terms": terms,
                            "score_method": "niche overlap, then study judge-rated opinion leadership (historical research measure)",
                            "score_explanation": {
                                "method": "mean_of_observed_source_rating_items",
                                "criterion": "opinion_leadership",
                                "value": round(score, 4),
                                "unrounded_value": score,
                                "observed_item_count": item_count,
                                "observed_items": observed_items,
                                "numerator": numerator,
                                "formula": "sum(observed_items.values()) / observed_item_count",
                                "matched_niches": terms,
                                "missing_rating_policy": "exclude profile; no score is imputed",
                            }})
        return results
    docs = [" ".join(str(p.get(field, "")) for field in ("bio", "primary_topic")) for p in candidates]
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        matrix = vectorizer.fit_transform(docs + [brief])
    except ValueError:
        return []
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    analyzer = vectorizer.build_analyzer()
    brief_terms = set(analyzer(brief))
    feature_names = vectorizer.get_feature_names_out()
    ranked = sorted(enumerate(scores), key=lambda x: (-x[1], candidates[x[0]]["creator_id"]))
    results = []
    for i, score in ranked:
        if score <= 0: continue
        products = matrix[-1].multiply(matrix[i])
        term_contributions = sorted(
            ({"term": str(feature_names[index]), "contribution": float(value)}
             for index, value in zip(products.indices, products.data) if value > 0),
            key=lambda item: (-item["contribution"], item["term"]),
        )
        explanation = [item["term"] for item in term_contributions if item["term"] in brief_terms]
        rounded_score = round(float(score), 4)
        results.append({**candidates[i], "match_score": rounded_score, "matched_terms": explanation,
                        "score_method": "cosine similarity over TF-IDF of imported bio/topic text",
                        "score_explanation": {"method": "tfidf_cosine_similarity", "value": rounded_score,
                                              "unrounded_value": float(score),
                                              "matched_terms": explanation,
                                              "term_contributions": term_contributions,
                                              "contribution_sum": sum(item["contribution"] for item in term_contributions)}})
        if len(results) >= limit: break
    return results
