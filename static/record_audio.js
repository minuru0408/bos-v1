// static/record_audio.js

// cross-browser getUserMedia
async function getMicStream(c) {
    if (navigator.mediaDevices?.getUserMedia) {
      return navigator.mediaDevices.getUserMedia(c);
    }
    const legacy = navigator.getUserMedia ||
                   navigator.webkitGetUserMedia ||
                   navigator.mozGetUserMedia;
    if (legacy) {
      return new Promise((res, rej) =>
        legacy.call(navigator, c, res, rej)
      );
    }
    throw new Error("getUserMedia not supported");
  }
  
  let mediaRecorder, audioChunks = [];
  
  // start recording
  window.startRecording = async function() {
    const stream = await getMicStream({ audio: true });
    const MR = window.MediaRecorder || window.WebKitMediaRecorder;
    if (!MR) throw new Error("MediaRecorder not supported");
    mediaRecorder = new MR(stream);
    audioChunks = [];
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.start();
  };
  
  // stop and transcribe
  window.stopRecording = function() {
    if (!mediaRecorder) return;
    mediaRecorder.stop();
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: "audio/webm" });
      const form = new FormData();
      form.append("file", blob, "voice.webm");
      const res = await fetch("/api/transcribe", { method: "POST", body: form });
      const { text } = await res.json();
      document.getElementById("user-input").value = text;
    };
  };
  