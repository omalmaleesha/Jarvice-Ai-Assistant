from datetime import datetime

def get_greeting_message():
    """
    Returns a greeting message based on the current time of day.
    """
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good morning!"
    elif 12 <= current_hour < 18:
        return "Good afternoon!"
    elif 18 <= current_hour < 22:
        return "Good evening!"
    else:
        return "Hello!"

def get_current_time():
    """Return the current time formatted as a string."""
    return datetime.now().strftime("%I:%M %p")