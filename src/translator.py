"""DeepL translation module for international WEB3 news articles."""

import logging
import os

logger = logging.getLogger(__name__)


def translate_articles(articles: list[dict], api_key: str | None = None) -> list[dict]:
    """
    Translate title and summary of international (English) articles into Japanese.
    Adds `title_ja` and `summary_ja` keys to each article dict in-place.
    Returns the same list.
    """
    key = api_key or os.environ.get("DEEPL_API_KEY", "")
    if not key:
        logger.warning("DEEPL_API_KEY not set, skipping translation")
        for article in articles:
            article.setdefault("title_ja", "")
            article.setdefault("summary_ja", "")
        return articles

    try:
        import deepl
    except ImportError:
        logger.error("deepl package not installed")
        for article in articles:
            article.setdefault("title_ja", "")
            article.setdefault("summary_ja", "")
        return articles

    translator = deepl.Translator(key)

    # Separate texts to translate: titles and summaries
    titles = [a.get("title", "") or "" for a in articles]
    summaries = [a.get("summary", "") or "" for a in articles]

    # Batch translate titles
    title_translations = _batch_translate(translator, titles)
    # Batch translate summaries (skip empty ones)
    summary_translations = _batch_translate(translator, summaries)

    for i, article in enumerate(articles):
        article["title_ja"] = title_translations[i]
        article["summary_ja"] = summary_translations[i]

    logger.info("Translation complete: %d articles", len(articles))
    return articles


def _batch_translate(translator, texts: list[str]) -> list[str]:
    """Translate a list of texts, returning empty string for empties. Handles quota errors."""
    results = [""] * len(texts)

    # Build index map for non-empty texts
    non_empty = [(i, t) for i, t in enumerate(texts) if t.strip()]
    if not non_empty:
        return results

    indices, to_translate = zip(*non_empty)

    try:
        import deepl
        translated = translator.translate_text(
            list(to_translate),
            source_lang="EN",
            target_lang="JA",
        )
        for idx, result in zip(indices, translated):
            results[idx] = result.text
    except Exception as e:
        logger.error("DeepL translation failed: %s", e)
        # Fall back to original text on error
        for idx, original in zip(indices, to_translate):
            results[idx] = original

    return results
