import os
import json
import threading
from flask import Flask, request, session, redirect, url_for, render_template_string, jsonify
from dotenv import load_dotenv

import state
import looper

load_dotenv()
PIN = os.getenv("PIN")

app = Flask(__name__)
# Generate a secret key if not provided, for session management
app.secret_key = os.urandom(24)

# --- INLINE CSS ---
BASE_CSS = """
body {
    background-color: #0A0A0A;
    color: #FFFFFF;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
}
.container {
    width: 100%;
    max-width: 500px;
}
h1, h2, h3 { text-align: center; margin-top: 0; }
.card {
    background: #1A1A1A;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.5);
}
.btn {
    display: block;
    width: 100%;
    padding: 15px;
    border: none;
    border-radius: 8px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    margin-top: 10px;
    text-align: center;
    text-decoration: none;
    box-sizing: border-box;
}
.btn-primary { background: #28a745; color: white; }
.btn-danger { background: #dc3545; color: white; }
.input-field {
    width: 100%;
    padding: 12px;
    margin: 8px 0 20px;
    background: #2A2A2A;
    border: 1px solid #444;
    border-radius: 6px;
    color: white;
    font-size: 16px;
    box-sizing: border-box;
}
.label { font-weight: bold; margin-bottom: 5px; display: block; color: #ccc; }
.error { color: #ff6b6b; text-align: center; margin-bottom: 15px; font-weight: bold; }
"""

# --- HTML TEMPLATES ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🎭 PHANTOM SEATS</title>
    <style>""" + BASE_CSS + """</style>
</head>
<body>
    <div class="container" style="margin-top: 10vh;">
        <h1>🎭 PHANTOM SEATS</h1>
        <div class="card">
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST" action="/login">
                <label class="label">Enter 4-Digit PIN</label>
                <input class="input-field" type="number" name="pin" placeholder="****" required style="text-align:center; font-size: 24px; letter-spacing: 10px;">
                <button class="btn btn-primary" type="submit">ENTER</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

SETUP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🎭 Setup Phantom Booking</title>
    <style>""" + BASE_CSS + """
    .instructions {
        background: #222;
        padding: 15px;
        border-left: 4px solid #007bff;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 14px;
        line-height: 1.6;
        color: #eee;
    }
    textarea.input-field { height: 120px; resize: vertical; font-family: monospace; font-size: 12px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>🎭 Setup Phantom Booking</h2>
        <div class="instructions">
            <strong>Instructions:</strong><br>
            1. Open BMS on your browser<br>
            2. Login and select your movie<br>
            3. Select seats &rarr; Pay &rarr; Accept T&C<br>
            4. STOP at Food & Beverages page<br>
            5. Copy the page URL<br>
            6. Install Cookie Editor extension<br>
            7. Click Export &rarr; copy the JSON<br>
            8. Paste both above and hit START!
        </div>
        <div class="card">
            <form method="POST" action="/start">
                <label class="label">Paste Food & Beverages page URL from BMS</label>
                <input class="input-field" type="url" name="url" placeholder="https://in.bookmyshow.com/..." required>
                
                <label class="label">Paste cookies JSON from Cookie Editor extension</label>
                <textarea class="input-field" name="cookies" placeholder='[{"name": "...", "value": "..."}, ...]' required></textarea>
                
                <label class="label">Seats (e.g. B12, B13)</label>
                <input class="input-field" type="text" name="seats" placeholder="B12, B13" required>
                
                <label class="label">Show Time</label>
                <input class="input-field" type="text" name="showtime" placeholder="11:55 AM" required>
                
                <label class="label">Movie Date</label>
                <input class="input-field" type="date" name="date" required>
                
                <button class="btn btn-primary" style="background:#28a745; font-size: 20px; padding: 18px; margin-top: 15px;" type="submit">🚀 START PHANTOM</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

STATUS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🎭 PHANTOM SEATS</title>
    <style>""" + BASE_CSS + """
    .badge {
        font-size: 22px;
        font-weight: bold;
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .badge.held { 
        background: rgba(40, 167, 69, 0.15); 
        border: 2px solid #28a745; 
        color: #28a745;
        box-shadow: 0 0 20px rgba(40,167,69,0.3); 
    }
    .badge.released { 
        background: rgba(220, 53, 69, 0.15); 
        border: 2px solid #dc3545; 
        color: #dc3545;
    }
    .stats-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
        font-size: 13px;
        background: #222;
        padding: 12px 5px;
        border-radius: 8px;
    }
    .stats-row div { text-align: center; flex: 1; border-right: 1px solid #444; }
    .stats-row div:last-child { border-right: none; }
    .log-box {
        background: #000;
        padding: 12px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 13px;
        height: 180px;
        overflow-y: auto;
        color: #ddd;
        border: 1px solid #333;
    }
    .log-entry { margin-bottom: 6px; border-bottom: 1px solid #222; padding-bottom: 6px; }
    .log-entry:last-child { border-bottom: none; }
    .log-success { color: #4CAF50; }
    .log-error { color: #f44336; }
    .log-warn { color: #ffeb3b; }
    .btn-small { 
        padding: 12px 20px; 
        font-size: 14px; 
        background: #333; 
        color: #aaa;
        width: auto; 
        display: inline-block; 
        margin-top: 10px;
    }
    .btn-small:hover { background: #444; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 PHANTOM SEATS</h1>
        
        <div class="card">
            <h3 style="color:#e0e0e0; margin-bottom: 5px;">🎬 {{ status.date }} - {{ status.showtime }}</h3>
            <p style="text-align:center; font-size: 20px; margin-top: 5px; margin-bottom: 20px;">
                Seats: <strong style="color: #fff;">{{ status.seats }}</strong>
            </p>
            
            <div id="status-badge" class="badge {% if status.running %}held{% else %}released{% endif %}">
                {% if status.running %}🟢 SEATS HELD 🔒{% else %}🔴 SEATS RELEASED 🔓{% endif %}
            </div>
            
            <div class="stats-row">
                <div><span style="color:#aaa;">Uptime</span><br><strong id="uptime" style="font-size: 15px; margin-top: 5px; display: block;">{{ status.uptime }}</strong></div>
                <div><span style="color:#aaa;">Refreshed</span><br><strong id="refreshed" style="font-size: 15px; margin-top: 5px; display: block;">{{ status.last_refreshed }}</strong></div>
                <div><span style="color:#aaa;">Session</span><br><strong id="session" style="font-size: 15px; margin-top: 5px; display: block;">{% if status.session_valid %}✅ Valid{% else %}⚠️ Expired{% endif %}</strong></div>
            </div>
            
            <button class="btn btn-danger" style="font-size:20px; padding: 18px; text-transform: uppercase; letter-spacing: 1px;" onclick="releaseSeats()">🔓 RELEASE SEATS</button>
        </div>

        <div class="card">
            <h4 style="margin-top: 0; color: #ccc;">Live Logs</h4>
            <div class="log-box" id="log-box">
                {% for log in status.logs[-10:] %}
                    <div class="log-entry
                        {% if '✅' in log %}log-success
                        {% elif '❌' in log %}log-error
                        {% elif '⚠️' in log %}log-warn{% endif %}
                    ">{{ log }}</div>
                {% endfor %}
            </div>
        </div>
        
        <div style="text-align: center;">
            <a href="/setup" class="btn btn-small">New Movie Setup</a>
        </div>
    </div>

    <script>
        function releaseSeats() {
            if(confirm("Release seats now? Make sure you're at the counter!")) {
                fetch('/release', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    if(data.success) location.reload();
                });
            }
        }

        function updateStatus() {
            fetch('/status')
            .then(r => r.json())
            .then(data => {
                document.getElementById('uptime').innerText = data.uptime;
                document.getElementById('refreshed').innerText = data.last_refreshed;
                document.getElementById('session').innerHTML = data.session_valid ? '✅ Valid' : '⚠️ Expired';
                
                const badge = document.getElementById('status-badge');
                if(data.running) {
                    badge.className = 'badge held';
                    badge.innerHTML = '🟢 SEATS HELD 🔒';
                } else {
                    badge.className = 'badge released';
                    badge.innerHTML = '🔴 SEATS RELEASED 🔓';
                }

                let logsHtml = '';
                const last10 = data.logs.slice(-10);
                last10.forEach(log => {
                    let c = '';
                    if(log.includes('✅')) c = 'log-success';
                    else if(log.includes('❌')) c = 'log-error';
                    else if(log.includes('⚠️')) c = 'log-warn';
                    logsHtml += `<div class="log-entry ${c}">${log}</div>`;
                });
                document.getElementById('log-box').innerHTML = logsHtml;
            });
        }
        
        // Refresh stats every 30 seconds
        setInterval(updateStatus, 30000);
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if not state.loop_running:
        return redirect(url_for("setup"))
    return render_template_string(STATUS_HTML, status=state.get_status())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("pin") == PIN:
            session["logged_in"] = True
            return redirect(url_for("index"))
        return render_template_string(LOGIN_HTML, error="Wrong PIN!")
    return render_template_string(LOGIN_HTML)

@app.route("/setup")
def setup():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template_string(SETUP_HTML)

@app.route("/start", methods=["POST"])
def start():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    
    url = request.form.get("url")
    cookies_str = request.form.get("cookies", "[]")
    seats = request.form.get("seats")
    showtime = request.form.get("showtime")
    date = request.form.get("date")
    
    try:
        cookies_list = json.loads(cookies_str)
        # Convert cookie editor list format to dict for requests library
        cookies_dict = {c["name"]: c["value"] for c in cookies_list if "name" in c and "value" in c}
    except Exception as e:
        print("Error parsing cookies:", e)
        cookies_dict = {}

    state.start_loop(url, cookies_dict, seats, showtime, date)
    
    # Start the looper in a background thread
    threading.Thread(target=looper.run_loop, daemon=True).start()
    
    return redirect(url_for("index"))

@app.route("/release", methods=["POST"])
def release():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    state.stop_loop()
    return jsonify({"success": True})

@app.route("/status")
def status_endpoint():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(state.get_status())

@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})
