import os
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

CANDIDATES_PATH = "data/processed/candidates.csv"
OUTPUT_PATH = "data/labeled/training_data.csv"
MODEL_NAME = "gemini-3.1-flash-lite"
BATCH_SIZE = 25
SAMPLE_SIZE = 2100
def load_sample():
    df = pd.read_csv(OUTPUT_PATH)  # read from training_data.csv, not candidates.csv
    unreviewed = df[(df["label"] == "business_negative") & (df["tier"] != "llm_reviewed_negative")]
    sample = unreviewed.sample(n=min(SAMPLE_SIZE, len(unreviewed)), random_state=42)
    return sample.reset_index(drop=True)
def build_prompt(headlines: list) -> str:
    numbered = "\n".join(f"{i+1}. {h}" for i, h in enumerate(headlines))
    prompt = f"""You are labeling news headlines for a dataset. For each headline below, answer ONLY "yes" or "no": is this headline about an FMCG (fast-moving consumer goods) company's merger, acquisition, stake purchase, investment, funding round, joint venture, or divestment?

FMCG means: packaged food, beverages, personal care, household products, tobacco, confectionery. Examples of FMCG companies: Hindustan Unilever, Nestle, Britannia, Dabur, Marico, Colgate, Godrej Consumer, ITC, P&G, PepsiCo, Coca-Cola, Patanjali, Emami, Tata Consumer, Parle, Amul, Heineken, JAB Holdings, Lavazza.

Answer "no" if ANY of these apply, even if the headline mentions deals, stakes, or investment:
- The company is in a different sector: furniture/retail (IKEA), cement/infrastructure (L&T), IT services (Wipro IT), pharma/healthcare, wellness/fitness services, autos, telecom, banking, real estate
- The company is a large diversified conglomerate (e.g. Reliance, Tata Group, Adani) and the headline does NOT specify the deal is in their FMCG/consumer-goods arm specifically
- No actual transaction is happening - e.g. a turnover target, a regulatory approval to enter a market, a demerger of a NON-FMCG business unit, a general business update
- The FMCG connection requires you to guess or infer something not stated in the headline

Headlines:
{numbered}

Respond with ONLY a numbered list of yes/no answers, one per line, nothing else. Example format:
1. no
2. yes
3. no"""
    return prompt
def label_batch(headlines: list, retries: int = 5) -> list:
    prompt = build_prompt(headlines)
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            return parse_response(response.text, len(headlines))
        except Exception as e:
            error_str = str(e)
            if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                wait_time = 65  # safely clear the 60-second rate-limit window
                print(f"  Attempt {attempt+1} rate-limited. Waiting {wait_time}s...")
            else:
                wait_time = 5 * (attempt + 1)
                print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(wait_time)
    return ["no"] * len(headlines)
def parse_response(text: str, expected_count: int) -> list:
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    answers = []
    for line in lines:
        line_lower = line.lower()
        if "yes" in line_lower:
            answers.append("yes")
        elif "no" in line_lower:
            answers.append("no")

    if len(answers) != expected_count:
        print(f"  Warning: expected {expected_count} answers, got {len(answers)}. Padding with 'no'.")
        while len(answers) < expected_count:
            answers.append("no")
        answers = answers[:expected_count]

    return answers
def main():
    sample = load_sample()
    headlines = sample["text"].tolist()

    all_answers = []
    for i in range(0, len(headlines), BATCH_SIZE):
        batch = headlines[i:i + BATCH_SIZE]
        print(f"Labeling batch {i // BATCH_SIZE + 1} / {-(-len(headlines) // BATCH_SIZE)} ({len(batch)} headlines)...")
        answers = label_batch(batch)
        all_answers.extend(answers)
        time.sleep(5)

    sample["llm_label"] = all_answers

    newly_confirmed = sample[sample["llm_label"] == "yes"].copy()
    newly_confirmed["label"] = "fmcg_deal_positive"
    newly_confirmed["tier"] = "llm_confirmed"

    still_negative = sample[sample["llm_label"] == "no"].copy()
    still_negative["tier"] = "llm_reviewed_negative"  # now correctly tagged as reviewed

    full = pd.read_csv(OUTPUT_PATH)
    untouched = full[~full["text"].isin(sample["text"])]

    final = pd.concat(
        [
            untouched,
            newly_confirmed[["text", "label", "tier", "source_dataset"]],
            still_negative[["text", "label", "tier", "source_dataset"]],
        ],
        ignore_index=True,
    )

    final.to_csv(OUTPUT_PATH, index=False)

    print("\n=== Labeling complete ===")
    print(f"Sampled {len(sample)} unreviewed rows for LLM review")
    print(f"Newly confirmed as FMCG-deal positive: {len(newly_confirmed)}")
    print(f"Final label distribution:\n{final['label'].value_counts()}")
    print(f"Final tier distribution:\n{final['tier'].value_counts()}")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()