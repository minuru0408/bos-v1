import os
import openai
import time
from elevenlabslib.User import User as ElevenLabsUser

# 1) TRANSCRIBE using Whisper API
def transcribe_audio(audio_file):
    """
    Convert uploaded audio (wav/webm/mp3) to text via OpenAI Whisper.
    audio_file is the Flask file object.
    """
    audio_file.seek(0)
    resp = openai.Audio.transcribe(
        model="whisper-1",
        file=audio_file
    )
    return resp["text"]

# 2) SPEAK using ElevenLabs
def speak_text(text):
    """
    Generate a TTS mp3 via ElevenLabs and return its URL path.
    Uses ELEVENLABS_VOICE_NAME env var (defaults to "George").
    """
    user = ElevenLabsUser(os.getenv("ELEVENLABS_API_KEY"))
    voice_name = os.getenv("ELEVENLABS_VOICE_NAME", "George")
    voice = user.get_voice_by_name(voice_name)

    audio_bytes = voice.generate_audio_bytes(text)

    # save under static/tts so Flask can serve it
    filename = f"tts_{int(time.time()*1000)}.mp3"
    filepath = os.path.join("static", "tts", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)

    return f"/static/tts/{filename}"
