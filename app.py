import os
import json
import openai
from flask import Flask, render_template, request, jsonify
from speech import speak_text
from search import intelligent_search

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are B.O.S., an AI assistant with web access. 
- If the user asks for information that requires up-to-date facts (current time, weather, stock prices, recent news, etc.), you MUST respond with exactly:
{"search":"<what to search on the web>"}
and nothing else.
- If the user’s request can be answered from your own knowledge (jokes, explanations, definitions), reply in plain text.
"""

@app.route("/api/message", methods=["POST"])
def message():
    data      = request.get_json() or {}
    user_text = data.get("text", "").strip()

    # 1) Ask the LLM whether to search or answer directly
    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": user_text}
    ]
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    raw = chat.choices[0].message.content.strip()

    # 2) Try parsing JSON {"search": "..."} 
    try:
        obj = json.loads(raw)
        query = obj.get("search")
    except json.JSONDecodeError:
        query = None

    # 3a) If the model requested a search, do it
    if query:
        try:
            items = intelligent_search(query)
            if not items:
                reply = f"No results found for “{query}.”"
            else:
                lines = [f"Top search results for “{query}”:"]
                for i, item in enumerate(items, start=1):
                    title   = item.get("title")
                    link    = item.get("link")
                    snippet = item.get("snippet")
                    lines.append(f"{i}. {title}\n   {snippet}\n   {link}")
                reply = "\n".join(lines)
        except Exception as e:
            reply = f"Search error: {e}"

    # 3b) Otherwise, treat raw as the final answer
    else:
        reply = raw

    return jsonify({"reply": reply})

@app.route("/api/speak", methods=["POST"])
def speak():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    url  = speak_text(text)
    return jsonify({"url": url})

# … your /api/search route can remain if you want standalone access …

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)

