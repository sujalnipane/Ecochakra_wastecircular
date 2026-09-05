function toggleChat() {
    const chatBox = document.getElementById('chat-box');
    chatBox.style.display = chatBox.style.display === 'none' ? 'block' : 'none';
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML += `<div><b>You:</b> ${message}</div>`;
    input.value = '';

    // Backend Flask Proxy Route Ko Call Karein
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        messagesContainer.innerHTML += `<div style="color: #2e7d32;"><b>EcoBot:</b> ${data.reply}</div>`;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (error) {
        messagesContainer.innerHTML += `<div style="color: red;"><b>System:</b> Error processing response.</div>`;
    }
}