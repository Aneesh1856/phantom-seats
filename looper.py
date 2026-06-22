import os
import time
from curl_cffi import requests
from dotenv import load_dotenv
import state

# Load environment variables
load_dotenv()
LOOP_INTERVAL = int(os.getenv("LOOP_INTERVAL", "300"))

def run_loop():
    print("Loop started!")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    while state.loop_running:
        try:
            # Using curl_cffi to spoof TLS fingerprint of a real browser
            response = requests.get(
                state.fnb_url,
                cookies=state.cookies,
                headers=headers,
                timeout=30,
                impersonate="chrome120"
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
