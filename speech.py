import os
# whisper import is disabled for now so the server can start quickly
# import whisper
# from elevenlabslib import ElevenLabsUser

model = None
def transcribe_audio(audio_file):
    """Placeholder until Whisper is fully integrated."""
    return "[transcription stub]"

def speak_text(text):
    """Use ElevenLabs to convert text to speech and return an audio URL."""
    user  = ElevenLabsUser(os.getenv("ELEVENLABS_API_KEY"))
    voice = user.get_voice_by_name("George")
    audio_bytes = voice.generate_audio_bytes(text)
    # TODO: save bytes to a temp file or static path, return its URL
    return "/static/tts_output.mp3"
