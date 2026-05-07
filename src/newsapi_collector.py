"""NewsAPI collector for WEB3 news (Japanese and English)."""

import logging
import os
from datetime import datetime, timezone

import requests
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

WEB3_KEYWORDS = "web3 OR blockchain OR crypto OR cryptocurrency OR DeFi OR NFT OR Bitcoin OR Ethereum"

QUERIES = [
    {
        "q": WEB3_KEYWORDS,
        "language": "ja",
        "category": "domestic",
    },
    {
        "q": WEB3_KEYWORDS,
        "language": "en",
        "category": "international",
    },
]


def _parse_iso(date_str: str) -> datetime | None:
    try:
        dt = dateutil_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def collect_newsapi(since: datetime, api_key: str | None = None) -> list[dict]:
    """
    Collect articles from NewsAPI published on or after `since` (UTC).
    Returns a list of article dicts.
    """
    if api_key is None:
        api_key = os.environ.get("NEWS_API_KEY", "")

    if not api_key:
        logger.warning("NEWS_API_KEY not set, skipping NewsAPI collection")
        return []

    # NewsAPI expects ISO 8601 date string
    from_date = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    articles = []

    for query_info in QUERIES:
        logger.info("Fetching NewsAPI lang=%s", query_info["language"])
        params = {
            "q": query_info["q"],
            "language": query_info["language"],
            "from": from_date,
            "sortBy": "publishedAt",
            "pageSize": 100,
            "apiKey": api_key,
        }

        try:
            response = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                logger.error("NewsAPI error: %s", data.get("message", "unknown"))
                continue

            for item in data.get("articles", []):
                url = (item.get("url") or "").strip()
                if not url or url == "https://removed.com":
                    continue

                published_at = _parse_iso(item.get("publishedAt", ""))
                if published_at is None or published_at < since:
                    continue

                source_name = (item.get("source") or {}).get("name", "NewsAPI")
                title = (item.get("title") or "").strip()
                description = (item.get("description") or "").strip()

                if not title or not url:
                    continue

                articles.append({
                    "title": title,
                    "url": url,
                    "source": source_name,
                    "category": query_info["category"],
                    "language": query_info["language"],
                    "published_at": published_at,
                    "summary": description[:200],
                })

        except requests.RequestException as e:
            logger.error("NewsAPI request failed (lang=%s): %s", query_info["language"], e)

    logger.info("NewsAPI collection done: %d articles", len(articles))
    return articles
