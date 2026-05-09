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
    summary      TEXT,
    title_ja     TEXT,
    summary_ja   TEXT
);
"""

# Columns added after initial release — migrate existing DBs gracefully
MIGRATION_SQLS = [
    "ALTER TABLE articles ADD COLUMN title_ja TEXT",
    "ALTER TABLE articles ADD COLUMN summary_ja TEXT",
]


def _get_conn(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Create the articles table if it doesn't exist, and run migrations."""
    with _get_conn(db_path) as conn:
        conn.execute(CREATE_TABLE_SQL)
        # Add new columns to existing DBs (ignore error if already present)
        for sql in MIGRATION_SQLS:
            try:
                conn.execute(sql)
            except sqlite3.OperationalError:
                pass
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
                    INSERT INTO articles (title, url, source, category, language, published_at, summary, title_ja, summary_ja)
                    VALUES (:title, :url, :source, :category, :language, :published_at, :summary, :title_ja, :summary_ja)
                    """,
                    {
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "source": article.get("source", ""),
                        "category": article.get("category", ""),
                        "language": article.get("language", ""),
                        "published_at": published_at,
                        "summary": article.get("summary", ""),
                        "title_ja": article.get("title_ja", ""),
                        "summary_ja": article.get("summary_ja", ""),
                    },
                )
                inserted += 1
            except sqlite3.IntegrityError:
                # 重複URL — 翻訳だけ更新する
                title_ja = article.get("title_ja", "")
                summary_ja = article.get("summary_ja", "")
                if title_ja or summary_ja:
                    conn.execute(
                        """
                        UPDATE articles
                        SET title_ja = :title_ja, summary_ja = :summary_ja
                        WHERE url = :url AND (title_ja IS NULL OR title_ja = '')
                        """,
                        {"url": article.get("url", ""), "title_ja": title_ja, "summary_ja": summary_ja},
                    )
                skipped += 1

        conn.commit()

    logger.info("DB save: %d inserted, %d skipped", inserted, skipped)
    return inserted, skipped


def get_translated_urls(urls: list[str], db_path: Path | None = None) -> set[str]:
    """Return the subset of URLs that already have a title_ja translation in the DB."""
    if not urls:
        return set()
    placeholders = ",".join("?" * len(urls))
    with _get_conn(db_path) as conn:
        rows = conn.execute(
            f"SELECT url FROM articles WHERE url IN ({placeholders}) AND title_ja IS NOT NULL AND title_ja != ''",
            urls,
        ).fetchall()
    return {row["url"] for row in rows}


def get_articles_for_date(since: datetime, db_path: Path | None = None) -> dict[str, list[dict]]:
    """
    Fetch articles published on or after `since` (UTC), grouped by category.
    Returns {"domestic": [...], "international": [...]}.
    """
    since_str = since.strftime("%Y-%m-%d %H:%M:%S")

    with _get_conn(db_path) as conn:
        rows = conn.execute(
            """
            SELECT title, url, source, category, language, published_at, summary, title_ja, summary_ja
            FROM articles
            WHERE published_at >= ?
            ORDER BY category, published_at DESC
            """,
            (since_str,),
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
