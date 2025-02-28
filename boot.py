from flask import Flask, request
import requests
import subprocess
import time
import random
import json
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
sessions = {}  # Per-user session state
CODE_PATH = "/home/ubuntu/main.py"  # Adjust if your path differs

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

CHROME_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.google.com/"
}

@app.route('/', methods=['GET'])
def process_form():
    password = request.args.get('password', '')
    if password != ACCESS_PASSWORD:
        return json.dumps({"error": "Invalid passwordâ€”access denied"})

    user_id = request.remote_addr
    input_data = request.args.get('input', '')
    if not input_data:
        return json.dumps({"error": "No input provided"})

    try:
        params = dict(p.split('=') for p in request.query_string.decode().split('&') if p and p.split('=')[0] != 'password')
        cmd = params.get('cmd', '')
        url = params.get('url', '')
        data_str = params.get('data', '')
        value = params.get('value', '')
        question = params.get('question', '')
        new_code = params.get('new_code', '')  # For update task

        if user_id not in sessions:
            sessions[user_id] = requests.Session()
        session = sessions[user_id]
        headers = CHROME_HEADERS.copy()
        headers["User-Agent"] = random.choice(USER_AGENTS)
        session.headers.update(headers)

        if input_data == 'run':
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return json.dumps({"output": process.stdout or process.stderr})
        elif input_data == 'login':
            form_data = dict(item.split(':') for item in data_str.split(',') if item)
            time.sleep(random.uniform(2, 5))
            response = session.post(url, data=form_data, timeout=15)
            return json.dumps({"status": "Logged in" if response.ok else "Login failed", "code": response.status_code})
        elif input_data == 'submit':
            form_data = dict(item.split(':') for item in data_str.split(',') if item)
            time.sleep(random.uniform(2, 5))
            response = session.post(url, data=form_data, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            return json.dumps({"content": soup.get_text().strip()[:1000]})
        elif input_data == 'scrape':
            time.sleep(random.uniform(2, 5))
            response = session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            if 'mail.google.com' in url:
                messages = []
                for msg in soup.select('tr.zA'):
                    sender = msg.select_one('.yP, .zF')
                    subject = msg.select_one('.y6')
                    snippet = msg.select_one('.y2')
                    messages.append({
                        "sender": sender.get('email', sender.get_text(strip=True)) if sender else "Unknown",
                        "subject": subject.get_text(strip=True) if subject else "No subject",
                        "snippet": snippet.get_text(strip=True) if snippet else "No preview"
                    })
                return json.dumps({"messages": messages})
            return json.dumps({"content": soup.get_text().strip()[:1000]})
        elif input_data == 'calc':
            return json.dumps({"result": str(eval(value))})
        elif input_data == 'query':
            return json.dumps({"query": question})
        elif input_data == 'update':
            if not new_code:
                return json.dumps({"error": "No new code provided"})
            with open(CODE_PATH, 'w') as f:
                f.write(new_code)  # Write new code
            subprocess.run("pkill -f 'python grok4.py'; nohup python grok4.py &", shell=True)  # Restart Flask
            return json.dumps({"status": "Backend updated and restarted"})
        else:
            return json.dumps({"error": "Unknown command: " + input_data})
    except Exception as e:
        return json.dumps({"error": str(e)})

@app.route('/result', methods=['GET'])
def get_result():
    return json.dumps({"error": "Use /?input=...&password=ThisP@$$word"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
