document.addEventListener('DOMContentLoaded', function() {
    const socket = io();

    // Show/hide sections
    function showSection(sectionId) {
        const sections = document.querySelectorAll('.section');
        sections.forEach(section => {
            section.style.display = section.id === sectionId ? 'block' : 'none';
        });
    }
    showSection('dashboard-section'); // Default to showing dashboard

    // Fetch and populate profiles
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

    // Fetch settings from session
    fetch('/get_settings')
    .then(response => response.json())
    .then(data => {
        document.getElementById('provider-select').value = data.provider;
        updateModelOptions(data.provider);
        document.getElementById('model-select').value = data.model;
        document.getElementById('memory-toggle').checked = data.memory_enabled;
    });

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

    // Update model options based on provider
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

    // Initialize status window elements
    const gpt2StatusText = document.getElementById('gpt2-status-text');
    const gpt2TaskText = document.getElementById('gpt2-task-text');
    const wordllamaStatusText = document.getElementById('wordllama-status-text');
    const wordllamaTaskText = document.getElementById('wordllama-task-text');

    // Real-time status updates
    socket.on('status_update', function(data) {
        gpt2StatusText.textContent = `Status: ${data.gpt2_status}`;
        gpt2TaskText.textContent = `Current Task: ${data.gpt2_task}`;
        wordllamaStatusText.textContent = `Status: ${data.wordllama_status}`;
        wordllamaTaskText.textContent = `Current Task: ${data.wordllama_task}`;
    });

    // Emit initial status request
    socket.emit('status_update');

    // CodeMirror Editor Setup
    const codeTextarea = document.getElementById('code-input');
    const codeOutput = document.getElementById('code-output');
    const executionStatus = document.getElementById('execution-status');
    const terminalWindow = document.getElementById('terminal-window');
    const languageSelect = document.getElementById('language-select');

    const codeEditor = CodeMirror.fromTextArea(codeTextarea, {
        lineNumbers: true,
        mode: 'python',  // Default mode
        theme: 'eclipse',
        indentUnit: 4,
        tabSize: 4
    });

    // Toggle terminal visibility
    document.getElementById('toggle-terminal-btn').addEventListener('click', function() {
        terminalWindow.style.display = (terminalWindow.style.display === 'none') ? 'block' : 'none';
    });

    languageSelect.addEventListener('change', function() {
        const language = this.value;
        const mode = {
            'python': 'python',
            'javascript': 'javascript',
            'bash': 'shell'
        }[language];
        codeEditor.setOption('mode', mode);
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

    // Handle chat form submission
    document.getElementById('chat-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const message = document.getElementById('user-input').value.trim();
        if (message === '') return;

        const provider = document.getElementById('provider-select').value;
        const model = document.getElementById('model-select').value;

        socket.emit('message', JSON.stringify({ message, provider, model }));

        const chatHistory = document.getElementById('chat-history');
        const userMessageElement = document.createElement('div');
        userMessageElement.classList.add('user-message');
        userMessageElement.innerHTML = `<strong>You:</strong> ${message}`;
        chatHistory.appendChild(userMessageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        document.getElementById('user-input').value = '';
    });

    // Display responses
    socket.on('message', function(data) {
        const chatHistory = document.getElementById('chat-history');
        let messageElement;

        if (data.assistant) {
            messageElement = document.createElement('div');
            messageElement.classList.add('assistant-message');
            messageElement.innerHTML = `<strong>Assistant:</strong> ${data.assistant}`;
        }

        if (data.error) {
            messageElement = document.createElement('div');
            messageElement.classList.add('error-message');
            messageElement.innerHTML = `<strong>Error:</strong> ${data.error}`;
        }

        if (messageElement) {
            chatHistory.appendChild(messageElement);
        }

        chatHistory.scrollTop = chatHistory.scrollHeight;
    });
});
