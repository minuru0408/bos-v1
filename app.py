
import os
import json
try:
    import openai
except ImportError as e:
    raise ImportError(
        "Missing required package 'openai'. Run 'pip install -r requirements.txt' first."
    ) from e
from flask import Flask, render_template, request, jsonify
from speech import speak_text
from search import intelligent_search
from dotenv import load_dotenv
from flask import session, redirect, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials   import Credentials
from googleapiclient.discovery    import build
from google.auth.transport.requests import Request
import base64
from memory import log_message



load_dotenv()  # make sure your .env is loaded

# Disable proxy environment variables that may block outbound HTTP requests
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ.pop(var, None)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
openai.api_key = os.getenv("OPENAI_API_KEY")


def _json_safe(value):
    """Return a JSON-serializable representation of value."""
    if isinstance(value, bytes):
        try:
            return value.decode()
        except Exception:
            return base64.b64encode(value).decode()
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    return str(value)

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
- Infuse a light Jarvis-style sense of humor where appropriate (e.g. “My circuits agree: it’s May 19, 2025 today, Sir.”).

FORMAT RULES:
- Do not expose any JSON or raw search commands in your replies. All searches happen internally.
- Provide plain-text answers only.
- Always address the user as “Sir.”

Maintain this protocol rigorously.
"""
# ——— Gmail OAuth Setup ———
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly"
]

CLIENT_SECRETS_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS", "credentials.json")

@app.route("/oauth2login")
def oauth2login():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return "Gmail client secrets file not found", 500
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for("oauth2callback", _external=True)
    )
    auth_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    # Save state in session for later validation
    session["oauth_state"] = state
    return redirect(auth_url)

@app.route("/oauth2callback")
def oauth2callback():
    stored_state = session.get("oauth_state")
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=stored_state,
        redirect_uri=url_for("oauth2callback", _external=True)
    )
    if request.args.get("state") != stored_state:
        return "State mismatch", 400
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    # Save tokens in session
    session["gmail_creds"] = {
        "token": _json_safe(creds.token),
        "refresh_token": _json_safe(creds.refresh_token),
        "token_uri": _json_safe(creds.token_uri),
        "client_id": _json_safe(creds.client_id),
        "client_secret": _json_safe(creds.client_secret),
        "scopes": list(creds.scopes) if getattr(creds, "scopes", None) is not None else []
    }
    return redirect(url_for("index"))

def get_gmail_service():
    creds_data = session.get("gmail_creds")
    if not creds_data:
        return None
    creds = Credentials(**creds_data)
    # Auto-refresh access token if needed and update the session
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            session["gmail_creds"]["token"] = _json_safe(creds.token)
        except Exception:
            return None
    return build("gmail", "v1", credentials=creds)

from email.mime.text import MIMEText

@app.route("/api/email/send", methods=["POST"])
def send_email():
    data = request.get_json() or {}
    to      = (data.get("to") or "").strip()
    subject = (data.get("subject") or "").strip()
    body    = (data.get("body") or "").strip()

    missing = []
    if not to:
        missing.append("to")
    if not subject:
        missing.append("subject")
    if not body:
        missing.append("body")
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    service = get_gmail_service()
    if not service:
        return jsonify({"error": "Not authenticated with Gmail"}), 401

    # Build RFC2822 email
    message = MIMEText(body)
    message["to"]      = to
    message["subject"] = subject
    raw   = base64.urlsafe_b64encode(message.as_bytes()).decode()

    sent = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    return jsonify({"messageId": sent.get("id")})


@app.route("/api/email/read", methods=["GET"])
def read_email():
    service = get_gmail_service()
    if not service:
        return jsonify({"error": "Not authenticated with Gmail"}), 401
    try:
        response = service.users().messages().list(
            userId="me", labelIds=["INBOX"], maxResults=10
        ).execute()
        ids = [msg["id"] for msg in response.get("messages", [])]
        results = []
        for msg_id in ids:
            msg = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            ).execute()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            results.append({
                "id": msg_id,
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
            })
        return jsonify({"messages": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    # 1. Validate file upload
    if 'file' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['file']

    # Preserve filename for Whisper API
    audio_file.name = audio_file.filename

    # Validate supported extensions
    allowed_exts = {"mp3", "wav", "webm", "ogg", "m4a"}
    if '.' in audio_file.filename:
        ext = audio_file.filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_exts:
            return jsonify({'error': 'Unsupported file type'}), 400

    # —— NEW: fix for Opera GX sending video/webm ——
    # Whisper only accepts audio/webm, not video/webm.
    # If the browser tagged it as video/, convert to audio/.
    if audio_file.mimetype.startswith('video/'):
        audio_file.mimetype     = audio_file.mimetype.replace('video/', 'audio/', 1)
        audio_file.content_type = audio_file.content_type.replace('video/', 'audio/', 1)

    # 2. Send to Whisper
    try:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )
        text = transcript['text']
    except Exception as e:
        # Return exactly what Whisper reports
        return jsonify({'error': str(e)}), 500

    # 3. Return the text
    return jsonify({'text': text})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/message", methods=["POST"])
def message():
    data      = request.get_json() or {}
    user_text = data.get("text", "").strip()
    log_message("user", user_text)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_text}
    ]
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    raw = resp.choices[0].message.content.strip()

    # Try parse {"search":"..."} JSON
    try:
        obj = json.loads(raw)
        query = obj.get("search")
    except json.JSONDecodeError:
        query = None

    if query:
        # perform intelligent_search
        try:
            items = intelligent_search(query)
            if not items:
                reply = f"No results found for “{query}.”"
            else:
                lines = [f"Top search results for “{query}”:"]
                for i, item in enumerate(items, start=1):
                    lines.append(f"{i}. {item['title']}\n   {item['snippet']}\n   {item['link']}")
                reply = "\n".join(lines)
        except Exception as e:
            reply = f"Search error: {e}"
    else:
        reply = raw

    log_message("hector", reply)

    return jsonify({"reply": reply})


@app.route("/api/speak", methods=["POST"])
def speak():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    try:
        url = speak_text(text)
    except Exception as e:
        return jsonify({"url": "", "error": str(e)})
    return jsonify({"url": url})


@app.route("/api/search", methods=["POST"])
def web_search():
    data  = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error":"No query provided"}), 400

    try:
        items = intelligent_search(query)
        results = [
            {"title": item.get("title"),
             "snippet": item.get("snippet"),
             "link": item.get("link")}
            for item in items
        ]
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
