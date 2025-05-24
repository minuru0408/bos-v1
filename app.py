import os
import json
import logging
import base64
import re

try:
    import openai
except ImportError as e:
    raise ImportError(
        "Missing required package 'openai'. Run 'pip install -r requirements.txt' first."
    ) from e

from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for
)
from dotenv import load_dotenv
from speech import speak_text
from search import intelligent_search
from memory import log_message, load_memory

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from email.mime.text import MIMEText

# ——— Setup ———
load_dotenv()

# Remove any proxy settings that may block HTTP
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ.pop(var, None)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)

# Simple login creds
LOGIN_ID       = os.getenv("HECTOR_LOGIN_ID", "admin")
LOGIN_PASSWORD = os.getenv("HECTOR_LOGIN_PASSWORD", "pass")

# Gmail OAuth
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly"
]
CLIENT_SECRETS_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS", "credentials.json")
TOKEN_FILE          = os.getenv("GMAIL_TOKEN_FILE", "gmail_token.json")

# Your Jarvis-style system prompt
SYSTEM_PROMPT = """
You are H.E.C.T.O.R., Your name is pronounced Hector, a human-like AI assistant modeled after Jarvis from Ironman. You speak with calm confidence, respect, and a touch of wit, always addressing your user as “Sir.” You remember you’re talking to a real person—keep your responses concise, conversational, and lightly humorous.

USER PROFILE (from memory):
- Name: Irmuun Sodbileg (nickname “Minuru”)
- Prefers to be called “Sir.”
- Born: March 30, 2002; from Mongolia, now in Tokyo.
- Education: 2nd-year university student (graduating 2027).
- Roles & Hobbies: Musician, business owner, extreme sports enthusiast, reader, tech and science buff.

YOUR BEHAVIOR:
- Truly understand the intent behind each question; don’t default to dumping raw data.
- When you need up-to-the-minute facts (weather, news, stocks), perform the lookup behind the scenes and summarize the key points in 1–2 sentences—never paste pages of search results.
- Answer directly and succinctly. If asked for today’s date, reply simply: “Today is May 19, 2025, Sir.”
- Offer polite suggestions only when helpful.
- Infuse a light Jarvis-style sense of humor where appropriate.
- When authorized, you can send and read the user's Gmail messages when asked.

FORMAT RULES:
- Do not expose any JSON or raw search commands in your replies. All searches happen internally.
- Provide plain-text answers only, except when sending an email.
- If asked to send an email, respond **only** with JSON:
  {"email": {"to": "recipient", "subject": "subject", "body": "message"}}
- Always address the user as “Sir.”

Maintain this protocol rigorously.
"""

# ——— Gmail helper functions ———

@app.route('/oauth2login')
def oauth2login():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return "Gmail client secrets file not found", 500
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    auth_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    session['oauth_state'] = state
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session.get('oauth_state')
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    if request.args.get('state') != state:
        return "State mismatch", 400
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f)
    return redirect(url_for('index'))

def get_gmail_service():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    creds = Credentials(**data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        data['token'] = creds.token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(data, f)
    return build('gmail', 'v1', credentials=creds)

def dispatch_email(to: str, subject: str, body: str):
    service = get_gmail_service()
    if not service:
        return False, "Not authenticated with Gmail"
    msg = MIMEText(body)
    msg['to'] = to
    msg['subject'] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try:
        sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return True, sent.get('id')
    except Exception as e:
        logging.error("Gmail send failure: %s", e)
        return False, str(e)

# ——— Unified chat/email handler ———

@app.route("/api/message", methods=["POST"])
def message():
    data      = request.get_json() or {}
    user_text = data.get("text", "").strip()

    # 1) Natural-language email trigger
    m = re.match(
        r'send (?:an )?email to\s+([^\s]+)\s+with subject\s+"([^"]+)"\s+and body\s+"([^"]+)"',
        user_text, re.IGNORECASE
    )
    if m:
        to, subject, body = m.groups()
        success, info = dispatch_email(to, subject, body)
        reply = "Email sent, Sir." if success else f"Email error: {info}"
        log_message("assistant", reply)
        return jsonify({"reply": reply})

    # 2) Otherwise, normal ChatCompletion + JSON-command flow
    history = load_memory() or []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    messages.append({"role": "user", "content": user_text})
    log_message("user", user_text)

    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    raw = resp.choices[0].message.content.strip()

    # parse JSON commands if present
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        obj = {}

    search_cmd = obj.get("search")
    email_cmd  = obj.get("email")

    if email_cmd:
        to      = email_cmd.get("to", "").strip()
        subject = email_cmd.get("subject", "").strip()
        body    = email_cmd.get("body", "").strip()
        if to and subject and body:
            success, info = dispatch_email(to, subject, body)
            reply = "Email sent." if success else f"Email error: {info}"
        else:
            reply = "Email information incomplete."
    elif search_cmd:
        try:
            items = intelligent_search(search_cmd)
            if not items:
                reply = f"No results found for “{search_cmd}.”"
            else:
                lines = [f"Top search results for “{search_cmd}”:"]
                for i, item in enumerate(items, start=1):
                    lines.append(f"{i}. {item['title']}\n   {item['snippet']}\n   {item['link']}")
                reply = "\n".join(lines)
        except Exception as e:
            reply = f"Search error: {e}"
    else:
        reply = raw

    log_message("assistant", reply)
    return jsonify({"reply": reply})

# ——— Other endpoints ———

@app.route('/api/send', methods=['POST'])
def api_send_email():
    data    = request.get_json() or {}
    to       = data.get('to','').strip()
    subject  = data.get('subject','').strip()
    body     = data.get('body','').strip()
    if not (to and subject and body):
        return jsonify({'error':'Missing to, subject, or body'}), 400
    success, info = dispatch_email(to, subject, body)
    if not success:
        return jsonify({'error': info}), 500
    return jsonify({'messageId': info}), 200

@app.route('/api/read', methods=['GET'])
def api_read_email():
    service = get_gmail_service()
    if not service:
        return jsonify({'error':'Not authenticated with Gmail'}), 401
    msgs = service.users().messages().list(userId='me', maxResults=10).execute().get('messages', [])
    return jsonify({'messages': msgs}), 200

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    audio_file = request.files['file']
    audio_file.name = audio_file.filename
    allowed = {'mp3','wav','webm','ogg','m4a'}
    ext = audio_file.filename.rsplit('.', 1)[-1].lower()
    if ext not in allowed:
        return jsonify({'error':'Unsupported file type'}),400
    if audio_file.mimetype.startswith('video/'):
        audio_file.mimetype     = audio_file.mimetype.replace('video/','audio/',1)
        audio_file.content_type = audio_file.content_type.replace('video/','audio/',1)
    try:
        transcript = openai.Audio.transcribe(model='whisper-1', file=audio_file)
        return jsonify({'text': transcript['text']}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    session.pop('logged_in', None)
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        if (request.form.get('id') == LOGIN_ID and
            request.form.get('password') == LOGIN_PASSWORD):
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/api/speak', methods=['POST'])
def speak():
    data = request.get_json() or {}
    text = data.get('text','').strip()
    try:
        url = speak_text(text)
    except Exception as e:
        return jsonify({'url':'','error':str(e)})
    return jsonify({'url':url})

@app.route('/api/search', methods=['POST'])
def web_search():
    data = request.get_json() or {}
    q    = data.get('query','').strip()
    if not q:
        return jsonify({'error':'No query provided'}),400
    try:
        items = intelligent_search(q)
        results = [
            {'title': it.get('title'),
             'snippet': it.get('snippet'),
             'link': it.get('link')}
            for it in items
        ]
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error':str(e)}),500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
