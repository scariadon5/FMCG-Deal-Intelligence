"""
ingest_live_news.py

Real-time news ingestion via Google News RSS - no API key, no LLM tokens
used here at all. Pure HTTP fetch + XML parsing.
"""

import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time

SEARCH_QUERIES = [
    "FMCG acquisition India",
    "FMCG merger stake investment",
    "Hindustan Unilever acquisition",
    "Nestle India investment stake",
    "Dabur acquisition stake",
    "Marico acquisition investment",
    "ITC FMCG stake acquisition",
    "Godrej Consumer acquisition",
    "Britannia investment stake",
    "Tata Consumer acquisition",
]

RSS_BASE_URL = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


def fetch_rss(query: str) -> list:
    """Fetch and parse one Google News RSS query into a list of article dicts."""
    url = RSS_BASE_URL.format(query=quote(query))
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Failed to fetch '{query}': {e}")
        return []

    articles = []
    try:
        root = ET.fromstring(response.content)
        for item in root.findall(".//item"):
            raw_title = item.findtext("title", default="")
            link = item.findtext("link", default="")
            pub_date = item.findtext("pubDate", default="")
            source_elem = item.find("source")
            source = source_elem.text if source_elem is not None else "Unknown"
            description = item.findtext("description", default="")

            # Google News appends " - SourceName" to every title; strip it
            # since we already capture source separately in its own field.
            if source_elem is not None and source_elem.text:
                title = raw_title.replace(f" - {source_elem.text}", "").strip()
            else:
                title = raw_title

            articles.append({
                "title": title,
                "text": title,
                "link": link,
                "pub_date": pub_date,
                "source": source,
                "search_query": query,
            })
    except ET.ParseError as e:
        print(f"  Failed to parse XML for '{query}': {e}")

    return articles


def ingest_all() -> list:
    """Run all search queries, combine results, remove exact-duplicate links."""
    all_articles = []
    seen_links = set()

    for query in SEARCH_QUERIES:
        print(f"Fetching: {query}")
        results = fetch_rss(query)
        for article in results:
            if article["link"] not in seen_links:
                seen_links.add(article["link"])
                all_articles.append(article)
        time.sleep(1)

    print(f"\nTotal unique articles fetched: {len(all_articles)}")
    return all_articles


if __name__ == "__main__":
    articles = ingest_all()
    for a in articles[:10]:
        print(f"\n[{a['source']}] {a['title']}")
        print(f"  {a['link']}")