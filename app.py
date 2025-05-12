import os
import openai
from flask import Flask, render_template, request, jsonify
from speech import speak_text
from search import intelligent_search

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/message", methods=["POST"])
def message():
    data      = request.get_json() or {}
    user_text = data.get("text", "").strip()
    lower     = user_text.lower()                  # <-- make sure we define `lower`

    # 1) If user asked to search the web
    trigger = "search the web for "
    if lower.startswith(trigger):
        # extract the actual search query
        query = user_text[len(trigger):].strip()
        if not query:
            return jsonify({"reply": "Please say what to search for."})

        try:
            items = intelligent_search(query)
            if not items:
                reply = f"No results found for “{query}.”"
            else:
                # Format the top results into a single reply string
                lines = ["Top search results:"]
                for i, item in enumerate(items, start=1):
                    lines.append(f"{i}. {item.get('title')}")
                    lines.append(f"   {item.get('snippet')}")
                    lines.append(f"   Link: {item.get('link')}")
                reply = "\n".join(lines)
        except Exception as e:
            reply = f"Search error: {e}"

        return jsonify({"reply": reply})

    # 2) Otherwise, normal chat via OpenAI
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":user_text}]
        )
        bot_reply = resp.choices[0].message.content
    except Exception as e:
        bot_reply = f"Chat error: {e}"

    return jsonify({"reply": bot_reply})

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
