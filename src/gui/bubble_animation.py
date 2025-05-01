from tkinter import Canvas
import math
import random

class BubbleAnimation:
    def __init__(self, canvas):
        self.canvas = canvas
        self.bubble = None
        self.bubble_phase = random.uniform(0, 2 * math.pi)  # Random initial phase

    def create_bubble(self, x, y, size):
        """
        Creates a bubble at the specified position with the given size.
        """
        self.bubble = self.canvas.create_oval(
            x - size, y - size, x + size, y + size,
            fill="#6441a5", outline="", tags="bubble"
        )

    def animate(self, state):
        """
        Animates the bubble based on the current state.
        """
        if not self.bubble:
            # Create a default bubble if it doesn't exist
            self.create_bubble(300, 250, 50)  # Default position and size

        x1, y1, x2, y2 = self.canvas.coords(self.bubble)
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        base_size = (x2 - x1) / 2  # Current radius

        if state == "idle":
            size_variation = 5 * math.sin(self.bubble_phase)
            new_size = base_size + size_variation
            color = "#4b367c"  # Darker, less vibrant
        elif state == "listening":
            size_variation = 10 * math.sin(self.bubble_phase * 1.5)
            new_size = base_size + size_variation
            color = "#6441a5"  # Brighter
        elif state == "speaking":
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