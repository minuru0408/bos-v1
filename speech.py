import os
import whisper
from elevenlabslib import ElevenLabsUser

# Load Whisper model once
model = whisper.load_model("base")

def transcribe_audio(audio_file):
    """Use Whisper to convert audio to text."""
    result = model.transcribe(audio_file)
    return result["text"]

def speak_text(text):
    """Use ElevenLabs to convert text to speech and return an audio URL."""
    user  = ElevenLabsUser(os.getenv("ELEVENLABS_API_KEY"))
    voice = user.get_voice_by_name("George")
    audio_bytes = voice.generate_audio_bytes(text)
    # TODO: save bytes to a temp file or static path, return its URL
    return "/static/tts_output.mp3"
