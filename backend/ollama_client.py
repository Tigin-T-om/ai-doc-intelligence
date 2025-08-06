import ollama

# def generate_response(prompt):
#     response = ollama.chat(model="llama2", messages=[{"role": "user", "content": prompt}])
#     return response['message']['content']

def generate_response(prompt, model="phi3:mini"):  # 🔁 or use "mistral"
    response = ollama.chat(model=model, messages=[
        {"role": "user", "content": prompt}
    ])
    return response["message"]["content"]


