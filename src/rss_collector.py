"""RSS feed collector for WEB3 news sources."""

import feedparser
import logging
from datetime import datetime, timezone
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

DOMESTIC_FEEDS = [
    {
        "name": "CoinPost",
        "url": "https://coinpost.jp/?feed=rss2",
        "category": "domestic",
        "language": "ja",
    },
    {
        "name": "CoinDesk Japan",
        "url": "https://www.coindeskjapan.com/feed/",
        "category": "domestic",
        "language": "ja",
    },
    {
        "name": "あたらしい経済",
        "url": "https://www.neweconomy.jp/feed",
        "category": "domestic",
        "language": "ja",
    },
]

INTERNATIONAL_FEEDS = [
    {
        "name": "CoinDesk",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "category": "international",
        "language": "en",
    },
    {
        "name": "Cointelegraph",
        "url": "https://cointelegraph.com/rss",
        "category": "international",
        "language": "en",
    },
    {
        "name": "Decrypt",
        "url": "https://decrypt.co/feed",
        "category": "international",
        "language": "en",
    },
    {
        "name": "The Block",
        "url": "https://www.theblock.co/rss.xml",
        "category": "international",
        "language": "en",
    },
]


def _parse_date(entry) -> datetime | None:
    """Parse published date from feed entry, returning UTC datetime."""
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            return datetime(*val[:6], tzinfo=timezone.utc)

    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            try:
                dt = dateutil_parser.parse(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass

    return None


def _get_summary(entry) -> str:
    """Extract plain-text summary from entry (truncated to 200 chars)."""
    raw = getattr(entry, "summary", "") or ""
    # Strip basic HTML tags
    import re
    text = re.sub(r"<[^>]+>", "", raw).strip()
    return text[:200] if text else ""


def collect_rss(since: datetime) -> list[dict]:
    """
    Collect articles from all RSS feeds published on or after `since` (UTC).
    Returns a list of article dicts.
    """
    articles = []

    for feed_info in DOMESTIC_FEEDS + INTERNATIONAL_FEEDS:
        logger.info("Fetching RSS: %s (%s)", feed_info["name"], feed_info["url"])
        try:
            feed = feedparser.parse(feed_info["url"], agent="web3-news-collector/1.0")
            if feed.bozo and not feed.entries:
                logger.warning("Feed parse error for %s: %s", feed_info["name"], feed.bozo_exception)
                continue

            for entry in feed.entries:
                published_at = _parse_date(entry)

                # Skip if we can't determine publish date
                if published_at is None:
                    logger.debug("No date for entry: %s", getattr(entry, "title", ""))
                    continue

                # Filter by date
                if published_at < since:
                    continue

                url = getattr(entry, "link", "")
                if not url:
                    continue

                articles.append({
                    "title": getattr(entry, "title", "").strip(),
                    "url": url.strip(),
                    "source": feed_info["name"],
                    "category": feed_info["category"],
                    "language": feed_info["language"],
                    "published_at": published_at,
                    "summary": _get_summary(entry),
                })

        except Exception as e:
            logger.error("Failed to fetch RSS %s: %s", feed_info["name"], e)

    logger.info("RSS collection done: %d articles", len(articles))
    return articles
