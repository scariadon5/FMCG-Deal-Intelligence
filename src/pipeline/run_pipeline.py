"""
run_pipeline.py

The orchestrator: runs the full pipeline end-to-end on live-ingested news.

Flow:
  1. Ingest live articles (Google News RSS)
  2. Stage 1: ML relevance classifier (keep only predicted "fmcg_deal")
  3. Stage 2: FMCG entity + deal-verb rule gate (keep only passes)
  4. Deduplication (TF-IDF cosine similarity near-dup removal)
  5. Credibility scoring + ranking

Outputs:
  - Prints funnel counts at each stage (for the pipeline-explanation deliverable)
  - Saves final surviving articles to data/processed/final_articles.csv and .json
"""

import sys
import os
import json
import joblib
import pandas as pd
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# Make sibling modules importable when running this script directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingest_live_news import ingest_all
from stage2 import passes_stage2
from deduplication import deduplicate_articles
from credibility_scoring import filter_by_credibility

MODEL_PATH = "models/relevance_classifier.pkl"
VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"
OUTPUT_CSV = "data/processed/final_articles.csv"
OUTPUT_JSON = "data/processed/final_articles.json"

# The assignment requires the newsletter to reflect "the latest developments"
# via real-time sourcing - Google News RSS itself has no date-range operator,
# so this is enforced explicitly here rather than left to RSS ranking alone.
RECENCY_DAYS = 90  # default; overridable per-run via run_pipeline(recency_days=...)


def load_stage1_model():
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    return model, vectorizer


def is_recent(article: dict, days: int = RECENCY_DAYS) -> bool:
    """True if article's pub_date parses and falls within the last `days` days.
    Unparseable/missing dates are dropped rather than assumed recent - we
    can't claim a "real-time" guarantee for a date we can't verify."""
    raw = article.get("pub_date", "")
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return dt >= cutoff


def apply_recency_filter(articles: list, days: int = RECENCY_DAYS) -> list:
    return [a for a in articles if is_recent(a, days)]


def apply_stage1(articles: list, model, vectorizer) -> list:
    """Keep only articles the trained classifier predicts as fmcg_deal (label=1)."""
    texts = [a["text"] for a in articles]
    X = vectorizer.transform(texts)
    predictions = model.predict(X)

    survivors = []
    for article, pred in zip(articles, predictions):
        if pred == 1:
            survivors.append(article)
    return survivors


def apply_stage2(articles: list) -> list:
    """Keep only articles that pass the FMCG entity + deal-verb rule gate."""
    survivors = []
    for article in articles:
        result = passes_stage2(article["text"])
        if result["passed"]:
            article_copy = dict(article)
            article_copy["stage2_reason"] = result["reason"]
            survivors.append(article_copy)
    return survivors


def run_pipeline(recency_days: int = RECENCY_DAYS):
    print("=" * 60)
    print("STEP 1: Live ingestion")
    print("=" * 60)
    articles = ingest_all()
    count_ingested = len(articles)

    print("\n" + "=" * 60)
    print(f"STEP 1.5: Recency filter (last {recency_days} days)")
    print("=" * 60)
    recent_articles = apply_recency_filter(articles, days=recency_days)
    count_recent = len(recent_articles)
    print(f"Recency filter kept {count_recent} / {count_ingested} articles published in the last {recency_days} days")

    print("\n" + "=" * 60)
    print("STEP 2: Stage 1 - ML relevance classifier")
    print("=" * 60)
    model, vectorizer = load_stage1_model()
    stage1_survivors = apply_stage1(recent_articles, model, vectorizer)
    count_stage1 = len(stage1_survivors)
    print(f"Stage 1 kept {count_stage1} / {count_recent} articles")

    print("\n" + "=" * 60)
    print("STEP 3: Stage 2 - FMCG keyword/entity gate")
    print("=" * 60)
    stage2_survivors = apply_stage2(stage1_survivors)
    count_stage2 = len(stage2_survivors)
    print(f"Stage 2 kept {count_stage2} / {count_stage1} articles")

    print("\n" + "=" * 60)
    print("STEP 4: Deduplication")
    print("=" * 60)
    deduped = deduplicate_articles(stage2_survivors)
    count_deduped = len(deduped)
    print(f"Deduplication kept {count_deduped} / {count_stage2} articles")

    print("\n" + "=" * 60)
    print("STEP 5: Credibility scoring + ranking")
    print("=" * 60)
    final = filter_by_credibility(deduped, min_tier="tier_3")  # rank, don't drop
    count_final = len(final)
    print(f"Final article count: {count_final}")

    # --- Funnel summary ---
    print("\n" + "=" * 60)
    print("PIPELINE FUNNEL SUMMARY")
    print("=" * 60)
    print(f"  Ingested:           {count_ingested}")
    print(f"  After Recency:      {count_recent}  ({count_recent/count_ingested*100:.1f}% of original)")
    print(f"  After Stage 1:      {count_stage1}  ({count_stage1/count_ingested*100:.1f}% kept)")
    print(f"  After Stage 2:      {count_stage2}  ({count_stage2/count_ingested*100:.1f}% of original)")
    print(f"  After Dedup:        {count_deduped}  ({count_deduped/count_ingested*100:.1f}% of original)")
    print(f"  Final (scored):     {count_final}")

    # --- Save outputs ---
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df = pd.DataFrame(final)
    df.to_csv(OUTPUT_CSV, index=False)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print(f"\nSaved final results to {OUTPUT_CSV} and {OUTPUT_JSON}")

    # --- Show the actual surviving articles ---
    print("\n" + "=" * 60)
    print("FINAL ARTICLES (ranked by credibility)")
    print("=" * 60)
    for a in final:
        print(f"\n[{a.get('credibility_tier', '?')} | {a.get('source', '?')}] {a['text']}")
        print(f"  Stage 2 reason: {a.get('stage2_reason', 'n/a')}")
    funnel = {
        "ingested": count_ingested,
        "recency_filtered": count_recent,
        "recency_days": recency_days,
        "stage1": count_stage1,
        "stage2": count_stage2,
        "dedup": count_deduped,
        "final": count_final,
    }
    with open("data/processed/funnel_summary.json", "w") as f:
        json.dump(funnel, f, indent=2)

    return final


if __name__ == "__main__":
    run_pipeline()
