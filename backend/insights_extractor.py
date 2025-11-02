import os
import json
from typing import Dict, List, Tuple, Any

try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import io
    import base64
    _wordcloud_available = True
except ImportError:
    _wordcloud_available = False

# ---------- Optional NLP deps (graceful fallback to LLM) ----------
_nlp = None
_sia = None

# Try spaCy for NER
try:
    import spacy
    try:
        _nlp = spacy.load("en_core_web_lg")
    except OSError:
        print("Downloading spaCy model 'en_core_web_lg'...")
        spacy.cli.download("en_core_web_lg")
        _nlp = spacy.load("en_core_web_lg")
except Exception as e:
    print(f"Error loading spaCy model: {e}")
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

# Import unified LLM client (Gemini + Ollama fallback)
from backend.llm_client import generate_text

# TF-IDF keywords
def extract_keywords_tfidf(text: str, top_n: int = 12) -> List[Tuple[str, float]]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    if not text.strip():
        return []

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
        max_features=5000
    )
    X = vectorizer.fit_transform([text])
    scores = X.toarray()[0]
    terms = np.array(vectorizer.get_feature_names_out())
    idx = scores.argsort()[::-1][:top_n]
    # Return keywords with their scores
    return [(terms[i], scores[i]) for i in idx if len(terms[i]) > 2]

def extract_entities(text: str, max_chars: int = 8000) -> Dict[str, List[Dict[str, Any]]]: # Changed return type
    snippet = text[:max_chars]

    if _nlp is not None:
        doc = _nlp(snippet)
        all_entities: Dict[str, List[Dict[str, Any]]] = {}
        for ent in doc.ents:
            label = ent.label_
            val = ent.text.strip()
            if not val:
                continue
            all_entities.setdefault(label, []).append({"text": val, "start": ent.start_char, "end": ent.end_char})
        
        # For consistent display, we might want to count and sort as well
        # But for annotated view, just the raw entities with offsets are fine.
        # If we want top entities with counts, we'd process all_entities further.

        # For the UI display, we'll still want top entities with counts.
        # Let's create a separate structure for that, while keeping offsets for highlighting.
        entity_counts: Dict[str, Dict[str, int]] = {}
        for label, entities_list in all_entities.items():
            entity_counts.setdefault(label, {})
            for ent_data in entities_list:
                entity_counts[label][ent_data["text"]] = entity_counts[label].get(ent_data["text"], 0) + 1
        
        top_entities_with_counts: Dict[str, List[Tuple[str, int]]] = {}
        for label, counts in entity_counts.items():
            top_entities_with_counts[label] = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:8]

        return {"raw_entities": all_entities, "top_entities": top_entities_with_counts}

    # ---------- LLM fallback ----------
    try:
        prompt = (
            "Extract named entities from the text. For each entity, return its text, label, start_offset, and end_offset. "
            "Also, provide a summary of top 8 entities with counts per label. "
            "Return JSON with two top-level keys: 'raw_entities' (a dictionary where keys are labels and values are lists of objects {text, start, end}) "
            "and 'top_entities' (a dictionary where keys are labels and values are lists of [entity, count] pairs). "
            "Text:\n" + snippet
        )
        raw = generate_text(prompt)
        import re
        json_text = re.findall(r"\{[\s\S]*\}", raw)
        if json_text:
            return json.loads(json_text[0])
    except Exception:
        pass
    return {"raw_entities": {}, "top_entities": {}}

def sentiment_overview(text: str, max_chars: int = 8000) -> Dict[str, Any]:
    snippet = text[:max_chars]

    if _sia is not None:
        scores = _sia.polarity_scores(snippet)
        return scores

    # ---------- LLM fallback ----------
    try:
        prompt = (
            "Classify overall sentiment of the following text as positive, neutral, or negative "
            "and give a compound score between -1 and 1. "
            "Return a JSON object with keys: compound, pos, neu, neg.\n\nText:\n" + snippet
        )
        raw = generate_text(prompt)
        import re
        json_text = re.findall(r"\{[\s\S]*\}", raw)
        if json_text:
            return json.loads(json_text[0])
    except Exception:
        pass

    return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}

def sentiment_trend_analysis(text: str, segment_size: int = 500) -> List[Dict[str, Any]]:
    """Analyzes sentiment across segments of text to show a trend."""
    if not _sia:
        return [] # Cannot perform trend analysis without SIA

    segments = []
    # Simple segment splitting for now, could be improved with NLP sentence splitting
    for i in range(0, len(text), segment_size):
        segments.append(text[i:i+segment_size])

    trend_data = []
    for i, segment in enumerate(segments):
        if segment.strip():
            scores = _sia.polarity_scores(segment)
            trend_data.append({"segment": i + 1, "compound": scores['compound'], "pos": scores['pos'], "neu": scores['neu'], "neg": scores['neg']})
    return trend_data

def detect_figures_tables(pdf_path: str) -> Dict[str, Any]:
    import fitz
    stats = {
        "pages": 0,
        "total_images": 0,
        "pages_with_images": 0,
        "likely_table_lines": 0,
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

            text = page.get_text("text")
            for line in text.splitlines():
                if line.count("|") >= 2 or line.count("\t") >= 3:
                    stats["likely_table_lines"] += 1
    except Exception:
        pass

    return stats

def concise_summary(text: str, max_chars: int = 6000) -> str:
    snippet = text[:max_chars]
    prompt = (
        "Create a concise bullet summary (5-8 bullets). "
        "Use clear, factual points and avoid repetition.\n\nText:\n" + snippet
    )
    return generate_text(prompt)

def generate_word_cloud_image(keywords: List[str]):
    """Generates a base64 encoded word cloud image from a list of keywords."""
    if not _wordcloud_available or not keywords:
        return None

    try:
        # Join keywords into a single string
        text = " ".join(keywords)
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

        # Save to a bytes buffer
        img_buffer = io.BytesIO()
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(img_buffer, format='png')
        plt.close() # Close the plot to free memory
        img_buffer.seek(0)

        # Encode image to base64
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Error generating word cloud: {e}")
        return None
# -----------------------------------------

# --- The correct extract_insights function (ensure this is the ONLY one) ---
def extract_insights(text: str, pdf_path: str = "") -> Dict[str, Any]:
    keywords_with_scores = extract_keywords_tfidf(text, top_n=25)
    keywords_only = [kw for kw, score in keywords_with_scores]
    entities = extract_entities(text)
    sentiment = sentiment_overview(text)
    figures_tables = (
        detect_figures_tables(pdf_path)
        if pdf_path
        else {"pages": 0, "total_images": 0, "pages_with_images": 0, "likely_table_lines": 0}
    )
    word_cloud_image = generate_word_cloud_image(keywords_only)
    sentiment_trend = sentiment_trend_analysis(text)

    return {
        "full_text": text,
        "keywords": keywords_only[:15],
        "keyword_scores": keywords_with_scores,
        "entities": entities["top_entities"],
        "raw_entities_with_offsets": entities["raw_entities"],
        "sentiment": sentiment,
        "sentiment_trend": sentiment_trend,
        "figures_tables": figures_tables,
        "word_cloud_image": word_cloud_image
    }

def save_insights_to_json(insights: Dict[str, Any], out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    return out_path


