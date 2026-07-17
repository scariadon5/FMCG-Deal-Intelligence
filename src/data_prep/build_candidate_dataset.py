import pandas as pd
import re

RAW_DIR = "data/raw"
OUT_PATH = "data/processed/candidates.csv"

DEAL_KEYWORDS = [
    "acqui", "merger", "stake", "invest", "funding", "buyout",
    " ipo", "divest", "takeover", "joint venture", "jv ",
]

FMCG_KEYWORDS = [
    "fmcg", "hindustan unilever", " hul ", "nestle", "britannia", "dabur",
    "marico", "colgate", "godrej consumer", " itc ", "p&g", "procter",
    "unilever", "pepsico", "coca-cola", "coca cola", "patanjali", "emami",
    "tata consumer", "varun beverages", "united spirits", "parle", "amul",
    "consumer goods", "packaged food", "personal care", "zandu", "cavinkare",
    "haircode", "balsara",
]

def has_any(text: str, keywords: list) -> bool:
    return any(k in text for k in keywords)


def clean_text(s: str) -> str:
    s = str(s) if s is not None else ""
    s = re.sub(r"\s+", " ", s).strip()
    return s

def build_from_headlines():
    """Stream the large headlines file in chunks; classify into 3 tiers."""
    positives, business_neg, general_neg = [], [], []

    for chunk in pd.read_csv(f"{RAW_DIR}/india-news-headlines.csv", chunksize=500_000):
        chunk["headline_text"] = chunk["headline_text"].fillna("")
        text_lower = chunk["headline_text"].str.lower()
        is_business = chunk["headline_category"].str.contains("business", na=False)

        has_deal = text_lower.apply(lambda t: has_any(t, DEAL_KEYWORDS))
        has_fmcg = text_lower.apply(lambda t: has_any(t, FMCG_KEYWORDS))

        pos_mask = is_business & has_deal & has_fmcg
        biz_neg_mask = is_business & ~pos_mask
        gen_neg_mask = ~is_business

        positives.append(chunk.loc[pos_mask, ["headline_text"]].rename(columns={"headline_text": "text"}))
        business_neg.append(chunk.loc[biz_neg_mask, ["headline_text"]].rename(columns={"headline_text": "text"}))
        general_neg.append(chunk.loc[gen_neg_mask, ["headline_text"]].rename(columns={"headline_text": "text"}))

    pos_df = pd.concat(positives, ignore_index=True)
    biz_df = pd.concat(business_neg, ignore_index=True)
    gen_df = pd.concat(general_neg, ignore_index=True)
    return pos_df, biz_df, gen_df

def build_from_financial_news():
    """Smaller Title+Description dataset - same tiering logic, no category column
    so everything not keyword-matched is treated as a 'business_negative' proxy
    (it's already a financial-news dataset, so it's a reasonable hard negative)."""
    df = pd.read_csv(f"{RAW_DIR}/IndianFinancialNews.csv")
    df["text"] = (df["Title"].fillna("") + " " + df["Description"].fillna("")).apply(clean_text)
    text_lower = df["text"].str.lower()

    has_deal = text_lower.apply(lambda t: has_any(t, DEAL_KEYWORDS))
    has_fmcg = text_lower.apply(lambda t: has_any(t, FMCG_KEYWORDS))
    pos_mask = has_deal & has_fmcg

    pos_df = df.loc[pos_mask, ["text"]]
    neg_df = df.loc[~pos_mask, ["text"]]
    return pos_df, neg_df

def main():
    print("Processing india-news-headlines.csv (this streams ~3.9M rows, may take a minute)...")
    h_pos, h_biz_neg, h_gen_neg = build_from_headlines()

    print("Processing IndianFinancialNews.csv...")
    f_pos, f_neg = build_from_financial_news()

    h_pos["label"] = "fmcg_deal_positive"
    h_pos["tier"] = "keyword_confirmed"
    h_pos["source_dataset"] = "india-headlines"

    f_pos["label"] = "fmcg_deal_positive"
    f_pos["tier"] = "keyword_confirmed"
    f_pos["source_dataset"] = "indian-financial-news"

    h_biz_neg["label"] = "business_negative"
    h_biz_neg["tier"] = "hard_negative"
    h_biz_neg["source_dataset"] = "india-headlines"

    f_neg["label"] = "business_negative"
    f_neg["tier"] = "hard_negative"
    f_neg["source_dataset"] = "indian-financial-news"

    h_gen_neg["label"] = "general_negative"
    h_gen_neg["tier"] = "easy_negative"
    h_gen_neg["source_dataset"] = "india-headlines"

    n_pos = len(h_pos) + len(f_pos)
    hard_neg_sample = h_biz_neg.sample(n=min(len(h_biz_neg), n_pos * 10), random_state=42)
    easy_neg_sample = h_gen_neg.sample(n=min(len(h_gen_neg), n_pos * 10), random_state=42)
    fin_neg_sample = f_neg.sample(n=min(len(f_neg), n_pos * 5), random_state=42)

    final = pd.concat(
        [h_pos, f_pos, hard_neg_sample, easy_neg_sample, fin_neg_sample],
        ignore_index=True,
    )
    final["text"] = final["text"].apply(clean_text)
    final = final.drop_duplicates(subset="text").reset_index(drop=True)

    final.to_csv(OUT_PATH, index=False)

    print("\n=== Candidate dataset summary ===")
    print("Total rows:", len(final))
    print(final["label"].value_counts())
    print(final["tier"].value_counts())
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
