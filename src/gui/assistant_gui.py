from tkinter import Tk, Label, Canvas, Entry, Button, Frame, Scrollbar, Text, END
import threading
import queue
import os
from gui.bubble_animation import BubbleAnimation
from voice.voice_handler import VoiceHandler
from utils.conversation_logger import log_conversation, load_conversation_history
from utils.llm_api import get_llm_response
from utils.time_utils import get_greeting_message

class AssistantGUI:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("JARVIS Modern")
        self.root.configure(bg="#1e1e2f")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Chat display area
        self.chat_frame = Frame(self.root, bg="#1e1e2f")
        self.chat_frame.pack(pady=10, fill="both", expand=True)

        self.scrollbar = Scrollbar(self.chat_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.chat_display = Text(self.chat_frame, wrap="word", yscrollcommand=self.scrollbar.set,
                                 bg="#2e2e3f", fg="white", font=("Poppins", 12), state="disabled")
        self.chat_display.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.chat_display.yview)

        # User input area
        self.input_frame = Frame(self.root, bg="#1e1e2f")
        self.input_frame.pack(fill="x", pady=10)

        self.user_input = Entry(self.input_frame, font=("Poppins", 14), bg="#2e2e3f", fg="white", insertbackground="white")
        self.user_input.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        self.user_input.bind("<Return>", self.on_user_input)

        self.send_button = Button(self.input_frame, text="Send", font=("Poppins", 12), bg="#6441a5", fg="white",
                                  activebackground="#8964d1", command=self.on_send_click)
        self.send_button.pack(side="right", padx=10)

        # Add a "Listen" button
        self.listen_button = Button(self.root, text="Listen", font=("Poppins", 12), bg="#6441a5", fg="white",
                                    activebackground="#8964d1", command=self.on_listen_click)
        self.listen_button.pack(pady=10)

        # Status label
        self.status_label = Label(self.root, text="Ready", font=("Poppins", 12), bg="#1e1e2f", fg="white")
        self.status_label.pack(pady=5)

        # Initialize components
        self.state = 0  # 0: idle, 1: waiting for file name, 2: waiting for file type
        self.file_name = ""
        self.file_type = ""
        self.bubble_animation = BubbleAnimation(Canvas(self.root))
        self.voice_handler = VoiceHandler(self)
        self.response_queue = queue.Queue()

        self.conversation_history = self.load_conversation_history()
        self.startup_greeting()

        self.root.after(100, self.check_queue)
        threading.Thread(target=self.listen_loop, daemon=True).start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.voice_handler.stop()
        self.root.destroy()

    def load_conversation_history(self):
        return load_conversation_history()

    def startup_greeting(self):
        message = get_greeting_message()
        self.display_message("JARVIS", message)
        self.voice_handler.speak(message)

    def on_user_input(self, event=None):
        query = self.user_input.get().strip()
        if query:
            self.process_query(query)
            self.user_input.delete(0, END)

    def on_send_click(self):
        self.on_user_input()

    def process_query(self, query):
        self.display_message("You", query)
        # Handle cancel command at any state
        if "cancel" in query.lower() or "stop" in query.lower():
            if self.state != 0:
                self.state = 0
                response = "File creation cancelled."
            else:
                response = "No operation to cancel."
            self.display_message("JARVIS", response)
            self.voice_handler.speak(response)
            self.status_label.config(text="Ready")
            return

        if self.state == 0:
            if "create file" in query.lower():
                self.state = 1
                response = "Please provide the file name."
                self.display_message("JARVIS", response)
                self.voice_handler.speak(response)
                self.status_label.config(text="Waiting for file name...")
            elif "exit" in query.lower() or "goodbye" in query.lower():
                self.status_label.config(text="Exiting...")
                response = "Goodbye, sir."
                self.display_message("JARVIS", response)
                log_conversation(query, response)
                self.voice_handler.speak(response)
                self.root.quit()
            elif "create a text file" in query.lower():
                self.create_text_file()
            elif "delete the text file" in query.lower():
                self.delete_text_file()
            else:
                self.status_label.config(text="Processing...")
                threading.Thread(target=self.get_response, args=(query,), daemon=True).start()
        elif self.state == 1:
            self.file_name = query.strip()
            self.state = 2
            response = f"You said the file name is '{self.file_name}'. Now, please provide the file type, like 'txt' or 'doc'."
            self.display_message("JARVIS", response)
            self.voice_handler.speak(response)
            self.status_label.config(text="Waiting for file type...")
        elif self.state == 2:
            self.file_type = query.strip()
            response = f"You said the file type is '{self.file_type}'. Creating the file '{self.file_name}.{self.file_type}'."
            self.display_message("JARVIS", response)
            self.voice_handler.speak(response)
            self.create_file()
            self.state = 0
            self.status_label.config(text="Ready")

    def create_file(self):
        directory = r"C:\icet\text file generate"
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, f"{self.file_name}.{self.file_type}")
        try:
            with open(file_path, "w") as file:
                file.write("This is a generated file.")
            response = f"File created at {file_path}."
        except Exception as e:
            response = f"Failed to create file: {e}"
        self.display_message("JARVIS", response)
        self.voice_handler.speak(response)

    def create_text_file(self):
        directory = r"C:\icet\text file generate"
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, "generated_file.txt")
        try:
            with open(file_path, "w") as file:
                file.write("This is a generated text file.")
            response = f"Text file created at {file_path}."
        except Exception as e:
            response = f"Failed to create text file: {e}"
        self.display_message("JARVIS", response)
        self.voice_handler.speak(response)

    def delete_text_file(self):
        file_path = r"C:\icet\text file generate\generated_file.txt"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                response = "Text file deleted successfully."
            except Exception as e:
                response = f"Failed to delete text file: {e}"
        else:
            response = "No text file found to delete."
        self.display_message("JARVIS", response)
        self.voice_handler.speak(response)

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
            self.display_message("JARVIS", response)
            self.voice_handler.speak(response)
            self.status_label.config(text="Ready")
            self.state = 0
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def display_message(self, sender, message):
        self.chat_display.config(state="normal")
        self.chat_display.insert(END, f"{sender}: {message}\n")
        self.chat_display.config(state="disabled")
        self.chat_display.see(END)
        print(f"{sender}: {message}")  # Log to terminal

    def listen_loop(self):
        while True:
            try:
                self.status_label.config(text="Listening...")
                self.bubble_animation.animate("listening")
                query = self.voice_handler.listen()
                if query:
                    self.process_query(query)
                else:
                    self.status_label.config(text="Ready")
            except Exception as e:
                print(f"Error in listen_loop: {e}")
                self.status_label.config(text="Error occurred")

    def on_listen_click(self):
        self.status_label.config(text="Listening...")
        self.bubble_animation.animate("listening")
        threading.Thread(target=self.start_listening, daemon=True).start()

    def start_listening(self):
        query = self.voice_handler.listen()
        if query:
            self.process_query(query)
        else:
            self.status_label.config(text="Ready")