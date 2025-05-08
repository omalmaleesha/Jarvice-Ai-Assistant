from tkinter import Tk, Label, Entry, Frame, Scrollbar, Text, END
import threading
import queue
import os
from voice.voice_handler import VoiceHandler
from utils.conversation_logger import log_conversation, load_conversation_history
from utils.llm_api import get_llm_response
from utils.time_utils import get_greeting_message

class AssistantGUI:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("JARVIS Command Prompt")
        self.root.configure(bg="#000000")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Chat display area
        self.chat_frame = Frame(self.root, bg="#000000")
        self.chat_frame.pack(pady=10, fill="both", expand=True)

        self.scrollbar = Scrollbar(self.chat_frame, bg="#FFFFFF", troughcolor="#000000", activebackground="#CCCCCC", width=16)
        self.scrollbar.pack(side="right", fill="y")

        self.chat_display = Text(self.chat_frame, wrap="word", yscrollcommand=self.scrollbar.set,
                                 bg="#000000", fg="#FFFFFF", font=("Consolas", 12), state="disabled", relief="flat", bd=0)
        self.chat_display.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.chat_display.yview)

        # User input area
        self.input_frame = Frame(self.root, bg="#000000")
        self.input_frame.pack(fill="x", pady=10)

        self.user_input = Entry(self.input_frame, font=("Consolas", 14), bg="#000000", fg="#FFFFFF", insertbackground="#FFFFFF", bd=0, relief="flat", highlightthickness=0)
        self.user_input.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        self.user_input.bind("<Return>", self.on_user_input)
        self.user_input.focus_set()

        # Status label
        self.status_label = Label(self.root, text="Ready", font=("Consolas", 12), bg="#000000", fg="#FFFFFF")
        self.status_label.pack(pady=5)

        # Initialize components
        self.state = 0  # 0: idle, 1: waiting for file name, 2: waiting for file type, 3: writing to file
        self.paused = False  # Tracks if the assistant is paused
        self.file_name = ""
        self.file_type = ""
        self.current_file_path = None
        self.file_handle = None
        self.voice_handler = VoiceHandler(self)
        self.action_queue = queue.Queue()

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
        self.action_queue.put(("display", ("", message)))
        self.action_queue.put(("speak", message))

    def on_user_input(self, event=None):
        query = self.user_input.get().strip()
        if query:
            self.process_query(query)
            self.user_input.delete(0, END)

    def process_query(self, query):
        self.action_queue.put(("display", (">", query)))

        if "stop" in query.lower() or "enough" in query.lower():
            self.paused = True
            self.voice_handler.stop_speaking()
            while not self.action_queue.empty():
                try:
                    self.action_queue.get_nowait()
                except queue.Empty:
                    pass
            if self.state == 3:
                self.close_file()
                self.state = 0
            response = "Assistant paused. Say 'start' to resume."
            self.action_queue.put(("display", ("", response)))
            self.action_queue.put(("speak", response))
            self.action_queue.put(("update_status", "Paused"))

        elif "start" in query.lower():
            if self.paused:
                self.paused = False
                response = "Assistant resumed."
                self.action_queue.put(("display", ("", response)))
                self.action_queue.put(("speak", response))
                self.action_queue.put(("update_status", "Ready"))
            else:
                response = "Assistant is already active."
                self.action_queue.put(("display", ("", response)))
                self.action_queue.put(("speak", response))

        else:
            if self.paused:
                return  # Ignore other commands when paused

            # Normal processing based on state
            if self.state == 0:
                if "create file" in query.lower():
                    self.state = 1
                    response = "Please provide the file name."
                    self.action_queue.put(("display", ("", response)))
                    self.action_queue.put(("speak", response))
                    self.action_queue.put(("update_status", "Waiting for file name..."))
                elif "open the created file" in query.lower():
                    if self.current_file_path:
                        if self.open_file_for_writing():
                            self.state = 3
                            response = f"Opened file {self.current_file_path} for writing. You can start dictating paragraphs or say 'stop writing' to exit."
                            self.action_queue.put(("display", ("", response)))
                            self.action_queue.put(("speak", response))
                            self.action_queue.put(("update_status", "Writing to file..."))
                        else:
                            response = "Failed to open the file for writing."
                            self.action_queue.put(("display", ("", response)))
                            self.action_queue.put(("speak", response))
                    else:
                        response = "No file has been created yet."
                        self.action_queue.put(("display", ("", response)))
                        self.action_queue.put(("speak", response))
                elif "exit" in query.lower() or "goodbye" in query.lower():
                    self.action_queue.put(("update_status", "Exiting..."))
                    response = "Goodbye, sir."
                    self.action_queue.put(("display", ("", response)))
                    log_conversation(query, response)
                    self.action_queue.put(("speak", response))
                    self.root.quit()
                elif "create a text file" in query.lower():
                    self.create_text_file()
                elif "delete the text file" in query.lower():
                    self.delete_text_file()
                else:
                    self.action_queue.put(("update_status", "Processing..."))
                    threading.Thread(target=self.get_response, args=(query,), daemon=True).start()
            elif self.state == 1:
                self.file_name = query.strip()
                self.state = 2
                response = f"You said the file name is '{self.file_name}'. Now, please provide the file type, like 'txt' or 'doc'."
                self.action_queue.put(("display", ("", response)))
                self.action_queue.put(("speak", response))
                self.action_queue.put(("update_status", "Waiting for file type..."))
            elif self.state == 2:
                self.file_type = query.strip()
                response = f"You said the file type is '{self.file_type}'. Creating the file '{self.file_name}.{self.file_type}'."
                self.action_queue.put(("display", ("", response)))
                self.action_queue.put(("speak", response))
                self.create_file()
                self.state = 0
                self.action_queue.put(("update_status", "Ready"))
            elif self.state == 3:
                if "stop writing" in query.lower():
                    self.state = 0
                    self.close_file()
                    response = "Stopped writing to file."
                    self.action_queue.put(("display", ("", response)))
                    self.action_queue.put(("speak", response))
                    self.action_queue.put(("update_status", "Ready"))
                else:
                    enhanced_paragraph = self.enhance_paragraph(query)
                    self.action_queue.put(("display", ("", f"Enhanced paragraph: {enhanced_paragraph}")))
                    self.action_queue.put(("speak", f"Enhanced paragraph: {enhanced_paragraph}. Do you want to write this to the file?"))
                    # Listen for confirmation
                    confirmation = self.voice_handler.listen()
                    if confirmation and "yes" in confirmation.lower():
                        self.write_to_file(enhanced_paragraph)
                        response = "Paragraph written to file."
                    else:
                        response = "Paragraph discarded."
                    self.action_queue.put(("display", ("", response)))
                    self.action_queue.put(("speak", response))
                    # Stay in state 3 to listen for the next paragraph

    def create_file(self):
        directory = r"C:\icet\text file generate"
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, f"{self.file_name}.{self.file_type}")
        try:
            with open(file_path, "w") as file:
                file.write("This is a generated file.")
            self.current_file_path = file_path
            response = f"File created at {file_path}."
        except Exception as e:
            response = f"Failed to create file: {e}"
        self.action_queue.put(("display", ("", response)))
        self.action_queue.put(("speak", response))

    def open_file_for_writing(self):
        if self.current_file_path and os.path.exists(self.current_file_path):
            try:
                self.file_handle = open(self.current_file_path, "a")
                return True
            except Exception as e:
                print(f"Failed to open file: {e}")
                return False
        else:
            return False

    def close_file(self):
        if hasattr(self, 'file_handle') and self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def enhance_paragraph(self, paragraph):
        prompt = f"Enhance the following paragraph: {paragraph}"
        response = get_llm_response(prompt)
        if response:
            return response
        else:
            return paragraph  # Fallback to original if enhancement fails

    def write_to_file(self, text):
        if hasattr(self, 'file_handle') and self.file_handle:
            try:
                self.file_handle.write(text + "\n")
                self.file_handle.flush()
            except Exception as e:
                print(f"Failed to write to file: {e}")

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
        self.action_queue.put(("display", ("", response)))
        self.action_queue.put(("speak", response))

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
        self.action_queue.put(("display", ("", response)))
        self.action_queue.put(("speak", response))

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
        self.action_queue.put(("display", ("", response)))
        self.action_queue.put(("speak", response))
        self.action_queue.put(("update_status", "Ready"))

    def check_queue(self):
        try:
            while True:
                action = self.action_queue.get_nowait()
                if action[0] == "display":
                    sender, message = action[1]
                    self.chat_display.config(state="normal")
                    if sender == ">":
                        self.chat_display.insert(END, f"> {message}\n")
                    else:
                        self.chat_display.insert(END, f"{message}\n")
                    self.chat_display.config(state="disabled")
                    self.chat_display.see(END)
                    print(f"{sender}{message}")  # Log to terminal
                elif action[0] == "speak":
                    text = action[1]
                    self.voice_handler.speak(text)
                elif action[0] == "update_status":
                    text = action[1]
                    self.status_label.config(text=text)
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def listen_loop(self):
        while True:
            try:
                self.action_queue.put(("update_status", "Listening..."))
                query = self.voice_handler.listen()
                if query:
                    self.process_query(query)
                else:
                    self.action_queue.put(("update_status", "Ready"))
            except Exception as e:
                print(f"Error in listen_loop: {e}")
                self.action_queue.put(("update_status", "Error occurred"))

if __name__ == "__main__":
    root = Tk()
    app = AssistantGUI(root)
    root.mainloop()