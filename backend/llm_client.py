# backend/llm_client.py
import os
import requests
from dotenv import load_dotenv
from backend.db.db_handler import get_session, add_api_log
import time

# Load .env file
load_dotenv()

# === Gemini Configuration ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# --- ★★★ THE FIX IS HERE ★★★ ---
# Use the stable model found via the curl command
GEMINI_MODEL = "gemini-2.5-flash" 
# Use the v1beta endpoint as used in the curl command
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent" 
# ---------------------------------

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
            # --- LOGGING ADDED ---
            try:
                with get_session() as db:
                    add_api_log(db, provider="Gemini", model=GEMINI_MODEL)
            except Exception as log_e:
                print(f"CRITICAL: Failed to log API call - {log_e}")
            # --- END LOGGING ---
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise RuntimeError(f"Unexpected Gemini response format: {data}")
    elif resp.status_code == 429:
        raise RuntimeError("Gemini quota exceeded or rate limited (429)")
    elif resp.status_code == 503:
        raise RuntimeError("Gemini server overloaded (503), try again later")
    else:
        # Pass the full error from Google back to the user
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
                try:
                    with get_session() as db:
                        add_api_log(db, provider="Ollama", model=ollama_model)
                except Exception as log_e:
                    print(f"CRITICAL: Failed to log API call - {log_e}")
                return ollama_generate(prompt, model=ollama_model), f"Ollama ({ollama_model})"
        except Exception as e:
            print(f"⚠️ {provider} failed: {e}")
            continue

    raise RuntimeError("All LLM providers failed.")

def test_api_provider(provider: str, model: str = "llama2"):
    """
    Runs a simple 'hello' prompt to test a provider.
    Returns: (success: bool, message: str)
    """
    try:
        if provider.lower() == "gemini":
            test_prompt = "Hello, respond with just 'OK'."
            response = generate_with_gemini(test_prompt)
            if "ok" in response.lower():
                return True, "Gemini connection successful."
            else:
                return False, f"Gemini response unexpected: {response}"
        
        elif provider.lower() == "ollama":
            test_prompt = "Hello, respond with just 'OK'."
            response = ollama_generate(test_prompt, model=model)
            if "ok" in response.lower():
                return True, f"Ollama ({model}) connection successful."
            else:
                return False, f"Ollama response unexpected: {response}"
        
        else:
            return False, "Unknown provider."
            
    except Exception as e:
        return False, f"API test failed: {e}"