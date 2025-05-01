import datetime
import json


def log_conversation(query, response):
    timestamp = datetime.datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "query": query,
        "response": response
    }
    try:
        with open("conversation_history.json", "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []
    history.append(entry)
    with open("conversation_history.json", "w") as f:
        json.dump(history, f, indent=4)

def load_conversation_history():
    try:
        with open("conversation_history.json", "r") as f:
            history = json.load(f)
            return {entry["query"].lower(): entry["response"] for entry in history}
    except FileNotFoundError:
        return {}