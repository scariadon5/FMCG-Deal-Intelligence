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
import re
import pandas as pd
from datetime import date
from dotenv import load_dotenv
from google import genai
from email.utils import parsedate_to_datetime

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL_NAME = "gemini-3.5-flash"  # free-tier model, chosen for synthesis quality
INPUT_CSV = "data/processed/final_articles.csv"
OUTPUT_MD = f"outputs/newsletter_drafts/newsletter_{date.today().isoformat()}.md"

MAX_ARTICLES_TO_LLM = 40  # cap input size - top N by credibility, keeps token usage predictable


def _format_date(raw):
    """Parse an RFC-822 pub_date into 'Mon DD, YYYY'; returns None if unparseable."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        return parsedate_to_datetime(raw).strftime("%b %d, %Y")
    except (TypeError, ValueError):
        return None


def load_final_articles() -> pd.DataFrame:
    df = pd.read_csv(INPUT_CSV)
    df = df.sort_values("credibility_score", ascending=False)
    return df.head(MAX_ARTICLES_TO_LLM)


def build_prompt(articles_df: pd.DataFrame) -> str:
    articles_df = articles_df.reset_index(drop=True)

    numbered_articles = "\n".join(
        f"{i+1}. [{articles_df.iloc[i]['source']}] {articles_df.iloc[i]['text']}"
        for i in range(len(articles_df))
    )

    # Computed here, not by the LLM, so the claimed coverage window is always
    # factually accurate rather than an LLM guess.
    parsed_dates = [
        _format_date(d) for d in articles_df.get("pub_date", []) if _format_date(d)
    ]
    if parsed_dates:
        # Re-parse to sort properly (string sort on "Mon DD, YYYY" isn't chronological)
        real_dates = sorted(
            (parsedate_to_datetime(d) for d in articles_df["pub_date"] if _format_date(d)),
        )
        date_range_line = (
            f"*Covering deals published {real_dates[0].strftime('%b %d, %Y')} "
            f"– {real_dates[-1].strftime('%b %d, %Y')}*"
        )
    else:
        date_range_line = ""

    prompt = f"""You are writing a concise FMCG industry newsletter covering recent M&A and investment activity, for a professional audience (analysts, investors, industry watchers).

Below is a numbered list of news headlines that have already been filtered for FMCG relevance and recency. However, some may still not be genuine deals (e.g. earnings commentary, brand rankings, conference call transcripts, accounting charges that mention "investment" without an actual transaction). Your first job is to SILENTLY skip any headline that is not a specific, genuine M&A/acquisition/stake/investment/JV/divestment transaction.

From the genuine deals that remain, write a newsletter with this exact structure:

# FMCG Deal Intelligence Newsletter
### {date.today().strftime('%B %d, %Y')}
{date_range_line}

## Executive Summary
(2-3 sentences summarizing the overall deal activity theme this period - e.g. which companies are most active, what categories are trending)

## Deals This Period
Group deals by acquiring company. For each company, write a subheading using
### Company Name
followed by a markdown bullet list of that company's deals. Each deal is exactly ONE bullet point, in this style:

- **Company A acquires/invests in Company B or Brand** — one or two sentence description of the deal (value if known, strategic rationale if evident). Source: [3]

CRITICAL citation rule: cite sources using ONLY the bracketed reference number(s) from the numbered Headlines list below — for example [3]. Do NOT write outlet names, URLs, or dates yourself anywhere in the Source line; only the bracketed number(s). If a single deal is supported by more than one headline, cite each as its own separate bracket, e.g.: Source: [3][7]. These bracket numbers will be automatically converted into proper linked source citations afterward — this is the ONLY acceptable citation format.

Every deal MUST be its own bullet line starting with "- " at the start of the line. Do NOT combine multiple deals into one paragraph and do NOT separate deals with asterisks in the middle of a sentence — each deal gets its own bullet, on its own line, under its company's ### subheading.

Do NOT use angle brackets or placeholder-style syntax like <action> or [Company B] in your actual output (other than the required bracketed reference numbers) - write the real company names and real actions directly in plain text.

## Sources
List the reference numbers (in brackets, e.g. [3]) of every headline you actually cited above, once each, in a single line, space-separated.

Headlines:
{numbered_articles}

Write ONLY the newsletter in the exact structure above. Do not add commentary about your filtering process."""
    return prompt


def resolve_citations(newsletter_text: str, articles_df: pd.DataFrame) -> str:
    """
    Replaces every [N] reference number the LLM wrote with a real markdown
    link built directly from articles_df - source name, exact URL, and date.
    This is done in Python specifically because these Google News URLs are
    ~300-character opaque tokens; asking an LLM to reproduce one verbatim
    is fragile and can silently corrupt a link. Citing by reference number
    instead means the LLM never has to touch a raw URL at all.
    """
    df = articles_df.reset_index(drop=True)

    def _replace(match):
        idx = int(match.group(1)) - 1
        if idx < 0 or idx >= len(df):
            return match.group(0)  # out-of-range ref - leave untouched rather than guess
        row = df.iloc[idx]
        source = row.get("source", "Unknown source")
        url = row.get("link", "")
        date_str = _format_date(row.get("pub_date"))
        date_part = f" · {date_str}" if date_str else ""
        if not url:
            return f"{source}{date_part}"
        return f"[{source}]({url}){date_part}"

    return re.sub(r"\[(\d+)\]", _replace, newsletter_text)


def generate_newsletter() -> str:
    articles_df = load_final_articles()
    print(f"Sending {len(articles_df)} articles to LLM for final filtering + newsletter generation...")

    prompt = build_prompt(articles_df)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    newsletter_text = response.text
    newsletter_text = resolve_citations(newsletter_text, articles_df)

    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(newsletter_text)

    print(f"\nNewsletter saved to {OUTPUT_MD}")
    return newsletter_text


if __name__ == "__main__":
    newsletter = generate_newsletter()
    print("\n" + "=" * 60)
    print(newsletter)