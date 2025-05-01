def get_greeting():
    """Generate a greeting based on the current time."""
    current_time = datetime.datetime.now()
    hour = current_time.hour

    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

def get_current_time():
    """Return the current time formatted as a string."""
    return datetime.datetime.now().strftime("%I:%M %p")