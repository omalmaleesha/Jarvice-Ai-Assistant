import tkinter as tk
import random
import speech_recognition as sr
import pyttsx3
import requests
import json
import datetime
import threading
import queue
import math

class VoiceHandler:
    def __init__(self, gui):
        self.gui = gui
        self.recognizer = sr.Recognizer()
        self.speak_queue = queue.Queue()
        threading.Thread(target=self.speak_loop, daemon=True).start()

    def speak_loop(self):
        """Initialize and run the pyttsx3 engine in a dedicated thread."""
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'male' in voice.name.lower() or 'en' in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 140)
        self.engine.setProperty('volume', 1.0)
        self.engine.connect('started-utterance', self.on_start_utterance)
        self.engine.connect('finished-utterance', self.on_finish_utterance)
        while True:
            text = self.speak_queue.get()
            if text is None:  # Exit signal
                break
            self.engine.say(text)
            self.engine.runAndWait()

    def on_start_utterance(self, name):
        """Marshal the start speaking callback to the main thread."""
        self.gui.root.after(0, self.gui.start_speaking, name)

    def on_finish_utterance(self, name, completed):
        """Marshal the stop speaking callback to the main thread."""
        self.gui.root.after(0, self.gui.stop_speaking, name, completed)

    def speak(self, text):
        """Queue text to be spoken by the speaking thread."""
        self.speak_queue.put(text)

    def listen(self):
        """Handle audio input in the listening thread."""
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

    def stop(self):
        """Stop the speaking thread cleanly."""
        self.speak_queue.put(None)

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
        self.bubble = None
        self.bubble_phase = 0  # Single phase for one bubble
        self.create_bubble()

        self.voice_handler = VoiceHandler(self)
        self.response_queue = queue.Queue()

        # Load conversation history
        self.conversation_history = self.load_conversation_history()

        # Startup greeting
        self.startup_greeting()

        self.animate()
        self.root.after(100, self.check_queue)
        threading.Thread(target=self.listen_loop, daemon=True).start()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handle window close event to stop threads cleanly."""
        self.voice_handler.stop()
        self.root.destroy()

    def load_conversation_history(self):
        try:
            with open("conversation_history.json", "r") as f:
                history = json.load(f)
                return {entry["query"].lower(): entry["response"] for entry in history}
        except FileNotFoundError:
            return {}

    def create_bubble(self):
        x = 200  # Center of canvas (400/2)
        y = 75   # Center of canvas (150/2)
        size = 20  # Base size
        self.bubble = self.canvas.create_oval(
            x - size, y - size, x + size, y + size,
            fill="#6441a5", outline="", tags="bubble"
        )
        self.bubble_phase = random.uniform(0, 2 * math.pi)  # Random initial phase

    def animate(self):
        x1, y1, x2, y2 = self.canvas.coords(self.bubble)
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        base_size = (x2 - x1) / 2  # Current radius

        if self.state == "idle":
            size_variation = 5 * math.sin(self.bubble_phase)
            new_size = base_size + size_variation
            color = "#4b367c"  # Darker, less vibrant
        elif self.state == "listening":
            size_variation = 10 * math.sin(self.bubble_phase * 1.5)
            new_size = base_size + size_variation
            color = "#6441a5"  # Brighter
        elif self.state == "speaking":
            size_variation = 15 * math.sin(self.bubble_phase * 2)
            new_size = base_size + size_variation
            color = "#8964d1"  # Most vibrant
        else:
            new_size = base_size
            color = "#4b367c"

        self.canvas.coords(self.bubble,
                           center_x - new_size, center_y - new_size,
                           center_x + new_size, center_y + new_size)
        self.canvas.itemconfig(self.bubble, fill=color)
        self.bubble_phase += 0.1  # Increment phase

        self.root.after(50, self.animate)

    def start_speaking(self, name=None, data=None):
        self.state = "speaking"

    def stop_speaking(self, name=None, data=None):
        self.state = "idle"

    def startup_greeting(self):
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        message = f"{greeting}, it's {current_time}. I am JARVIS, your assistant."
        self.voice_handler.speak(message)

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
        query_lower = query.lower()
        if query_lower in self.conversation_history:
            response = self.conversation_history[query_lower]
        else:
            response = get_llm_response(query)
            if response:
                self.conversation_history[query_lower] = response
                log_conversation(query, response)
            else:
                response = "I'm sorry, I couldn't process that."
        self.response_queue.put((query, response))

    def check_queue(self):
        try:
            query, response = self.response_queue.get_nowait()
            self.status_label.config(text="Speaking...")
            self.voice_handler.speak(response)
            self.status_label.config(text="Ready")
            self.state = "idle"
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

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