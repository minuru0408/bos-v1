const chat = document.getElementById('chat');
const input = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const speakBtn = document.getElementById('speakBtn');
let recognition;

function append(text) {
    const div = document.createElement('div');
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function handleSend() {
    const text = input.value.trim();
    if (!text) return;
    append('You: ' + text);
    input.value = '';

    if (/read email|show inbox/i.test(text)) {
        fetch('/api/email/read').then(r => r.json()).then(data => {
            if (data.messages) {
                data.messages.forEach(m => {
                    append(`From: ${m.from}\nSubject: ${m.subject}\n${m.snippet}`);
                });
            } else if (data.error) {
                append('Error: ' + data.error);
            }
        });
        return;
    }
    const match = text.match(/^send email to (.+?) subject (.+?) body (.+)$/i);
    if (match) {
        const payload = { to: match[1], subject: match[2], body: match[3] };
        fetch('/api/email/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(r => r.json()).then(data => {
            if (data.messageId) {
                append('Hector: Email sent successfully.');
            } else {
                append('Error: ' + (data.error || 'Unknown error'));
            }
        });
        return;
    }
    append("Hector: Command not recognized.");
}

sendBtn.addEventListener('click', handleSend);
input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = event => {
        const transcript = event.results[0][0].transcript;
        input.value = transcript;
        handleSend();
    };
}

speakBtn.addEventListener('click', () => {
    if (recognition) recognition.start();
});
