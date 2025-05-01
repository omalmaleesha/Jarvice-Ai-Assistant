import queue
import threading
import pyttsx3
import speech_recognition as sr  # Correct import for speech recognition

class VoiceHandler:
    def __init__(self, gui):
        self.gui = gui
        self.recognizer = sr.Recognizer()  # Use the correct recognizer from speech_recognition
        self.speak_queue = queue.Queue()
        threading.Thread(target=self.speak_loop, daemon=True).start()

    def speak_loop(self):
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'male' in voice.name.lower() or 'en' in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 140)
        self.engine.setProperty('volume', 1.0)
        while True:
            text = self.speak_queue.get()
            if text is None:
                break
            self.engine.say(text)
            self.engine.runAndWait()

    def on_start_utterance(self, name):
        self.gui.root.after(0, self.gui.start_speaking, name)

    def on_finish_utterance(self, name, completed):
        self.gui.root.after(0, self.gui.stop_speaking, name, completed)

    def speak(self, text):
        self.speak_queue.put(text)

    def listen(self):
        """
        Listens to the microphone and returns the recognized text.
        """
        with sr.Microphone() as source:  # Use the correct Microphone class from speech_recognition
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                print("Could not understand the audio.")
                return None
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                return None
            except sr.WaitTimeoutError:
                print("Listening timed out while waiting for phrase.")
                return None

    def stop(self):
        self.speak_queue.put(None)