def listen_for_audio():
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            return audio
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            print("Could not understand audio or timeout.")
            return None

def recognize_speech(audio):
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return None
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return None

def listen_and_recognize():
    audio = listen_for_audio()
    if audio:
        return recognize_speech(audio)
    return None