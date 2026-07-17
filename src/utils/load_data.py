import os
import pandas as pd

FINAL_ARTICLES_CSV = "data/processed/final_articles.csv"
NEWSLETTER_DIR = "outputs/newsletter_drafts"


def load_final_articles():
    """
    Load the processed articles CSV.
    """
    if os.path.exists(FINAL_ARTICLES_CSV):
        return pd.read_csv(FINAL_ARTICLES_CSV)

    return pd.DataFrame()


def get_latest_newsletter():
    """
    Load the latest generated newsletter markdown file.
    Returns:
        (filename, content)
    """
    if not os.path.exists(NEWSLETTER_DIR):
        return None, None

    files = [f for f in os.listdir(NEWSLETTER_DIR) if f.endswith(".md")]

    if not files:
        return None, None

    files.sort(reverse=True)

    latest_file = files[0]

    with open(
        os.path.join(NEWSLETTER_DIR, latest_file),
        "r",
        encoding="utf-8",
    ) as f:
        content = f.read()

    return latest_file, content