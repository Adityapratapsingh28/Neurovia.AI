document.addEventListener('DOMContentLoaded', () => {
    const dropupBtn = document.getElementById('dropup-btn');
    const dropupContent = document.getElementById('myDropup');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const clearChatLink = document.getElementById('clear-chat');

    function toggleDropup() {
        dropupContent.classList.toggle('hidden');
        dropupContent.classList.toggle('scale-95');
        dropupContent.classList.toggle('opacity-0');
    }

    window.onclick = function(event) {
        if (!event.target.matches('#dropup-btn')) {
            if (!dropupContent.classList.contains('hidden')) {
                dropupContent.classList.add('hidden');
                dropupContent.classList.add('scale-95');
                dropupContent.classList.add('opacity-0');
            }
        }
    };

    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        chatMessages.innerHTML += `<div class="bg-blue-100 p-2 rounded-lg mb-2 self-end">You: ${message}</div>`;
        chatInput.value = '';

        const response = await fetch('/api/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        chatMessages.innerHTML += `<div class="bg-gray-100 p-2 rounded-lg mb-2 self-start">Bot: ${data.response}</div>`;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function clearChat() {
        chatMessages.innerHTML = '';
    }

    dropupBtn.addEventListener('click', toggleDropup);
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    clearChatLink.addEventListener('click', (e) => {
        e.preventDefault();
        clearChat();
    });
});