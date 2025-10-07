# backend/llm_client.py
import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# === Gemini Configuration ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"  # fast model
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# === Ollama fallback ===
from backend.ollama_client import generate_response as ollama_generate

def generate_with_gemini(prompt: str, timeout: int = 30) -> str:
    """Generate text using Gemini API."""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not found. Set GEMINI_API_KEY in .env")

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    body = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        resp = requests.post(GEMINI_URL, headers=headers, params=params, json=body, timeout=timeout)
    except requests.exceptions.Timeout:
        raise RuntimeError("Gemini request timed out")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Gemini request failed: {e}")

    if resp.status_code == 200:
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise RuntimeError(f"Unexpected Gemini response format: {data}")
    elif resp.status_code == 429:
        raise RuntimeError("Gemini quota exceeded or rate limited (429)")
    elif resp.status_code == 503:
        raise RuntimeError("Gemini server overloaded (503), try again later")
    else:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")

def generate_text(prompt: str, prefer=["gemini", "ollama"], ollama_model="llama2"):
    """
    Generate text with preferred providers.
    Fallback automatically if a provider fails.
    Returns: (text, provider)
    """
    for provider in prefer:
        try:
            if provider.lower() == "gemini":
                return generate_with_gemini(prompt), "Gemini"
            elif provider.lower() == "ollama":
                return ollama_generate(prompt, model=ollama_model), f"Ollama ({ollama_model})"
        except Exception as e:
            print(f"⚠️ {provider} failed: {e}")
            continue

    raise RuntimeError("All LLM providers failed.")
