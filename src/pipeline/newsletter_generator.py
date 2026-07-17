"""
newsletter_generator.py

The single LLM call in the entire pipeline. Takes the final, filtered,
deduplicated, credibility-ranked articles and:
  1. Does one last judgment pass - drops anything that isn't a genuine,
     specific FMCG deal (catches what Stage 2's keyword logic can't,
     e.g. "impairment charge" or "conference call transcript" mentioning
     "investment" without an actual transaction).
  2. Writes a short, structured newsletter from what survives.

This is intentionally the ONLY LLM call in production use - everything
upstream (Stage 1, Stage 2, dedup, credibility) is classical ML/rules,
so token usage here is a few thousand tokens per newsletter run, not
per article.
"""

import os
import pandas as pd
from datetime import date
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL_NAME = "gemini-3.5-flash"  # upgraded from flash-lite - still free tier, better synthesis quality
INPUT_CSV = "data/processed/final_articles.csv"
OUTPUT_MD = f"outputs/newsletter_drafts/newsletter_{date.today().isoformat()}.md"

MAX_ARTICLES_TO_LLM = 40  # cap input size - top N by credibility, keeps token usage predictable


def load_final_articles() -> pd.DataFrame:
    df = pd.read_csv(INPUT_CSV)
    df = df.sort_values("credibility_score", ascending=False)
    return df.head(MAX_ARTICLES_TO_LLM)


def build_prompt(articles_df: pd.DataFrame) -> str:
    numbered_articles = "\n".join(
        f"{i+1}. [{articles_df.iloc[i]['source']}] {articles_df.iloc[i]['text']}"
        for i in range(len(articles_df))
    )

    prompt = f"""You are writing a concise FMCG industry newsletter covering recent M&A and investment activity, for a professional audience (analysts, investors, industry watchers).

Below is a list of news headlines that have already been filtered for FMCG relevance. However, some may still not be genuine deals (e.g. earnings commentary, brand rankings, conference call transcripts, accounting charges that mention "investment" without an actual transaction). Your first job is to SILENTLY skip any headline that is not a specific, genuine M&A/acquisition/stake/investment/JV/divestment transaction.

From the genuine deals that remain, write a newsletter with this exact structure:

# FMCG Deal Intelligence Newsletter
### {date.today().strftime('%B %d, %Y')}

## Executive Summary
(2-3 sentences summarizing the overall deal activity theme this period - e.g. which companies are most active, what categories are trending)

## Deals This Period
For each genuine deal, write one entry in plain prose, in this style:
**Company A acquires/invests in Company B or Brand** — one or two sentence description of the deal (value if known, strategic rationale if evident). Source: outlet name.

Do NOT use angle brackets, square brackets, or placeholder-style syntax like <action> or [Company B] in your actual output - write the real company names and real actions directly in plain text.

Group deals by acquiring company if the same company appears multiple times, to avoid repetition.

## Sources
List all outlets cited, once each.

Headlines:
{numbered_articles}

Write ONLY the newsletter in the exact structure above. Do not add commentary about your filtering process."""
    return prompt


def generate_newsletter() -> str:
    articles_df = load_final_articles()
    print(f"Sending {len(articles_df)} articles to LLM for final filtering + newsletter generation...")

    prompt = build_prompt(articles_df)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    newsletter_text = response.text

    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(newsletter_text)

    print(f"\nNewsletter saved to {OUTPUT_MD}")
    return newsletter_text


if __name__ == "__main__":
    newsletter = generate_newsletter()
    print("\n" + "=" * 60)
    print(newsletter)