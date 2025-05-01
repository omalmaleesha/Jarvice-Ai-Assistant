import requests


def get_llm_response(query):
    api_key = "your_api_key"  # Replace with your actual API key
    if not api_key:
        print("Please set the GROQ_API_KEY environment variable.")
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            content = response.json()
            return content["choices"][0]["message"]["content"].strip()
        else:
            print(f"Error from Groq API: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Exception in getting response: {e}")
        return None