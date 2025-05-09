import os
import time
from elevenlabslib.User import User as ElevenLabsUser
import openai

def transcribe_audio(audio_file):
    """
    Use OpenAI’s Whisper API to convert uploaded audio to text.
    Supports webm, wav, mp3, etc.
    """
    # audio_file is a Flask FileStorage; we can send it directly
    audio_file.seek(0)
    resp = openai.Audio.transcribe(
        model="whisper-1",
        file=audio_file
    )
    return resp["text"]

def speak_text(text):
    """
    Generate a TTS mp3 via ElevenLabs and return its static URL.
    Uses the ELEVENLABS_VOICE_NAME env var (defaulting to "George").
    """
    # 1) Init client
    user = ElevenLabsUser(os.getenv("ELEVENLABS_API_KEY"))

    # 2) Pick voice name from env
    voice_name = os.getenv("ELEVENLABS_VOICE_NAME", "George")
    voice = user.get_voice_by_name(voice_name)

    # 3) Generate audio bytes
    audio_bytes = voice.generate_audio_bytes(text)

    # 4) Save to static/tts
    filename = f"tts_{int(time.time() * 1000)}.mp3"
    filepath = os.path.join("static", "tts", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)

    # 5) Return the URL your front-end can fetch
    return f"/static/tts/{filename}"
