from flask import Flask, request, render_template_string
import requests
import datetime
import json
import os

app = Flask(__name__)

LOG_FILE = "logs.txt"

TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Visitor Logs</title>
<style>
body { font-family: Arial; padding:20px; max-width:800px; margin:auto; }
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
<th>Device</th>
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

def detect_device(ua):
    ua = ua.lower()

    brands = {
        "samsung": ["samsung", "sm-"],
        "apple": ["iphone", "ipad"],
        "xiaomi": ["mi ", "redmi", "xiaomi"],
        "oppo": ["oppo"],
        "vivo": ["vivo"],
        "realme": ["realme"],
        "huawei": ["huawei", "honor"],
        "oneplus": ["oneplus"],
        "infinix": ["infinix"],
        "tecno": ["tecno"]
    }

    for brand, keywords in brands.items():
        for k in keywords:
            if k in ua:
                return brand.capitalize()

    return "Unknown"

@app.route('/')
def log_request():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or "0.0.0.0"
    if "," in ip:
        ip = ip.split(",")[0].strip()

    ua = request.headers.get("User-Agent", "Unknown")

    geo = {}
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        if resp.status_code == 200:
            geo = resp.json()
    except:
        pass

    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "ip": ip,
        "city": geo.get("city", "Unknown"),
        "region": geo.get("region", "Unknown"),
        "country": geo.get("country_name", "Unknown"),
        "isp": geo.get("org", "Unknown"),
        "device": detect_device(ua),
        "user_agent": ua
    }

    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except:
        print("Error writing logs")

    all_entries = []
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                for line in f:
                    try:
                        all_entries.append(json.loads(line))
                    except:
                        continue
    except:
        pass

    return render_template_string(TEMPLATE, all_entries=all_entries, enumerate=enumerate)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
