import os
import time
import requests
from dotenv import load_dotenv
import state

# Load environment variables
load_dotenv()
LOOP_INTERVAL = int(os.getenv("LOOP_INTERVAL", "300"))

def run_loop():
    print("Loop started!")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/91.0 Mobile Safari/537.36",
        "Accept": "text/html",
        "Accept-Language": "en-IN",
        "Referer": "https://in.bookmyshow.com"
    }

    while state.loop_running:
        try:
            response = requests.get(
                state.fnb_url,
                cookies=state.cookies,
                headers=headers,
                timeout=30
            )
            
            if "food-and-beverages" in response.url or "Grab a Bite" in response.text:
                state.update_refreshed()
                state.set_session_valid(True)
                state.add_log("✅ Seats re-held successfully!")
            elif response.status_code == 200:
                state.add_log(f"⚠️ Redirected to: {response.url}")
                state.set_session_valid(False)
            else:
                state.add_log(f"❌ Bad response: {response.status_code}")
                state.set_session_valid(False)
                
        except Exception as e:
            state.add_log(f"❌ Error: {e}")
            state.set_session_valid(False)

        # Wait for LOOP_INTERVAL seconds
        # Check loop_running every second so it stops immediately when released
        for _ in range(LOOP_INTERVAL):
            if not state.loop_running:
                break
            time.sleep(1)

    print("Loop stopped!")
