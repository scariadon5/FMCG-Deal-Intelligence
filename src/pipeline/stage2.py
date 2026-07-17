"""
stage2_fmcg_keyword_gate.py

Stage 2: Rule-based FMCG-specificity + deal-type gate.
Runs AFTER Stage 1 (ML classifier) in the live pipeline. An article must
pass BOTH stages to be considered relevant for the newsletter.

This module is intentionally simple and auditable - no ML, just explicit
keyword logic - because Stage 1's job is "does this sound financial/deal-like"
while Stage 2's job is "is this specifically about an FMCG company's deal."
Keeping them separate means each stage is easy to debug and explain on its own.
"""

import re

# "Strong" entities = specific, named FMCG companies. If one of these appears
# as the acquiring/investing party, we trust that identity over the sector-exclusion
# check, since coincidental words in a TARGET company's name (e.g. "Fem Care
# Pharma Ltd") shouldn't override a clearly-identified real FMCG acquirer.
STRONG_FMCG_COMPANIES = [
    "hindustan unilever", "hul", "nestle", "britannia", "dabur", "marico",
    "colgate", "godrej consumer", "itc", "p&g", "procter", "unilever",
    "pepsico", "coca-cola", "coca cola", "patanjali", "emami", "tata consumer",
    "varun beverages", "united spirits", "parle", "amul", "diageo", "danone",
    "lavazza", "heineken", "jab holdings", "haldiram", "britvic", "mondelez",
    "kellanova", "reckitt", "beiersdorf", "cavinkare",
]

# Generic sector terms - less certain on their own, so exclusion checks
# still apply if ONLY these matched (not an actual named company).
GENERIC_FMCG_TERMS = [
    "fmcg", "consumer goods", "packaged food", "personal care", "zandu",
]

FMCG_ENTITIES = STRONG_FMCG_COMPANIES + GENERIC_FMCG_TERMS

DEAL_VERBS = [
    "acqui", "merger", "merge", "stake", "invest", "funding", "buyout",
    "ipo", "divest", "takeover", "joint venture", " jv ", "raises",
    "valuation", "backs", "infuse", "sell stake", "sells stake",
]

# Sectors that produce false positives if only checked against DEAL_VERBS
# (mirrors the exclusions we manually discovered while spot-checking labels)
EXCLUDED_SECTOR_HINTS = [
    "ikea", "furniture", "cement", "infrastructure", "wipro technologies",
    "wipro it", "pharma", "hospital", "healthcare", "wellness", "yoga",
    "fitness", "auto", "telecom", "bank", "real estate", "fipb",
    "regulatory approval", "turnover target",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def has_fmcg_entity(text: str) -> bool:
    text = normalize(text)
    return any(entity in text for entity in FMCG_ENTITIES)


def has_strong_fmcg_company(text: str) -> bool:
    text = normalize(text)
    return any(company in text for company in STRONG_FMCG_COMPANIES)


def has_deal_verb(text: str) -> bool:
    text = normalize(text)
    return any(verb in text for verb in DEAL_VERBS)


def has_excluded_sector(text: str) -> bool:
    text = normalize(text)
    return any(hint in text for hint in EXCLUDED_SECTOR_HINTS)


def passes_stage2(text: str) -> dict:
    """
    Returns a dict with the pass/fail decision AND the reasoning,
    so the live pipeline can log *why* an article was kept or dropped -
    important for the "pipeline explanation" deliverable.
    """
    entity_hit = has_fmcg_entity(text)
    deal_hit = has_deal_verb(text)
    excluded = has_excluded_sector(text)
    strong_company = has_strong_fmcg_company(text)

    # If a known, named FMCG company is present, ignore the sector-exclusion
    # check entirely - trust the acquirer's real identity over incidental
    # words in the target's name (e.g. "Fem Care Pharma Ltd").
    if strong_company and deal_hit:
        passed = True
        reason = "passed: named FMCG company + deal verb present (exclusion check bypassed - trusted acquirer identity)"
    else:
        passed = entity_hit and deal_hit and not excluded
        if not entity_hit:
            reason = "no FMCG entity/sector term found"
        elif not deal_hit:
            reason = "FMCG entity found, but no deal-type language found"
        elif excluded:
            reason = "matched generic FMCG term + deal terms, but excluded-sector hint present (likely false positive)"
        else:
            reason = "passed: FMCG entity + deal verb present, no exclusion hints"

    return {
        "passed": passed,
        "reason": reason,
        "entity_hit": entity_hit,
        "deal_hit": deal_hit,
        "excluded_sector_hit": excluded,
        "strong_company_hit": strong_company,
    }


if __name__ == "__main__":
    # Quick manual test against a few known cases from our labeling work
    test_cases = [
        "Dabur acquires 72% stake in Fem Care Pharma Ltd",
        "IKEA to double sourcing from India to 600m euros",
        "General insurers sell ITC stock to hike book value",
        "Godrej Consumer to acquire South African hair brand",
        "Wipro's consumer care div targets Rs 450cr turnover",
    ]
    for t in test_cases:
        result = passes_stage2(t)
        print(f"[{'PASS' if result['passed'] else 'FAIL'}] {t}")
        print(f"    -> {result['reason']}")