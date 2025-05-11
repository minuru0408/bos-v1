import os
import time
import requests
from io import BytesIO
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_file):
    try:
        audio_bytes = audio_file.read()
        audio_buffer = BytesIO(audio_bytes)
        
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=("recording.webm", audio_buffer, "audio/webm")
        )
        return transcription.text
    except Exception as e:
        print(f"Transcription error: {e}")
        raise

def speak_text(text):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVEN_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    tts_dir = os.path.join("static", "tts")
    os.makedirs(tts_dir, exist_ok=True)
    filename = f"tts_{int(time.time() * 1000)}.mp3"
    filepath = os.path.join(tts_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(response.content)
    
    return f"/static/tts/{filename}"