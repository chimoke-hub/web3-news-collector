"""Slack Block Kit notifier for daily WEB3 news summary."""

import logging
import os
from datetime import datetime, timezone

import pytz
import requests
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

JST = pytz.timezone("Asia/Tokyo")
MAX_ARTICLES_PER_SECTION = 5  # 詳細表示するため件数を絞る


CATEGORY_LABEL = {"domestic": "国内", "international": "海外"}


def _format_jst(dt_str: str | None) -> str:
    if not dt_str:
        return "不明"
    try:
        dt = dateutil_parser.parse(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(JST).strftime("%Y-%m-%d %H:%M JST")
    except Exception:
        return dt_str


def _article_block(article: dict) -> dict:
    """1記事分のSection Blockを生成する。"""
    title = article.get("title", "（タイトルなし）")
    url = article.get("url", "")
    source = article.get("source", "不明")
    category = CATEGORY_LABEL.get(article.get("category", ""), article.get("category", ""))
    published = _format_jst(article.get("published_at"))
    summary = article.get("summary", "")
    title_ja = article.get("title_ja", "")
    summary_ja = article.get("summary_ja", "")

    lines = [f"*<{url}|{title}>*"]
    if title_ja and title_ja != title:
        lines.append(f"_{title_ja}_")
    lines.append(f":office: *ソース*: {source}　|　:label: *カテゴリ*: {category}　|　:calendar: *公開日*: {published}")
    if summary_ja and summary_ja != summary:
        lines.append(f":memo: *概要*: {summary_ja[:150]}")
    elif summary:
        lines.append(f":memo: *概要*: {summary[:150]}")

    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "\n".join(lines)},
    }


def _build_section_blocks(articles: list[dict], header_text: str) -> list[dict]:
    """カテゴリセクションのブロック一覧を生成する。"""
    blocks: list[dict] = [
        {"type": "section", "text": {"type": "mrkdwn", "text": header_text}},
    ]

    if not articles:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "_本日のニュースはありませんでした。_"},
        })
        return blocks

    displayed = articles[:MAX_ARTICLES_PER_SECTION]
    for article in displayed:
        blocks.append(_article_block(article))
        blocks.append({"type": "divider"})

    remaining = len(articles) - MAX_ARTICLES_PER_SECTION
    if remaining > 0:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"_...他 {remaining} 件（Markdownファイルで全件確認できます）_"}],
        })

    return blocks


def _build_blocks(
    articles_by_category: dict[str, list[dict]],
    target_date: datetime,
) -> list[dict]:
    date_str = target_date.strftime("%Y-%m-%d")
    domestic = articles_by_category.get("domestic", [])
    international = articles_by_category.get("international", [])

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f":newspaper: WEB3ニュース {date_str}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*国内*: {len(domestic)}件  |  *海外*: {len(international)}件\n上位{MAX_ARTICLES_PER_SECTION}件を表示しています。",
            },
        },
        {"type": "divider"},
    ]

    blocks += _build_section_blocks(domestic, f":jp: *国内ニュース ({len(domestic)}件)*")
    blocks.append({"type": "divider"})
    blocks += _build_section_blocks(international, f":globe_with_meridians: *海外ニュース ({len(international)}件)*")

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"収集完了: {datetime.now(JST).strftime('%Y-%m-%d %H:%M JST')} | WEB3 News Collector",
            }
        ],
    })

    return blocks


def send_slack_notification(
    articles_by_category: dict[str, list[dict]],
    target_date: datetime,
    webhook_url: str | None = None,
) -> bool:
    """
    Send a Slack Block Kit message with the daily news summary.
    Returns True on success, False on failure.
    """
    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL", "")
    if not url:
        logger.warning("SLACK_WEBHOOK_URL not set, skipping Slack notification")
        return False

    blocks = _build_blocks(articles_by_category, target_date)
    domestic = articles_by_category.get("domestic", [])
    international = articles_by_category.get("international", [])

    payload = {
        "text": f"WEB3ニュース {target_date.strftime('%Y-%m-%d')} — 国内{len(domestic)}件・海外{len(international)}件",
        "blocks": blocks,
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        logger.info("Slack notification sent successfully")
        return True
    except requests.RequestException as e:
        logger.error("Failed to send Slack notification: %s", e)
        return False
