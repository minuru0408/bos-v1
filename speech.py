import os
import openai
import time
import requests

def transcribe_audio(audio_file):
    audio_file.seek(0)
    resp = openai.Audio.transcribe("whisper-1", file=audio_file)
    return resp["text"]

def speak_text(text):
    api_key  = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVEN_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")  # George

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_monolingual_v1",
               "voice_settings": {"stability":0.5,"similarity_boost":0.8}}

    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()

    tts_dir = os.path.join("static", "tts")
    os.makedirs(tts_dir, exist_ok=True)
    filename = f"tts_{int(time.time()*1000)}.mp3"
    path = os.path.join(tts_dir, filename)
    with open(path, "wb") as f:
        f.write(resp.content)
    return f"/static/tts/{filename}"
