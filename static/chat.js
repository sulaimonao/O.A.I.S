
// chat.js

const socket = io();

const chatForm = document.getElementById('chat-form');
chatForm.addEventListener('submit', function (event) {
    event.preventDefault();
    const messageInput = document.getElementById('user-input');
    const message = messageInput.value.trim();
    if (message === '') {
        return;
    }

    const provider = document.getElementById('provider-select').value;
    const model = document.getElementById('model-select').value;
    const config = {
        temperature: parseFloat(document.getElementById('temperature').value),
        maxTokens: parseInt(document.getElementById('max-tokens').value),
        topP: parseFloat(document.getElementById('top-p').value)
    };

    const data = {
        message: message,
        provider: provider,
        model: model,
        config: config
    };

    socket.emit('message', JSON.stringify(data));

    addMessageToChat('You', message);
    messageInput.value = '';
});

socket.on('message', function (data) {
    if (data.assistant) {
        addMessageToChat('Assistant', data.assistant);
    }

    if (data.error) {
        addMessageToChat('Error', data.error);
    }

    if (data.feedback_prompt) {
        addMessageToChat('Assistant', data.feedback_prompt);
    }

    if (data.memory) {
        addMessageToChat('Memory', data.memory);
    }

    if (data.response) {
        addMessageToChat('Assistant', data.response);
    }
});

function addMessageToChat(sender, message) {
    const chatHistory = document.getElementById('chat-history');
    const messageElement = document.createElement('div');
    messageElement.classList.add(sender === 'You' ? 'user-message' : 'assistant-message');
    messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}
