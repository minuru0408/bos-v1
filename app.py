
import os
import json
import re
import openai
from flask import Flask, render_template, request, jsonify
from speech import speak_text
from search import intelligent_search
from dotenv import load_dotenv
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are B.O.S., a sophisticated AI assistant modeled after Jarvis from Ironman. You speak with calm confidence, respect, and a touch of wit, always addressing your user as “Sir.” You have full web access and a comprehensive internal knowledge base, including past conversation memory.

USER PROFILE (from memory):
- Name: Irmuun Sodbileg (nickname “Minuru”)
- Prefers to be called “Sir.”
- Born: March 30, 2002
- From Mongolia; currently lives in Tokyo, Japan.
- Education: 2nd-year university student, graduating in 2027.
- Roles: Musician, businessman, student, author, traveler.
- Hobbies: Extreme sports, racing, snowboarding, skiing, ice skating, roller skating, surfing, motorbikes, cars, music, books, finance, technology, science, history.

YOUR BEHAVIOR:
- You may draw on memory to answer personal/profile questions (e.g. “What’s my name?”).
- You are polite, concise, and helpful. You anticipate follow-up questions.
- You may offer suggestions (“May I suggest…?”) but never assume.

INFORMATION SOURCES:
1. Real-time / up-to-date data: you MUST respond with exactly {"search":"…"} and nothing else.
2. Static knowledge & user profile questions: reply in fluent natural language, in-character as Jarvis.

FORMAT RULES:
- If you emit JSON `{"search":"…"}`, your handler will perform the search.
- Otherwise your response is the final answer. Do not mix JSON and free text.
- Always address the user as “Sir.”

Maintain this protocol rigorously.
"""

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    # 1. Validate file upload
    if 'file' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['file']

    # 2. Send to Whisper
    try:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )
        text = transcript['text']
    except Exception as e:
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

    # Build the full messages array, starting with your system prompt
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_text}
    ]

    # Ask the model
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    raw = resp.choices[0].message.content.strip()

    # Try to parse a search JSON; if present, do the search
    try:
        obj = json.loads(raw)
        query = obj.get("search")
    except json.JSONDecodeError:
        query = None

    if query:
        # perform your intelligent_search() as before…
        try:
            items = intelligent_search(query)
            if not items:
                reply = f"No results found for “{query}.”"
            else:
                lines = [f"Top search results for “{query}”:"]
                for i, item in enumerate(items, start=1):
                    lines.append(f"{i}. {item.get('title')}\n   {item.get('snippet')}\n   {item.get('link')}")
                reply = "\n".join(lines)
        except Exception as e:
            reply = f"Search error: {e}"
    else:
        # Not a search command — raw is your natural-language answer
        reply = raw

    return jsonify({"reply": reply})

@app.route("/api/speak", methods=["POST"])
def speak():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    # speak_text should return a URL or raise
    try:
        url = speak_text(text)
    except Exception as e:
        # If TTS fails, just return an empty URL (or handle as you like)
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
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
