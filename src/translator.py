"""Google Translate module for international WEB3 news articles (via deep-translator)."""

import logging
import time

logger = logging.getLogger(__name__)

BATCH_SIZE = 10      # 1回のリクエストで翻訳する件数
REQUEST_DELAY = 1.0  # リクエスト間のウェイト（秒）


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

    translator = GoogleTranslator(source="en", target="ja")

    titles = [a.get("title", "") or "" for a in articles]
    summaries = [a.get("summary", "") or "" for a in articles]

    logger.info("Translating %d titles...", len(titles))
    title_translations = _batch_translate(translator, titles)

    logger.info("Translating %d summaries...", len(summaries))
    summary_translations = _batch_translate(translator, summaries)

    for i, article in enumerate(articles):
        article["title_ja"] = title_translations[i]
        article["summary_ja"] = summary_translations[i]

    logger.info("Translation complete: %d articles", len(articles))
    return articles


def _batch_translate(translator, texts: list[str]) -> list[str]:
    """テキストリストをバッチ翻訳する。空文字・エラーは元テキストを返す。"""
    results = [""] * len(texts)

    for i, text in enumerate(texts):
        if not text.strip():
            continue
        # Google翻訳は1テキスト5000文字上限
        text_truncated = text[:4500]
        try:
            results[i] = translator.translate(text_truncated) or text
        except Exception as e:
            logger.warning("Translation failed for index %d: %s", i, e)
            results[i] = text  # 失敗時は元テキストを使用

        # バッチサイズごとにウェイトを入れてレート制限を回避
        if (i + 1) % BATCH_SIZE == 0:
            time.sleep(REQUEST_DELAY)

    return results
