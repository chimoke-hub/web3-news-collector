"""Slack Block Kit notifier for daily WEB3 news summary."""

import logging
import os
from datetime import datetime

import pytz
import requests

logger = logging.getLogger(__name__)

JST = pytz.timezone("Asia/Tokyo")
MAX_ARTICLES_PER_SECTION = 10  # Slack message size limit


def _article_line(article: dict) -> str:
    title = article.get("title", "（タイトルなし）")
    url = article.get("url", "")
    source = article.get("source", "不明")
    return f"• <{url}|{title}> _{source}_"


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
                "text": f"*国内*: {len(domestic)}件  |  *海外*: {len(international)}件",
            },
        },
        {"type": "divider"},
    ]

    # Domestic section
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f":jp: *国内ニュース ({len(domestic)}件)*",
        },
    })

    if domestic:
        displayed = domestic[:MAX_ARTICLES_PER_SECTION]
        text_lines = [_article_line(a) for a in displayed]
        if len(domestic) > MAX_ARTICLES_PER_SECTION:
            text_lines.append(f"_...他 {len(domestic) - MAX_ARTICLES_PER_SECTION} 件_")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(text_lines),
            },
        })
    else:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "_本日の国内ニュースはありませんでした。_"},
        })

    blocks.append({"type": "divider"})

    # International section
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f":globe_with_meridians: *海外ニュース ({len(international)}件)*",
        },
    })

    if international:
        displayed = international[:MAX_ARTICLES_PER_SECTION]
        text_lines = [_article_line(a) for a in displayed]
        if len(international) > MAX_ARTICLES_PER_SECTION:
            text_lines.append(f"_...他 {len(international) - MAX_ARTICLES_PER_SECTION} 件_")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(text_lines),
            },
        })
    else:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "_本日の海外ニュースはありませんでした。_"},
        })

    blocks.append({"type": "divider"})
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
