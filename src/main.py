from gui.assistant_gui import AssistantGUI
import tkinter as tk

def main():
    root = tk.Tk()
    gui = AssistantGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()