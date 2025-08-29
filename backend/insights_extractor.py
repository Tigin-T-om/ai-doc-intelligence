# backend/insights_extractor.py

import os
import json
from typing import Dict, List, Tuple, Any

# ---------- Optional NLP deps (graceful fallback to LLM) ----------
_nlp = None
_sia = None

# Try spaCy for NER
try:
    import spacy
    # Use small English model if present; user can: python -m spacy download en_core_web_sm
    _nlp = spacy.load("en_core_web_sm")
except Exception:
    _nlp = None

# Try VADER for sentiment
try:
    from nltk.sentiment import SentimentIntensityAnalyzer
    import nltk

    try:
        _ = nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon")
    _sia = SentimentIntensityAnalyzer()
except Exception:
    _sia = None

# TF-IDF keywords
def extract_keywords_tfidf(text: str, top_n: int = 12) -> List[str]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    if not text.strip():
        return []

    # Keep it fairly light; 1-2 grams to surface key phrases
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=5000)
    X = vectorizer.fit_transform([text])
    scores = X.toarray()[0]
    terms = np.array(vectorizer.get_feature_names_out())
    idx = scores.argsort()[::-1][:top_n]
    return [t for t in terms[idx] if len(t) > 2]

def extract_entities(text: str, max_chars: int = 8000) -> Dict[str, List[Tuple[str, int]]]:
    """
    Returns top entities grouped by label: {"PERSON":[("Alice",3),...], "ORG":[...], "GPE":[...], "DATE":[...]}
    Falls back to LLM if spaCy is unavailable.
    """
    snippet = text[:max_chars]

    if _nlp is not None:
        doc = _nlp(snippet)
        buckets: Dict[str, Dict[str, int]] = {}
        for ent in doc.ents:
            label = ent.label_
            val = ent.text.strip()
            if not val:
                continue
            buckets.setdefault(label, {})
            buckets[label][val] = buckets[label].get(val, 0) + 1

        # Top 8 per label
        top: Dict[str, List[Tuple[str, int]]] = {}
        for label, counts in buckets.items():
            top[label] = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:8]
        return top

    # ---------- LLM fallback ----------
    try:
        from backend.ollama_client import generate_response
        prompt = (
            "Extract named entities from the text. Return JSON with keys PERSON, ORG, GPE, DATE. "
            "For each key, provide a list of [entity, count] pairs, top 8 per label. "
            "Text:\n" + snippet
        )
        raw = generate_response(prompt, model="mistral")
        # Best-effort JSON parsing
        import re, json
        json_text = re.findall(r"\{[\s\S]*\}", raw)
        if json_text:
            return json.loads(json_text[0])
    except Exception:
        pass
    return {}

def sentiment_overview(text: str, max_chars: int = 8000) -> Dict[str, Any]:
    """
    Returns {"compound": float, "pos": float, "neu": float, "neg": float}
    Falls back to LLM classification if VADER unavailable.
    """
    snippet = text[:max_chars]

    if _sia is not None:
        scores = _sia.polarity_scores(snippet)
        return scores

    # ---------- LLM fallback ----------
    try:
        from backend.ollama_client import generate_response
        prompt = (
            "Classify overall sentiment of the following text as positive, neutral, or negative "
            "and give a compound score between -1 and 1. "
            "Return a JSON object with keys: compound, pos, neu, neg.\n\nText:\n" + snippet
        )
        raw = generate_response(prompt, model="mistral")
        import re, json
        json_text = re.findall(r"\{[\s\S]*\}", raw)
        if json_text:
            return json.loads(json_text[0])
    except Exception:
        pass

    # Least-informative safe default
    return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}

def detect_figures_tables(pdf_path: str) -> Dict[str, Any]:
    """
    Lightweight page stats: images/figures per page via PyMuPDF, and a naive table heuristic.
    """
    import fitz
    stats = {
        "pages": 0,
        "total_images": 0,
        "pages_with_images": 0,
        "likely_table_lines": 0,  # crude heuristic: lines containing many separators
    }
    if not os.path.exists(pdf_path):
        return stats

    try:
        doc = fitz.open(pdf_path)
        stats["pages"] = len(doc)

        for page in doc:
            imgs = page.get_images(full=True)
            if imgs:
                stats["pages_with_images"] += 1
                stats["total_images"] += len(imgs)

            # Very naive text-based table hint
            text = page.get_text("text")
            for line in text.splitlines():
                if line.count("|") >= 2 or line.count("\t") >= 3:
                    stats["likely_table_lines"] += 1
    except Exception:
        pass

    return stats

def concise_summary(text: str, max_chars: int = 6000, model: str = "llama2") -> str:
    """
    Uses your Ollama LLM to create a concise bullet summary (map-reduce style is a later step).
    """
    from backend.ollama_client import generate_response
    snippet = text[:max_chars]
    prompt = (
        "Create a concise bullet summary (5-8 bullets). "
        "Use clear, factual points and avoid repetition.\n\nText:\n" + snippet
    )
    return generate_response(prompt, model=model)

def extract_insights(text: str, pdf_path: str = "") -> Dict[str, Any]:
    """
    High-level wrapper that returns a unified insights dict.
    """
    keywords = extract_keywords_tfidf(text, top_n=12)
    entities = extract_entities(text)
    sentiment = sentiment_overview(text)
    figures_tables = detect_figures_tables(pdf_path) if pdf_path else {"pages": 0, "total_images": 0, "pages_with_images": 0, "likely_table_lines": 0}
    summary = concise_summary(text)

    return {
        "summary": summary,
        "keywords": keywords,
        "entities": entities,
        "sentiment": sentiment,
        "figures_tables": figures_tables,
    }

def save_insights_to_json(insights: Dict[str, Any], out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    return out_path
