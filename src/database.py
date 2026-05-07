"""SQLite database operations for WEB3 news articles."""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "news.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    url          TEXT UNIQUE NOT NULL,
    source       TEXT,
    category     TEXT,
    language     TEXT,
    published_at DATETIME,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    summary      TEXT
);
"""


def _get_conn(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Create the articles table if it doesn't exist."""
    with _get_conn(db_path) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
    logger.info("Database initialized at %s", db_path or DB_PATH)


def save_articles(articles: list[dict], db_path: Path | None = None) -> tuple[int, int]:
    """
    Insert articles, skipping duplicates by URL.
    Returns (inserted_count, skipped_count).
    """
    inserted = 0
    skipped = 0

    with _get_conn(db_path) as conn:
        for article in articles:
            published_at = article.get("published_at")
            if isinstance(published_at, datetime):
                published_at = published_at.strftime("%Y-%m-%d %H:%M:%S")

            try:
                conn.execute(
                    """
                    INSERT INTO articles (title, url, source, category, language, published_at, summary)
                    VALUES (:title, :url, :source, :category, :language, :published_at, :summary)
                    """,
                    {
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "source": article.get("source", ""),
                        "category": article.get("category", ""),
                        "language": article.get("language", ""),
                        "published_at": published_at,
                        "summary": article.get("summary", ""),
                    },
                )
                inserted += 1
            except sqlite3.IntegrityError:
                # Duplicate URL
                skipped += 1

        conn.commit()

    logger.info("DB save: %d inserted, %d skipped", inserted, skipped)
    return inserted, skipped


def get_articles_for_date(target_date: datetime, db_path: Path | None = None) -> dict[str, list[dict]]:
    """
    Fetch articles collected today (by collected_at date), grouped by category.
    Returns {"domestic": [...], "international": [...]}.
    """
    date_str = target_date.strftime("%Y-%m-%d")

    with _get_conn(db_path) as conn:
        rows = conn.execute(
            """
            SELECT title, url, source, category, language, published_at, summary
            FROM articles
            WHERE DATE(collected_at) = ?
            ORDER BY category, published_at DESC
            """,
            (date_str,),
        ).fetchall()

    result: dict[str, list[dict]] = {"domestic": [], "international": []}
    for row in rows:
        article = dict(row)
        cat = article.get("category", "international")
        if cat in result:
            result[cat].append(article)
        else:
            result["international"].append(article)

    return result
