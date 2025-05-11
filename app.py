from flask import Flask, request, jsonify
import os
import openai

app = Flask(__name__)

# Your existing Whisper-based transcribe_audio in speech.py:
from speech import transcribe_audio

@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No audio file uploaded"}), 400

    # Save raw for debugging (optional)
    save_dir = os.path.join("static", "recordings")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f.filename)
    f.save(save_path)

    try:
        with open(save_path, "rb") as af:
            text = transcribe_audio(af)
        return jsonify({"text": text, "error": None})
    except Exception as e:
        app.logger.error(f"Transcribe error: {e}")
        return jsonify({"error": str(e)}), 500
