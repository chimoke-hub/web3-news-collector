"""Markdown file generator for daily WEB3 news."""

import logging
from datetime import datetime, timezone
from pathlib import Path

import pytz

logger = logging.getLogger(__name__)

JST = pytz.timezone("Asia/Tokyo")
DATA_DIR = Path(__file__).parent.parent / "data"


def _format_jst(dt_str: str | None) -> str:
    """Convert a datetime string (UTC) to JST formatted string."""
    if not dt_str:
        return "不明"
    try:
        from dateutil import parser as dateutil_parser
        dt = dateutil_parser.parse(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_jst = dt.astimezone(JST)
        return dt_jst.strftime("%Y-%m-%d %H:%M JST")
    except Exception:
        return dt_str


def _render_articles(articles: list[dict]) -> str:
    lines = []
    for i, article in enumerate(articles, 1):
        title = article.get("title", "（タイトルなし）")
        url = article.get("url", "")
        source = article.get("source", "不明")
        published_at = _format_jst(article.get("published_at"))
        summary = article.get("summary", "")

        lines.append(f"### {i}. [{title}]({url})")
        lines.append(f"- **メディア**: {source}")
        lines.append(f"- **公開日時**: {published_at}")
        if summary:
            lines.append(f"- **概要**: {summary}")
        lines.append("")

    return "\n".join(lines)


def write_markdown(
    articles_by_category: dict[str, list[dict]],
    target_date: datetime,
    output_dir: Path | None = None,
) -> Path:
    """
    Write a daily Markdown file and return its path.
    `target_date` should be the collection date (JST).
    """
    out_dir = output_dir or DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = target_date.strftime("%Y-%m-%d")
    filepath = out_dir / f"{date_str}.md"

    domestic = articles_by_category.get("domestic", [])
    international = articles_by_category.get("international", [])

    lines = [
        f"# WEB3ニュース {date_str}",
        "",
        f"> 収集日時: {datetime.now(JST).strftime('%Y-%m-%d %H:%M JST')}  ",
        f"> 国内: {len(domestic)}件 / 海外: {len(international)}件",
        "",
        "---",
        "",
        "## 国内ニュース",
        "",
    ]

    if domestic:
        lines.append(_render_articles(domestic))
    else:
        lines.append("*本日の国内ニュースはありませんでした。*\n")

    lines += [
        "---",
        "",
        "## 海外ニュース",
        "",
    ]

    if international:
        lines.append(_render_articles(international))
    else:
        lines.append("*本日の海外ニュースはありませんでした。*\n")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Markdown written: %s", filepath)
    return filepath
