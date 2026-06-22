from datetime import datetime

# Shared State Variables
loop_running = False
session_valid = True
start_time = None
last_refreshed = None
fnb_url = ""
cookies = {}
seats = ""
showtime = ""
movie_date = ""
logs = []  # max 50 entries

def start_loop(new_fnb_url, new_cookies, new_seats, new_showtime, new_date):
    global fnb_url, cookies, seats, showtime, movie_date
    global loop_running, start_time

    fnb_url = new_fnb_url
    cookies = new_cookies
    seats = new_seats
    showtime = new_showtime
    movie_date = new_date

    loop_running = True
    start_time = datetime.now()

def stop_loop():
    global loop_running
    loop_running = False

def update_refreshed():
    global last_refreshed
    last_refreshed = datetime.now()

def set_session_valid(is_valid: bool):
    global session_valid
    session_valid = is_valid

def add_log(message: str):
    global logs
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    logs.append(log_entry)
    if len(logs) > 50:
        logs.pop(0)
        
    # Safely print without emojis for the console (Windows encoding fix)
    safe_print = log_entry.replace("✅", "[OK]").replace("❌", "[ERR]").replace("⚠️", "[WARN]")
    try:
        print(safe_print)
    except UnicodeEncodeError:
        print(safe_print.encode('ascii', 'ignore').decode('ascii'))

def get_uptime() -> str:
    if not start_time:
        return "Not started yet"
    delta = datetime.now() - start_time
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"

def get_last_refreshed() -> str:
    if not last_refreshed:
        return "Never"
    delta = datetime.now() - last_refreshed
    minutes = delta.seconds // 60 + (delta.days * 24 * 60)
    return f"{minutes} min ago"

def get_status() -> dict:
    return {
        "running": loop_running,
        "session_valid": session_valid,
        "uptime": get_uptime(),
        "last_refreshed": get_last_refreshed(),
        "seats": seats,
        "showtime": showtime,
        "date": movie_date,
        "logs": logs.copy()
    }
