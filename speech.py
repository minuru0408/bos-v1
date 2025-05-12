# speech.py

import os
import time
import requests
import openai

# ——— Transcription (unchanged) ———
openai.api_key = os.getenv("OPENAI_API_KEY")

def transcribe_audio(audio_file):
    audio_file.seek(0)
    resp = openai.Audio.transcribe(
        model="gpt-4o-transcribe",    # or "whisper-1"
        file=audio_file,
        response_format="text"
    )
    return resp["text"]


# ——— TTS via ElevenLabs ———
def speak_text(text):
    # 1) Load & validate your ElevenLabs key
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ELEVENLABS_API_KEY environment variable")

    # 2) Voice ID (must match one you own in ElevenLabs)
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
    if not voice_id:
        raise RuntimeError("Missing ELEVENLABS_VOICE_ID environment variable")

    # 3) Correct endpoint (note the /stream suffix)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }

    # 4) POST to ElevenLabs
    response = requests.post(url, json=payload, headers=headers)

    # 5) If unauthorized or any other 4xx/5xx, log the body
    if not response.ok:
        body = response.text
        raise RuntimeError(f"ElevenLabs TTS error {response.status_code}: {body}")

    # 6) Save the returned MP3 so Flask can serve it
    tts_dir = os.path.join("static", "tts")
    os.makedirs(tts_dir, exist_ok=True)
    filename = f"tts_{int(time.time() * 1000)}.mp3"
    path = os.path.join(tts_dir, filename)
    with open(path, "wb") as f:
        f.write(response.content)

    return f"/static/tts/{filename}"
