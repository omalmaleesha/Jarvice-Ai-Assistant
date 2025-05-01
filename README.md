# JARVIS Assistant

JARVIS is a modern voice assistant application that utilizes speech recognition and text-to-speech technologies to provide a seamless user experience. This project is designed to be modular, with separate components for the graphical user interface (GUI), voice handling, and utility functions.

## Features

- Voice recognition for user commands
- Text-to-speech capabilities for responses
- Animated speech bubble to indicate speaking status
- Conversation history logging
- Modular architecture for easy maintenance and enhancements

## Project Structure

```
jarvis-assistant
├── src
│   ├── gui
│   │   ├── __init__.py
│   │   ├── assistant_gui.py
│   │   └── bubble_animation.py
│   ├── voice
│   │   ├── __init__.py
│   │   ├── voice_handler.py
│   │   └── speech_recognition.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── conversation_logger.py
│   │   ├── llm_api.py
│   │   └── time_utils.py
│   ├── main.py
│   └── config.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/jarvis-assistant.git
   ```
2. Navigate to the project directory:
   ```
   cd jarvis-assistant
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python src/main.py
   ```
2. Follow the on-screen instructions to interact with the assistant.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.