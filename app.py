import os
from flask import Flask, request, render_template, jsonify, session
from dotenv import load_dotenv
import openai

# Helpers
from memory import log_message, load_memory
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
    # 1) Log the user message
    log_message("user", user_text)

    # 2) Build chat history: system prompt + recent memory + this new user message
    chat_history = [SYSTEM_PROMPT]
    memories = load_memory(limit=20)             # load last 20 lines
    chat_history.extend(memories)
    chat_history.append({"role": "user", "content": user_text})

    # 3) Ask OpenAI
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=chat_history
        )
        bot_text = resp.choices[0].message.content
    except Exception as e:
        app.logger.error(f"OpenAI error: {e}")
        bot_text = "⚠️ Sorry, I had trouble thinking. Please try again."

    # 4) Log and return the assistant reply
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
    # Use the PORT env var (set by Render), or default to 5001 locally
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)

