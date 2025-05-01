class VoiceHandler:
    def __init__(self, gui):
        self.gui = gui
        self.recognizer = sr.Recognizer()
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
        self.engine.connect('started-utterance', self.on_start_utterance)
        self.engine.connect('finished-utterance', self.on_finish_utterance)
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
        self.speak_queue.put(None)