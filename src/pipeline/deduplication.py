"""
deduplication.py

Removes duplicate/near-duplicate articles from a batch of scraped news.
Live news commonly has the same deal story covered by multiple outlets
(Reuters, ET, Mint) with slightly different wording - this catches those
near-duplicates using TF-IDF + cosine similarity, not exact string matching.

Usage:
    from deduplication import deduplicate_articles
    unique_articles = deduplicate_articles(list_of_article_dicts)
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SIMILARITY_THRESHOLD = 0.45  # articles above this cosine similarity are treated as near-duplicates


def normalize(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def deduplicate_articles(articles: list) -> list:
    """
    articles: list of dicts, each expected to have at least a "text" key
              (title + description/snippet combined).
    Returns: a filtered list with near-duplicates removed, keeping the
             longest (most complete) article per duplicate cluster.
    """
    if len(articles) <= 1:
        return articles

    texts = [normalize(a.get("text", "")) for a in articles]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=3000)
    tfidf_matrix = vectorizer.fit_transform(texts)

    similarity_matrix = cosine_similarity(tfidf_matrix)

    n = len(articles)
    visited = [False] * n
    clusters = []

    # Group articles into clusters of near-duplicates.
    # Simple approach: for each unvisited article, gather everything
    # similar enough to it into one cluster, mark them visited, repeat.
    for i in range(n):
        if visited[i]:
            continue
        cluster = [i]
        visited[i] = True
        for j in range(i + 1, n):
            if not visited[j] and similarity_matrix[i][j] >= SIMILARITY_THRESHOLD:
                cluster.append(j)
                visited[j] = True
        clusters.append(cluster)

    # From each cluster, keep the article with the longest text
    # (a simple, defensible proxy for "most complete source article").
    deduplicated = []
    for cluster in clusters:
        best_idx = max(cluster, key=lambda idx: len(texts[idx]))
        deduplicated.append(articles[best_idx])

    return deduplicated


if __name__ == "__main__":
    # Quick manual test: 4 articles, where 1-2 are near-duplicates of each other
    test_articles = [
        {"text": "Dabur acquires 72% stake in Fem Care Pharma Ltd for undisclosed sum", "source": "Reuters"},
        {"text": "Dabur buys a 72 percent stake in Fem Care Pharma", "source": "Economic Times"},
        {"text": "Godrej Consumer to acquire South African hair care brand", "source": "Mint"},
        {"text": "Nestle India reports Q3 earnings, revenue up 8%", "source": "Business Standard"},
    ]

    result = deduplicate_articles(test_articles)
    print(f"Input: {len(test_articles)} articles -> Output: {len(result)} unique articles")
    for a in result:
        print(f"  [{a['source']}] {a['text']}")