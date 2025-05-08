import os
from flask import Flask, request, render_template, jsonify, session
from dotenv import load_dotenv
import openai

# Helpers
from memory import log_message
from search import intelligent_search
from speech import transcribe_audio, speak_text

# 1) Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 2) Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret")

# 3) System prompt
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are B.O.S., a warm, witty digital butler. "
        "Always call the user ‘sir’ and speak like Jarvis from Iron Man."
    )
}

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/api/message", methods=["POST"])
def message():
    user_text = request.json.get("text", "").strip()
    # Log user message
    log_message("user", user_text)

    # Build or retrieve chat history in session
    session.setdefault("chat", [SYSTEM_PROMPT])
    session["chat"].append({"role": "user", "content": user_text})

    # Ask OpenAI
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=session["chat"]
    )
    bot_text = resp.choices[0].message.content

    # Save and return
    session["chat"].append({"role": "assistant", "content": bot_text})
    log_message("assistant", bot_text)
    return jsonify({"reply": bot_text})

@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    audio = request.files['file']
    text = transcribe_audio(audio)
    return jsonify({"text": text})

@app.route("/api/speak", methods=["POST"])
def speak():
    text = request.json.get("text", "")
    url = speak_text(text)
    return jsonify({"url": url})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)

