from flask import Flask, request, render_template_string
import requests
import datetime
import json
import os
import re

app = Flask(__name__)

LOG_FILE = "logs.txt"

TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Visitor Logs</title>
<style>
body { font-family: Arial; padding:20px; max-width:900px; margin:auto; }
table { width:100%; border-collapse: collapse; }
th, td { border:1px solid #ccc; padding:8px; text-align:left; }
th { background:#f4f4f4; }
pre { white-space: pre-wrap; word-wrap: break-word; }
</style>
</head>
<body>
<h2>All Visitors (Educational Test)</h2>
<table>
<tr>
<th>#</th>
<th>Timestamp</th>
<th>IP</th>
<th>City</th>
<th>Region</th>
<th>Country</th>
<th>ISP</th>
<th>Device Info</th>
<th>User-Agent</th>
</tr>
{% for i, row in enumerate(all_entries, start=1) %}
<tr>
<td>{{i}}</td>
<td>{{row.timestamp}}</td>
<td>{{row.ip}}</td>
<td>{{row.city}}</td>
<td>{{row.region}}</td>
<td>{{row.country}}</td>
<td>{{row.isp}}</td>
<td>{{row.device}}</td>
<td><pre>{{row.user_agent}}</pre></td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""

def parse_device(user_agent):
    ua = user_agent.lower()

    # Basic detection (safe)
    if "android" in ua:
        match = re.search(r'android\s([\d\.]+)', ua)
        version = match.group(1) if match else "Unknown"
        return f"Android (Version {version})"

    if "iphone" in ua:
        return "iPhone (iOS)"

    if "ipad" in ua:
        return "iPad (iOS)"

    if "windows" in ua:
        return "Windows PC"

    if "macintosh" in ua:
        return "MacOS Device"

    return "Unknown Device"

@app.route('/')
def log_request():

    # Get real IP
    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or "0.0.0.0"
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    user_agent = request.headers.get("User-Agent", "Unknown")
    device = parse_device(user_agent)

    # Get geolocation from ipinfo (more accurate)
    try:
        geo = requests.get(f"https://ipinfo.io/{ip}/json").json()
        city = geo.get("city", "Unknown")
        region = geo.get("region", "Unknown")
        country = geo.get("country", "Unknown")
        isp = geo.get("org", "Unknown")
    except:
        city = region = country = isp = "Unknown"

    # Build entry
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "ip": ip,
        "city": city,
        "region": region,
        "country": country,
        "isp": isp,
        "device": device,
        "user_agent": user_agent
    }

    # Save to log file
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except:
        pass

    # Read logs
    all_entries = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE", "r") as f:
            for line in f:
                try:
                    all_entries.append(json.loads(line))
                except:
                    continue

    return render_template_string(TEMPLATE, all_entries=all_entries, enumerate=enumerate)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
