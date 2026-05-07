"""Google Translate module for international WEB3 news articles (via deep-translator)."""

import logging
import time

logger = logging.getLogger(__name__)

CHUNK_SIZE = 50       # 1回のtranslate_batchで送る件数
CHUNK_DELAY = 3.0     # チャンク間のウェイト（秒）
RETRY_LIMIT = 3       # リトライ回数
RETRY_DELAY = 10.0    # リトライ前のウェイト（秒）


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

    titles = [a.get("title", "") or "" for a in articles]
    summaries = [a.get("summary", "") or "" for a in articles]

    logger.info("Translating %d titles in batches...", len(titles))
    title_translations = _batch_translate(titles)

    logger.info("Translating %d summaries in batches...", len(summaries))
    summary_translations = _batch_translate(summaries)

    for i, article in enumerate(articles):
        article["title_ja"] = title_translations[i]
        article["summary_ja"] = summary_translations[i]

    logger.info("Translation complete: %d articles", len(articles))
    return articles


def _batch_translate(texts: list[str]) -> list[str]:
    """
    テキストリストをCHUNK_SIZEごとにまとめて翻訳する。
    失敗した場合はリトライし、それでも失敗したら空文字を返す。
    """
    results = [""] * len(texts)

    # 空テキストを除いたインデックスマップを作成
    non_empty = [(i, t[:4500]) for i, t in enumerate(texts) if t.strip()]
    if not non_empty:
        return results

    # CHUNK_SIZEごとに分割して翻訳
    for chunk_start in range(0, len(non_empty), CHUNK_SIZE):
        chunk = non_empty[chunk_start: chunk_start + CHUNK_SIZE]
        indices = [c[0] for c in chunk]
        chunk_texts = [c[1] for c in chunk]

        translated = _translate_chunk_with_retry(chunk_texts)

        for idx, text in zip(indices, translated):
            results[idx] = text

        # チャンク間のウェイト（最後のチャンクは不要）
        if chunk_start + CHUNK_SIZE < len(non_empty):
            logger.debug("Waiting %.1fs before next chunk...", CHUNK_DELAY)
            time.sleep(CHUNK_DELAY)

    return results


def _translate_chunk_with_retry(texts: list[str]) -> list[str]:
    """1チャンクをリトライ付きで翻訳する。失敗時は空文字を返す。"""
    from deep_translator import GoogleTranslator

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            translated = GoogleTranslator(source="en", target="ja").translate_batch(texts)
            # translate_batch はNoneを返すことがある
            return [t or "" for t in translated]
        except Exception as e:
            logger.warning("Chunk translation failed (attempt %d/%d): %s", attempt, RETRY_LIMIT, e)
            if attempt < RETRY_LIMIT:
                time.sleep(RETRY_DELAY * attempt)  # 指数バックオフ

    logger.error("All retries failed for chunk of %d texts", len(texts))
    return [""] * len(texts)
