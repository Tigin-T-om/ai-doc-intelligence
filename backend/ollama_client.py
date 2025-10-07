import ollama

def generate_response(prompt, model="llama2"):
    """
    Direct Ollama wrapper for local inference.
    Called by llm_client if Gemini fails or quota is exceeded.
    """
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]
