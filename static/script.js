document.addEventListener('DOMContentLoaded', function() {
    const socket = io();

    // Show/hide sections based on navigation
    function showSection(sectionId) {
        const sections = document.querySelectorAll('.section');
        sections.forEach(section => {
            section.style.display = section.id === sectionId ? 'block' : 'none';
        });
    }
    showSection('dashboard-section'); // Default to showing dashboard

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

    // Check GPT-2 status immediately on load
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

    // Toggle terminal window visibility
    document.getElementById('toggle-terminal-btn').addEventListener('click', function() {
        if (terminalWindow.style.display === 'none' || terminalWindow.style.display === '') {
            terminalWindow.style.display = 'block';
        } else {
            terminalWindow.style.display = 'none';
        }
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

    let currentAssistantMessageElement = null;

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

        const chatHistory = document.getElementById('chat-history');
        const userMessageElement = document.createElement('div');
        userMessageElement.classList.add('user-message');
        userMessageElement.innerHTML = `<strong>You:</strong> ${message}`;
        chatHistory.appendChild(userMessageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        messageInput.value = '';

        currentAssistantMessageElement = null;
    });

    socket.on('message', function(data) {
        const chatHistory = document.getElementById('chat-history');

        if (data.assistant) {
            if (!currentAssistantMessageElement) {
                currentAssistantMessageElement = document.createElement('div');
                currentAssistantMessageElement.classList.add('assistant-message');
                currentAssistantMessageElement.innerHTML = '<strong>Assistant:</strong> ';
                chatHistory.appendChild(currentAssistantMessageElement);
            }
            currentAssistantMessageElement.innerHTML += data.assistant;
        }

        if (data.error) {
            const errorMessage = document.createElement('div');
            errorMessage.classList.add('error-message');
            errorMessage.innerHTML = `<strong>Error:</strong> ${data.error}`;
            chatHistory.appendChild(errorMessage);
        }

        if (data.feedback_prompt) {
            const feedbackMessage = document.createElement('div');
            feedbackMessage.classList.add('assistant-message');
            feedbackMessage.innerHTML = `<strong>Assistant:</strong> ${data.feedback_prompt}`;
            chatHistory.appendChild(feedbackMessage);
        }

        if (data.memory) {
            const memoryMessage = document.createElement('div');
            memoryMessage.classList.add('assistant-message');
            memoryMessage.innerHTML = `<strong>Memory:</strong> ${data.memory}`;
            chatHistory.appendChild(memoryMessage);
        }

        if (data.response) {
            const responseMessage = document.createElement('div');
            responseMessage.classList.add('assistant-message');
            responseMessage.innerHTML = `<strong>Assistant:</strong> ${data.response}`;
            chatHistory.appendChild(responseMessage);
        }

        if (data.done) {
            currentAssistantMessageElement = null;
        }

        chatHistory.scrollTop = chatHistory.scrollHeight;
    });
});
