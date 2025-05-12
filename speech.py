# speech.py

import os
import time
import requests
import openai 

client = openai(api_key=os.getenv("OPENAI_API_KEY"))
transcription = client.audio.transcriptions.create(
  model="gpt-4o-transcribe",
  file=audio_file
)
print(transcription.text)

def speak_text(text):
    """
    Generate TTS mp3 via ElevenLabs HTTP API and return its URL path.
    (Unchanged from before.)
    """
    api_key  = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVEN_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")  # George

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": api_key,
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

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    # Save the MP3 under static/tts so Flask can serve it
    tts_dir = os.path.join("static", "tts")
    os.makedirs(tts_dir, exist_ok=True)
    filename = f"tts_{int(time.time() * 1000)}.mp3"
    filepath = os.path.join(tts_dir, filename)
    with open(filepath, "wb") as f:
        f.write(response.content)

    return f"/static/tts/{filename}"
