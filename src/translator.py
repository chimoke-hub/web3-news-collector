"""Google Translate module for international WEB3 news articles (via deep-translator)."""

import logging
import time

logger = logging.getLogger(__name__)

REQUEST_INTERVAL = 0.5   # リクエスト間隔（秒）
RETRY_LIMIT = 3          # 失敗時のリトライ回数
RETRY_WAIT = 15.0        # リトライ前のウェイト（秒）


def translate_articles(articles: list[dict]) -> list[dict]:
    """
    Translate title and summary of international (English) articles into Japanese.
    Adds `title_ja` and `summary_ja` keys to each article dict in-place.
    Returns the same list.
    """
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        logger.error("deep-translator package not installed")
        for article in articles:
            article.setdefault("title_ja", "")
            article.setdefault("summary_ja", "")
        return articles

    total = len(articles)
    logger.info("Translating %d international articles (titles + summaries)...", total)

    for i, article in enumerate(articles):
        title = article.get("title", "") or ""
        summary = article.get("summary", "") or ""

        article["title_ja"] = _translate_one(title, i * 2, total * 2) if title.strip() else ""
        article["summary_ja"] = _translate_one(summary, i * 2 + 1, total * 2) if summary.strip() else ""

        if (i + 1) % 50 == 0:
            logger.info("Progress: %d/%d articles translated", i + 1, total)

    logger.info("Translation complete: %d articles", total)
    return articles


def _translate_one(text: str, request_index: int, total_requests: int) -> str:
    """
    1テキストを翻訳して返す。失敗時はリトライし、それでも失敗したら空文字を返す。
    リクエスト間にREQUEST_INTERVALの待機を入れてレート制限を回避する。
    """
    from deep_translator import GoogleTranslator

    text_truncated = text[:4500]

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            result = GoogleTranslator(source="en", target="ja").translate(text_truncated)
            time.sleep(REQUEST_INTERVAL)
            return result or ""
        except Exception as e:
            logger.warning(
                "Translation failed [%d/%d] attempt %d/%d: %s",
                request_index + 1, total_requests, attempt, RETRY_LIMIT, e,
            )
            if attempt < RETRY_LIMIT:
                time.sleep(RETRY_WAIT * attempt)  # 指数バックオフ: 15s, 30s
            else:
                time.sleep(REQUEST_INTERVAL)

    return ""
