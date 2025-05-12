import os
import openai
from flask import Flask, render_template, request, jsonify
from speech import speak_text

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Configure OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/message", methods=["POST"])
def message():
    data = request.get_json()
    user_text = data.get("text", "")
    # Call ChatCompletion (GPT-4, GPT-3.5, etc.)
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":user_text}]
    )
    bot_reply = resp.choices[0].message.content
    return jsonify({"reply": bot_reply})

@app.route("/api/speak", methods=["POST"])
def speak():
    data = request.get_json()
    text = data.get("text", "")
    url = speak_text(text)
    return jsonify({"url": url})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
