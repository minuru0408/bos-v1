import os
import openai
from flask import Flask, render_template, request, jsonify
from speech import speak_text
from search import intelligent_search   # <-- new import

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Configure OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/message", methods=["POST"])
def message():
    data = request.get_json() or {}
    user_text = data.get("text", "")
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":user_text}]
    )
    bot_reply = resp.choices[0].message.content
    return jsonify({"reply": bot_reply})

@app.route("/api/speak", methods=["POST"])
def speak():
    data = request.get_json() or {}
    text = data.get("text", "")
    url = speak_text(text)
    return jsonify({"url": url})

# —— New web-search endpoint —— 
@app.route("/api/search", methods=["POST"])
def web_search():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "No search query provided"}), 400

    try:
        items = intelligent_search(query)
        # Simplify each item to title, snippet, and link
        results = [
            {
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link")
            }
            for item in items
        ]
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
