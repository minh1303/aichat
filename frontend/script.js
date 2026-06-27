const chatBox = document.getElementById('chatBox');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const statusDiv = document.getElementById('status');
const avatar = document.getElementById('avatar');

function setStatus(msg, isError = false) {
    statusDiv.textContent = msg;
    statusDiv.className = isError ? 'offline' : '';
}

function setEmotion(emotion) {
    avatar.className = 'avatar ' + emotion;
}

function addMessage(text, type = 'assistant') {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addTyping() {
    const div = document.createElement('div');
    div.className = 'message assistant typing';
    div.textContent = '✍️ Thinking...';
    div.id = 'typing-indicator';
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.value = '';
    addMessage(text, 'user');
    addTyping();
    setStatus('⏳ Thinking...');

    try {
        const res = await fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });

        const data = await res.json();
        removeTyping();

        if (data.reply) {
            addMessage(data.reply, 'assistant');

            // Simple emotion detection from reply
            const reply = data.reply.toLowerCase();
            if (reply.includes('love') || reply.includes('happy') || reply.includes('cute') || reply.includes('adorable')) {
                setEmotion('happy');
            } else if (reply.includes('sad') || reply.includes('cry') || reply.includes('sorry')) {
                setEmotion('sad');
            } else {
                setEmotion('');
            }

            setStatus('✅ Online');
        } else {
            addMessage('❌ Error: ' + (data.error || 'Unknown'), 'system');
            setStatus('❌ Error', true);
        }
    } catch (err) {
        removeTyping();
        addMessage('❌ Server unreachable (port 5000)', 'system');
        setStatus('❌ Offline', true);
    }
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
});

setStatus('✨ Online');