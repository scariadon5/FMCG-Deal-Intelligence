"""
credibility_scoring.py

Simple, rule-based source credibility tiering.
No ML here deliberately - credibility is better handled as an explicit,
auditable whitelist than as something a model "learns," since trustworthiness
of a news source isn't really inferrable from article text itself.

Usage:
    from credibility_scoring import score_credibility
    tier, score = score_credibility("Economic Times")
"""

# Tier 1: highly credible, established financial/business journalism
TIER_1_SOURCES = [
    "reuters", "bloomberg", "economic times", "the economic times",
    "mint", "livemint", "business standard", "financial times",
    "the hindu businessline", "moneycontrol",
]

# Tier 2: legitimate but slightly less rigorous - aggregators, general press
TIER_2_SOURCES = [
    "times of india", "hindustan times", "the indian express", "ndtv",
    "cnbc", "cnbc-tv18", "business today", "forbes india", "yourstory",
    "inc42", "entrackr","businessline", "the hindu businessline", "ani news", "the new indian express","entrepreneur india", "storyboard18", "et healthworld",
]

# Tier 3: everything else - unknown blogs, unverified sources
# Not blocked outright, but ranked/flagged lowest.

CREDIBILITY_SCORES = {
    "tier_1": 1.0,
    "tier_2": 0.7,
    "tier_3": 0.3,
}


def normalize_source(source: str) -> str:
    return str(source).strip().lower()


def score_credibility(source: str) -> dict:
    """
    Returns a dict with the source's tier, numeric score, and reasoning -
    same pattern as Stage 2's passes_stage2(), so every pipeline stage
    is equally auditable/explainable.
    """
    src = normalize_source(source)

    if any(t1 in src for t1 in TIER_1_SOURCES):
        tier = "tier_1"
    elif any(t2 in src for t2 in TIER_2_SOURCES):
        tier = "tier_2"
    else:
        tier = "tier_3"

    return {
        "source": source,
        "tier": tier,
        "score": CREDIBILITY_SCORES[tier],
    }


def filter_by_credibility(articles: list, min_tier: str = "tier_3") -> list:
    """
    Filters a list of article dicts (each with a "source" key) by minimum
    acceptable credibility tier. Default min_tier="tier_3" means nothing
    gets excluded outright - everything just gets scored/ranked. Set
    min_tier="tier_2" to actually drop tier_3 (unverified) sources entirely.
    """
    tier_order = {"tier_1": 3, "tier_2": 2, "tier_3": 1}
    min_rank = tier_order[min_tier]

    scored = []
    for a in articles:
        result = score_credibility(a.get("source", ""))
        if tier_order[result["tier"]] >= min_rank:
            a_copy = dict(a)
            a_copy["credibility_tier"] = result["tier"]
            a_copy["credibility_score"] = result["score"]
            scored.append(a_copy)

    # Sort by credibility score, highest first - most trustworthy sources
    # surface first in the newsletter draft.
    scored.sort(key=lambda x: x["credibility_score"], reverse=True)
    return scored


if __name__ == "__main__":
    test_articles = [
        {"text": "Dabur acquires stake in Fem Care Pharma", "source": "Reuters"},
        {"text": "Godrej Consumer to acquire South African brand", "source": "Mint"},
        {"text": "Nestle India reports Q3 earnings", "source": "Random Blog XYZ"},
        {"text": "Marico expands into Bangladesh", "source": "Inc42"},
    ]

    print("=== All articles, scored and ranked ===")
    result = filter_by_credibility(test_articles, min_tier="tier_3")
    for a in result:
        print(f"  [{a['credibility_tier']} | {a['credibility_score']}] {a['source']}: {a['text']}")

    print("\n=== Only tier_1/tier_2 sources (tier_3 dropped) ===")
    result_filtered = filter_by_credibility(test_articles, min_tier="tier_2")
    for a in result_filtered:
        print(f"  [{a['credibility_tier']} | {a['credibility_score']}] {a['source']}: {a['text']}")