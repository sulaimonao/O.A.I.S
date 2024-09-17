document.getElementById('chat-form').addEventListener('submit', function (e) {
    e.preventDefault();
    const message = document.getElementById('user-input').value;
    const socket = io();

    socket.emit('message', { message });
    socket.on('message', function (data) {
        const chatHistory = document.getElementById('chat-history');
        const messageDiv = document.createElement('div');
        messageDiv.textContent = data.response;
        chatHistory.appendChild(messageDiv);
    });
});
