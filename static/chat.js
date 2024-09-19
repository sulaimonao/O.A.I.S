
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
        }
    });

    function addMessageToChat(user, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message');
        messageElement.innerHTML = `<strong>${user}:</strong> ${message}`;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Scroll to bottom
    }
});
