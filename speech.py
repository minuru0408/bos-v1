import os
import time
import requests

def speak_text(text):
    """
    Generate a TTS mp3 via ElevenLabs HTTP API and return its URL path.
    """
    api_key  = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ELEVENLABS_API_KEY")

    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability":0.5,"similarity_boost":0.8}
    }

    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()

    # Save MP3 so Flask can serve it
    tts_dir = os.path.join("static", "tts")
    os.makedirs(tts_dir, exist_ok=True)
    filename = f"tts_{int(time.time()*1000)}.mp3"
    path     = os.path.join(tts_dir, filename)
    with open(path, "wb") as f:
        f.write(resp.content)

    return f"/static/tts/{filename}"
