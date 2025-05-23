import os
import json
import base64
from email.mime.text import MIMEText
from flask import Flask, request, redirect, url_for, session, render_template, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

CLIENT_SECRETS_FILE = os.getenv('GOOGLE_OAUTH_CLIENT_SECRETS', 'credentials.json')
TOKEN_FILE = os.getenv('GMAIL_TOKEN_FILE', 'gmail_token.json')
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]


def get_gmail_service():
    """Return an authenticated Gmail service or None."""
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, 'r') as f:
        data = json.load(f)
    creds = Credentials(**data)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        data['token'] = creds.token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(data, f)
    return build('gmail', 'v1', credentials=creds)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/oauth2login')
def oauth2login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(auth_url)


@app.route('/oauth2callback')
def oauth2callback():
    state = session.pop('state', None)
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
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


@app.route('/api/email/read', methods=['GET'])
def read_email():
    service = get_gmail_service()
    if not service:
        return jsonify({'error': 'Not authenticated with Gmail'}), 401
    result = []
    response = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=10).execute()
    ids = [m['id'] for m in response.get('messages', [])]
    for mid in ids:
        msg = service.users().messages().get(userId='me', id=mid, format='metadata', metadataHeaders=['From', 'Date', 'Subject']).execute()
        headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
        result.append({
            'id': mid,
            'from': headers.get('From', ''),
            'date': headers.get('Date', ''),
            'subject': headers.get('Subject', ''),
            'snippet': msg.get('snippet', '')
        })
    return jsonify({'messages': result})


@app.route('/api/email/send', methods=['POST'])
def send_email():
    data = request.get_json() or {}
    to = data.get('to', '').strip()
    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()
    if not (to and subject and body):
        return jsonify({'error': 'Missing to, subject or body'}), 400

    service = get_gmail_service()
    if not service:
        return jsonify({'error': 'Not authenticated with Gmail'}), 401

    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return jsonify({'messageId': sent.get('id')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv('PORT', 5002)))
