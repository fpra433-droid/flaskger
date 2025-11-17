from flask import Flask, request, render_template_string
import requests
import datetime
import json

app = Flask(__name__)

# Simple HTML template that displays the captured data and saves it to localStorage
TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Test Logger</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
      body { font-family: Arial, sans-serif; padding: 18px; max-width: 800px; margin: auto; }
      pre { background:#f4f4f4; padding:12px; border-radius:6px; overflow:auto; }
      .badge { display:inline-block; padding:6px 10px; background:#eee; border-radius:8px; margin-right:6px; }
      button { padding:8px 12px; border-radius:6px; border:0; background:#2b7cff; color:white; }
    </style>
  </head>
  <body>
    <h2>Request captured (educational test)</h2>
    <p>Timestamp: <strong>{{data.timestamp}}</strong></p>

    <div>
      <span class="badge">IP</span><strong>{{data.ip}}</strong><br/>
      <span class="badge">City</span>{{data.city}} &nbsp;
      <span class="badge">Region</span>{{data.region}} &nbsp;
      <span class="badge">Country</span>{{data.country}}<br/>
      <span class="badge">ISP</span>{{data.isp}}<br/>
      <span class="badge">User-Agent</span><br/>
      <pre id="ua">{{data.user_agent}}</pre>
    </div>

    <h3>Parsed (simple)</h3>
    <pre id="parsed">{{parsed}}</pre>

    <p>
      <button id="saveLocal">Save this entry to my browser localStorage</button>
      <button id="showLocal">Show localStorage entries</button>
    </p>

    <h3>Local storage contents (browser)</h3>
    <pre id="localOut">(none yet)</pre>

    <script>
      // Data object injected from server
      const entry = {{data_json}};

      // Save to localStorage when user clicks
      document.getElementById('saveLocal').addEventListener('click', ()=>{
        let arr = JSON.parse(localStorage.getItem('test_logger_entries') || "[]");
        arr.push(entry);
        localStorage.setItem('test_logger_entries', JSON.stringify(arr));
        alert('Saved to this browser localStorage (' + arr.length + ' entries).');
      });

      document.getElementById('showLocal').addEventListener('click', ()=>{
        const raw = localStorage.getItem('test_logger_entries') || "[]";
        const out = JSON.stringify(JSON.parse(raw), null, 2);
        document.getElementById('localOut').textContent = out;
      });

      // auto-show current local storage
      document.getElementById('showLocal').click();
    </script>
  </body>
</html>
"""

def simple_parse_user_agent(ua: str):
    """
    Very simple, best-effort UA parsing for education:
    - Looks for common Android/iPhone patterns and extracts device model if present.
    - Not a replacement for a real UA parser library.
    """
    ua = ua or ""
    info = []
    if "Android" in ua:
        # find substring like 'Android 12; <device>'
        try:
            part = ua.split("Android",1)[1]
            # take up to the closing parenthesis
            if ")" in part:
                inside = part.split(")")[0]
                info.append("Android" + inside)
            else:
                info.append("Android")
        except:
            info.append("Android (unknown)")
    if "iPhone" in ua or "iPad" in ua:
        info.append("iOS device (iPhone/iPad)")
    # Browser
    if "Chrome/" in ua:
        info.append("Chrome")
    if "Safari/" in ua and "Chrome" not in ua:
        info.append("Safari")
    if "Firefox/" in ua:
        info.append("Firefox")
    return "; ".join(info) or "Unknown"

@app.route('/')
def log_request():
    # Get IP (respect X-Forwarded-For if present; Render and many hosts use it)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip and ',' in ip:
        ip = ip.split(',')[0].strip()

    ua = request.headers.get('User-Agent', '')

    # Geolocation via ipapi.co (public free endpoint; rate limits apply)
    geo = {}
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        if resp.status_code == 200:
            geo = resp.json()
    except Exception:
        geo = {}

    data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "ip": ip,
        "city": geo.get("city"),
        "region": geo.get("region"),
        "country": geo.get("country_name"),
        "isp": geo.get("org"),
        "user_agent": ua
    }

    # Save to server-side logs.txt (note: on Render this is ephemeral)
    try:
        with open("logs.txt", "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        # keep running even if file write fails
        print("Failed to write logs.txt:", e)

    parsed = simple_parse_user_agent(ua)

    # Render HTML page that both shows data and includes JS to save to browser localStorage
    return render_template_string(
        TEMPLATE,
        data=data,
        parsed=parsed,
        data_json=json.dumps(data)
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
