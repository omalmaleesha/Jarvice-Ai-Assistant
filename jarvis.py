import tkinter as tk
import random
import speech_recognition as sr
import pyttsx3
import requests
import json
import datetime
import threading
import queue

class VoiceHandler:
    def __init__(self, gui):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()

        # Set a deeper, slower JARVIS-like voice
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'male' in voice.name.lower() or 'en' in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break

        self.engine.setProperty('rate', 140)   # slower for robotic feel
        self.engine.setProperty('volume', 1.0) # maximum volume

        self.engine.connect('started-utterance', gui.start_speaking)
        self.engine.connect('finished-utterance', gui.stop_speaking)

    def listen(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                print("Could not understand audio or timeout.")
                return None

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS Modern")
        self.root.configure(bg="#0e0e10")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        self.status_label = tk.Label(root, text="Ready", font=("Poppins", 16), bg="#0e0e10", fg="white")
        self.status_label.pack(pady=20)

        self.canvas = tk.Canvas(root, width=400, height=150, bg="#1a1a2e", highlightthickness=0)
        self.canvas.pack(pady=10)

        self.state = "idle"  # idle, listening, speaking
        self.bars = []
        self.create_bars()

        self.voice_handler = VoiceHandler(self)
        self.response_queue = queue.Queue()

        self.animate()
        self.root.after(100, self.check_queue)
        threading.Thread(target=self.listen_loop, daemon=True).start()

    def create_bars(self):
        self.bars.clear()
        bar_width = 10
        spacing = 8
        for i in range(20):
            x0 = i * (bar_width + spacing) + 20
            y0 = 75
            x1 = x0 + bar_width
            y1 = y0 - 20
            bar = self.canvas.create_rectangle(x0, y0, x1, y1, fill="#6441a5", width=0)
            self.bars.append(bar)

    def animate(self):
        for idx, bar in enumerate(self.bars):
            if self.state == "idle":
                height = 20
            elif self.state == "listening":
                height = random.randint(20, 50)
            elif self.state == "speaking":
                height = random.randint(40, 100)
            else:
                height = 20

            x0, y0, x1, y1 = self.canvas.coords(bar)
            self.canvas.coords(bar, x0, 130, x1, 130 - height)
        self.root.after(100, self.animate)

    def start_speaking(self, name=None, data=None):
        self.state = "speaking"

    def stop_speaking(self, name=None, data=None):
        self.state = "idle"

    def listen_loop(self):
        while True:
            self.status_label.config(text="Listening...")
            self.state = "listening"
            query = self.voice_handler.listen()
            if query:
                if "exit" in query.lower() or "goodbye" in query.lower():
                    self.status_label.config(text="Exiting...")
                    response = "Goodbye, sir."
                    log_conversation(query, response)
                    self.voice_handler.speak(response)
                    self.root.quit()
                else:
                    self.status_label.config(text="Processing...")
                    threading.Thread(target=self.get_response, args=(query,), daemon=True).start()
            else:
                print("No valid input detected.")
                self.status_label.config(text="Ready")
                self.state = "idle"

    def get_response(self, query):
        response = get_llm_response(query)
        if response:
            self.response_queue.put((query, response))
        else:
            error_message = "I'm sorry, I couldn't process that."
            self.response_queue.put((query, error_message))

    def check_queue(self):
        try:
            query, response = self.response_queue.get_nowait()
            self.status_label.config(text="Speaking...")
            log_conversation(query, response)
            self.voice_handler.speak(response)
            self.status_label.config(text="Ready")
            self.state = "idle"
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

def get_llm_response(query):
    api_key = "your-groq-api-key"  # Replace with your actual API key
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

if __name__ == "__main__":
    root = tk.Tk()
    gui = AssistantGUI(root)
    root.mainloop()
