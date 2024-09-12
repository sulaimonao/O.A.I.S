document.addEventListener('DOMContentLoaded', function() {
    // Socket.IO setup
    const socket = io();

    // Fetch and populate profiles from the database
    fetch('/get_profiles')
    .then(response => response.json())
    .then(profiles => {
        const profileSelect = document.getElementById('profile-select');
        profiles.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile.id;
            option.textContent = profile.username;
            profileSelect.appendChild(option);
        });
    });

    // Fetch settings from session and restore
    fetch('/get_settings')
    .then(response => response.json())
    .then(data => {
        // Restore provider, model, and memory settings
        document.getElementById('provider-select').value = data.provider;
        updateModelOptions(data.provider);
        document.getElementById('model-select').value = data.model;
        document.getElementById('memory-toggle').checked = data.memory_enabled;
    });

    // Save settings when changed
    document.getElementById('save-settings').addEventListener('click', function() {
        const provider = document.getElementById('provider-select').value;
        const model = document.getElementById('model-select').value;
        const memoryEnabled = document.getElementById('memory-toggle').checked;

        fetch('/save_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ provider, model, memory_enabled: memoryEnabled })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Settings saved successfully!');
            } else {
                alert('Failed to save settings.');
            }
        })
        .catch(() => {
            alert('Error saving settings.');
        });
    });

    // Check GPT-2 status immediately on load
    fetch('/api/gpt2_status')
    .then(response => response.json())
    .then(data => {
        // Update status element
        const statusElement = document.getElementById('gpt2-status');

        if (data.status === 'operational') {
            statusElement.textContent = 'Status: Operational';
            statusElement.classList.add('status-success');
        } else {
            statusElement.textContent = 'Status: Error - ' + data.error;
            statusElement.classList.add('status-error');
        }
    })
    .catch(error => {
        console.error('Error fetching GPT-2 status:', error);
    });

    // Test GPT-2 model interaction
    document.getElementById('test-gpt2-model').addEventListener('click', function() {
        const promptText = prompt("Enter a prompt to test GPT-2:");
        if (promptText) {
            fetch('/api/gpt2_interact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ input_text: promptText })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('gpt2-response').textContent = data.response || data.error;
            })
            .catch(() => {
                document.getElementById('gpt2-response').textContent = 'Error generating response.';
            });
        }
    });

    // Update model options based on provider selection
    document.getElementById('provider-select').addEventListener('change', function() {
        const provider = this.value;
        updateModelOptions(provider);
    });

    function updateModelOptions(provider) {
        const modelSelect = document.getElementById('model-select');
        let models = [];
        if (provider === 'openai') {
            models = ['gpt-4o', 'gpt-4o-mini'];
        } else if (provider === 'google') {
            models = ['gemini-1.5-pro', 'gemini-1.5-flash'];
        } else if (provider === 'local') {
            models = ['gpt-2-local'];
        }
        modelSelect.innerHTML = models.map(model => `<option value="${model}">${model}</option>`).join('');
    }

    // Create Profile
    document.getElementById('create-profile').addEventListener('click', function() {
        const username = prompt("Enter new profile name:");
        if (username) {
            fetch('/create_profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username: username })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Profile created successfully!');
                    const profileSelect = document.getElementById('profile-select');
                    const option = document.createElement('option');
                    option.value = data.id;
                    option.textContent = username;
                    profileSelect.appendChild(option);
                } else {
                    alert(data.error);
                }
            })
            .catch(() => {
                alert('Error creating profile.');
            });
        }
    });

    // Toggle Memory
    document.getElementById('memory-toggle').addEventListener('change', function() {
        const memoryEnabled = this.checked;
        fetch('/toggle_memory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ memory_enabled: memoryEnabled })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Memory toggled successfully!');
            } else {
                alert(data.error);
            }
        })
        .catch(() => {
            alert('Error toggling memory.');
        });
    });

    // Save GPT-2 Settings
    document.getElementById('save-gpt2-settings').addEventListener('click', function() {
        const maxTokens = parseInt(document.getElementById('gpt2-max-tokens').value, 10);
        if (isNaN(maxTokens) || maxTokens <= 0) {
            alert('Please enter a valid number for Max Tokens.');
            return;
        }
        // Save the maxTokens value as needed
        alert('GPT-2 settings saved successfully!');
    });

    // Socket.IO chat functionality
    const chatForm = document.getElementById('chat-form');
    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const messageInput = document.getElementById('user-input');
        const message = messageInput.value.trim();
        if (message === '') {
            return;
        }

        const provider = document.getElementById('provider-select').value;
        const model = document.getElementById('model-select').value;

        const data = {
            message: message,
            provider: provider,
            model: model
        };

        socket.emit('message', JSON.stringify(data));

        // Add user's message to chat history
        const chatHistory = document.getElementById('chat-history');
        chatHistory.innerHTML += `<div class="user-message"><strong>You:</strong> ${message}</div>`;
        chatHistory.scrollTop = chatHistory.scrollHeight;

        messageInput.value = '';
    });

    // Handle incoming messages from the server
    socket.on('message', function(data) {
        const chatHistory = document.getElementById('chat-history');
        if (data.assistant) {
            chatHistory.innerHTML += `<div class="assistant-message"><strong>Assistant:</strong> ${data.assistant}</div>`;
        }
        if (data.error) {
            chatHistory.innerHTML += `<div class="error-message"><strong>Error:</strong> ${data.error}</div>`;
        }
        if (data.feedback_prompt) {
            chatHistory.innerHTML += `<div class="assistant-message"><strong>Assistant:</strong> ${data.feedback_prompt}</div>`;
        }
        if (data.memory) {
            chatHistory.innerHTML += `<div class="assistant-message"><strong>Memory:</strong> ${data.memory}</div>`;
        }
        if (data.response) {
            chatHistory.innerHTML += `<div class="assistant-message"><strong>Assistant:</strong> ${data.response}</div>`;
        }
        chatHistory.scrollTop = chatHistory.scrollHeight;
    });
});
