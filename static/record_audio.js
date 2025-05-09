// static/record_audio.js

// Cross–browser getUserMedia
async function getMicStream(constraints) {
    if (navigator.mediaDevices?.getUserMedia) {
      return navigator.mediaDevices.getUserMedia(constraints);
    }
    const legacy = navigator.getUserMedia ||
                   navigator.webkitGetUserMedia ||
                   navigator.mozGetUserMedia;
    if (legacy) {
      return new Promise((res, rej) =>
        legacy.call(navigator, constraints, res, rej)
      );
    }
    throw new Error("getUserMedia not supported");
  }
  
  let mediaRecorder;
  let audioChunks = [];
  
  // Called when user clicks “Start Recording”
  async function startRecording() {
    try {
      const stream = await getMicStream({ audio: true });
      const MR = window.MediaRecorder || window.WebKitMediaRecorder;
      if (!MR) throw new Error("MediaRecorder not supported");
  
      mediaRecorder = new MR(stream);
      audioChunks = [];
      mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
      mediaRecorder.start();
    } catch (err) {
      alert("🔴 Cannot access microphone:\n" + err.message);
    }
  }
  
  // Called when user clicks “Stop Recording”
  async function stopRecording() {
    if (!mediaRecorder) return;
  
    mediaRecorder.stop();
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      const form = new FormData();
      form.append('file', blob, 'voice.webm');
  
      try {
        const res = await fetch('/api/transcribe', { method: 'POST', body: form });
        const { text } = await res.json();
        document.getElementById('user_input').value = text;
      } catch (err) {
        console.error(err);
        alert("🔴 Transcription failed:\n" + err.message);
      }
    };
  }
  