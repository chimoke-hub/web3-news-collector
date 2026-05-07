"""Entry point for WEB3 news collection pipeline."""

import logging
import sys
from datetime import datetime, timedelta, timezone

import pytz

from src.database import get_articles_for_date, init_db, save_articles
from src.markdown_writer import write_markdown
from src.newsapi_collector import collect_newsapi
from src.rss_collector import collect_rss
from src.slack_notifier import send_slack_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

JST = pytz.timezone("Asia/Tokyo")


def main() -> None:
    now_jst = datetime.now(JST)
    logger.info("=== WEB3 News Collector started at %s ===", now_jst.strftime("%Y-%m-%d %H:%M JST"))

    # Collect articles published since yesterday 00:00 JST
    yesterday_jst = now_jst.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    since_utc = yesterday_jst.astimezone(timezone.utc)
    logger.info("Collecting articles since: %s", yesterday_jst.strftime("%Y-%m-%d %H:%M JST"))

    # Initialize database
    init_db()

    # Collect from all sources
    rss_articles = collect_rss(since=since_utc)
    newsapi_articles = collect_newsapi(since=since_utc)

    all_articles = rss_articles + newsapi_articles
    logger.info("Total collected: %d articles", len(all_articles))

    # Save to DB (deduplication handled by UNIQUE constraint on URL)
    inserted, skipped = save_articles(all_articles)
    logger.info("Saved to DB: %d new, %d duplicates skipped", inserted, skipped)

    # Retrieve today's articles for output
    articles_by_category = get_articles_for_date(now_jst)
    domestic_count = len(articles_by_category.get("domestic", []))
    international_count = len(articles_by_category.get("international", []))
    logger.info("Today's articles — 国内: %d, 海外: %d", domestic_count, international_count)

    # Write Markdown file
    md_path = write_markdown(articles_by_category, target_date=now_jst)
    logger.info("Markdown file: %s", md_path)

    # Send Slack notification
    send_slack_notification(articles_by_category, target_date=now_jst)

    logger.info("=== WEB3 News Collector finished ===")


if __name__ == "__main__":
    main()
