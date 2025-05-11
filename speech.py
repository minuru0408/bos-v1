# speech.py

import os
from openai import OpenAI  # <-- new v2 client
import time
import requests

# Initialize the OpenAI client once, using your env var
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_file):
    """
    Send the uploaded audio blob to OpenAI's GPT-4o-transcribe model
    and return the transcription text.
    """
    # Make sure we’re at the start of the file
    audio_file.seek(0)

    # Call the new client.audio.transcriptions.create endpoint
    resp = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",  # or "whisper-1" if you prefer
        file=audio_file
    )
    return resp.text  # this is the transcribed text

def speak_text(text):
    """
    (unchanged) your existing ElevenLabs TTS logic
    """
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
