import os
from flask import Flask, request, render_template, jsonify, session
from dotenv import load_dotenv
from openai import OpenAI
from memory import log_message, load_memory  # ADD THIS IMPORT

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret")

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are B.O.S., a warm, witty digital butler. Always call the user 'sir' and speak like Jarvis from Iron Man."
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/message", methods=["POST"])
def message():
    user_text = request.json.get("text", "").strip()
    log_message("user", user_text)  # Now properly imported

    chat_history = [SYSTEM_PROMPT]
    chat_history.extend(load_memory(limit=20))
    chat_history.append({"role": "user", "content": user_text})

    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=chat_history
        )
        bot_text = resp.choices[0].message.content
    except Exception as e:
        app.logger.error(f"OpenAI error: {e}")
        bot_text = "⚠️ Sorry, I had trouble thinking. Please try again."

    log_message("assistant", bot_text)
    return jsonify({"reply": bot_text})

# ... rest of the code remains the same ...