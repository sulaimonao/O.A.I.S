// script.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize socket connection
    const socket = io();

    // Profile Management
    function loadProfiles() {
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
            })
            .catch(error => console.error('Error loading profiles:', error));
    }
    loadProfiles();

    // Save settings function
    function saveSettings() {
        const provider = document.getElementById('provider-select').value;
        const model = document.getElementById('model-select').value;
        const memoryEnabled = document.getElementById('memory-toggle').checked;

        fetch('/save_settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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
            .catch(() => alert('Error saving settings.'));
    }
    document.getElementById('save-settings').addEventListener('click', saveSettings);

    // Fetch and display settings
    function loadSettings() {
        fetch('/get_settings')
            .then(response => response.json())
            .then(data => {
                document.getElementById('provider-select').value = data.provider;
                updateModelOptions(data.provider);
                document.getElementById('model-select').value = data.model;
                document.getElementById('memory-toggle').checked = data.memory_enabled;
            })
            .catch(error => console.error('Error loading settings:', error));
    }
    loadSettings();

    // Model Options Update
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
    document.getElementById('provider-select').addEventListener('change', function() {
        updateModelOptions(this.value);
    });

    // Memory Toggle Event
    document.getElementById('memory-toggle').addEventListener('change', function() {
        const memoryEnabled = this.checked;
        fetch('/toggle_memory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ memory_enabled: memoryEnabled })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Memory toggled successfully!');
                } else {
                    alert('Failed to toggle memory.');
                }
            })
            .catch(() => alert('Error toggling memory.'));
    });

    // Code Execution Handling
    const codeTextarea = document.getElementById('code-input');
    const codeOutput = document.getElementById('code-output');
    const executionStatus = document.getElementById('execution-status');
    const terminalWindow = document.getElementById('terminal-window');
    const languageSelect = document.getElementById('language-select');

    const codeEditor = CodeMirror.fromTextArea(codeTextarea, {
        lineNumbers: true,
        mode: 'python', // Default mode
        theme: 'eclipse',
        indentUnit: 4,
        tabSize: 4
    });

    // Toggle terminal window visibility
    const terminalToggleBtn = document.getElementById('toggle-terminal-btn');
    terminalToggleBtn.addEventListener('click', function() {
        if (terminalWindow.style.display === 'none' || terminalWindow.style.display === '') {
            terminalWindow.style.display = 'block';
        } else {
            terminalWindow.style.display = 'none';
        }
    });

    document.getElementById('execute-code-btn').addEventListener('click', function() {
        const code = codeEditor.getValue();
        const language = languageSelect.value;

        if (code.trim() === '') {
            alert('Please enter some code to execute.');
            return;
        }

        executionStatus.textContent = 'Executing code...';
        executionStatus.style.color = 'blue';

        fetch('/execute_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code, language: language })
        })
            .then(response => response.json())
            .then(result => {
                if (result.status === 'success') {
                    codeOutput.textContent = result.output;
                    codeOutput.style.color = 'black';
                    executionStatus.textContent = 'Execution successful.';
                    executionStatus.style.color = 'green';
                } else {
                    codeOutput.textContent = result.output;
                    codeOutput.style.color = 'red';
                    executionStatus.textContent = 'Execution failed.';
                    executionStatus.style.color = 'red';
                }
            })
            .catch(error => {
                console.error('Error executing code:', error);
                executionStatus.textContent = 'An error occurred.';
                executionStatus.style.color = 'red';
            });
    });

    // Chat Functionality
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

        const data = { message, provider, model };

        socket.emit('message', JSON.stringify(data));

        // Add user's message to chat history
        const chatHistory = document.getElementById('chat-history');
        const userMessageElement = document.createElement('div');
        userMessageElement.classList.add('user-message');
        userMessageElement.innerHTML = `<strong>You:</strong> ${message}`;
        chatHistory.appendChild(userMessageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        // Clear the message input
        messageInput.value = '';
    });

    // Handle incoming messages
    socket.on('message', function(data) {
        const chatHistory = document.getElementById('chat-history');
        let messageContent = '';

        if (data.assistant) {
            messageContent = `<strong>Assistant:</strong> ${data.assistant}`;
        } else if (data.error) {
            messageContent = `<strong>Error:</strong> ${data.error}`;
        }

        const assistantMessageElement = document.createElement('div');
        assistantMessageElement.classList.add('assistant-message');
        assistantMessageElement.innerHTML = messageContent;
        chatHistory.appendChild(assistantMessageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    });

    // Local Model Status Check
    function checkLocalModelStatus() {
        fetch('/api/gpt2_status')
            .then(response => response.json())
            .then(data => {
                const statusElement = document.getElementById('gpt2-status');
                if (data.status === 'operational') {
                    statusElement.textContent = 'Status: Operational';
                    statusElement.classList.add('status-success');
                } else {
                    statusElement.textContent = 'Status: Error - ' + data.error;
                    statusElement.classList.add('status-error');
                }
            })
            .catch(error => console.error('Error fetching GPT-2 status:', error));
    }
    checkLocalModelStatus();
});
