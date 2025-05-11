import os
import time
import requests
import openai

def transcribe_audio(audio_file):
    """
    Send uploaded audio (webm/wav/mp3) to OpenAI Whisper and return the text.
    """
    # Initialize OpenAI client with API key
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Explicit initialization
    
    # Ensure file pointer is at start
    audio_file.seek(0)
    
    # Create transcription using updated API syntax
    resp = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return resp.text  # Access text attribute directly

def speak_text(text):
    """
    Send text to ElevenLabs API and save the streamed MP3 under static/tts.
    Returns the URL path for your front-end to fetch and play.
    """
    # Load your ElevenLabs key and George’s voice ID
    api_key  = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVEN_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")

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

    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()

    # Save MP3 under static/tts so Flask can serve it
    tts_dir = os.path.join("static", "tts")
    os.makedirs(tts_dir, exist_ok=True)
    filename = f"tts_{int(time.time()*1000)}.mp3"
    filepath = os.path.join(tts_dir, filename)
    with open(filepath, "wb") as f:
        f.write(resp.content)

    return f"/static/tts/{filename}"
