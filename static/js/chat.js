// chat.js
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chat-input');
    const sendChatButton = document.getElementById('send-chat');
    const chatBox = document.getElementById('chat-box');

    sendChatButton.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            addMessageToChat('You', message);
            chatInput.value = ''; // Clear input
            sendMessageToServer(message); // Send message to server
        }
    });

    function addMessageToChat(user, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message');
        messageElement.innerHTML = `<strong>${user}:</strong> ${message}`;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Scroll to bottom
    }

    function sendMessageToServer(message) {
        const provider = document.getElementById('provider-select').value;
        const model = document.getElementById('model-select').value;

        fetch('/api/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, provider, model })
        })
        .then(response => response.json())
        .then(data => {
            if (data.assistant) {
                addMessageToChat('Assistant', data.assistant);
            } else if (data.error) {
                addMessageToChat('Error', data.error);
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
            addMessageToChat('Error', 'Failed to send message.');
        });
    }
});
