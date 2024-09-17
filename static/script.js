// script.js

// Show and hide sections
function showSection(sectionId) {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = section.id === sectionId + '-section' ? 'block' : 'none';
    });
}

// On page load, show the 'dashboard' section by default
document.addEventListener('DOMContentLoaded', function () {
    showSection('dashboard');

    // Initialize chat functionality
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
            document.getElementById('temperature').value = data.temperature;
            document.getElementById('max-tokens').value = data.maxTokens;
            document.getElementById('top-p').value = data.topP;
        });

    // Save settings when changed
    document.getElementById('save-settings').addEventListener('click', function () {
        const provider = document.getElementById('provider-select').value;
        const model = document.getElementById('model-select').value;
        const memoryEnabled = document.getElementById('memory-toggle').checked;
        const temperature = parseFloat(document.getElementById('temperature').value);
        const maxTokens = parseInt(document.getElementById('max-tokens').value);
        const topP = parseFloat(document.getElementById('top-p').value);

        fetch('/save_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ provider, model, memory_enabled: memoryEnabled, temperature, maxTokens, topP })
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

    // Update model options based on provider selection
    document.getElementById('provider-select').addEventListener('change', function () {
        const provider = this.value;
        updateModelOptions(provider);
    });

    function updateModelOptions(provider) {
        const modelSelect = document.getElementById('model-select');
        let models = [];
        if (provider === 'openai') {
            models = ['gpt-4', 'gpt-3.5-turbo'];
        } else if (provider === 'google') {
            models = ['gemini-1.5-pro', 'gemini-1.5-flash'];
        } else if (provider === 'local') {
            models = ['gpt-2-local'];
        }
        modelSelect.innerHTML = models.map(model => `<option value="${model}">${model}</option>`).join('');
    }

    // Create Profile
    document.getElementById('create-profile').addEventListener('click', function () {
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
    document.getElementById('memory-toggle').addEventListener('change', function () {
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

    // Chat Functionality
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

        // Add user's message to chat history
        addMessageToChat('You', message);

        // Clear the message input
        messageInput.value = '';
    });

    // Handle incoming messages from the server
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

    // Code Execution Functionality
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
    document.getElementById('toggle-terminal-btn').addEventListener('click', function () {
        if (terminalWindow.style.display === 'none' || terminalWindow.style.display === '') {
            terminalWindow.style.display = 'block';
        } else {
            terminalWindow.style.display = 'none';
        }
    });

    languageSelect.addEventListener('change', function () {
        const language = this.value;
        const mode = {
            'python': 'python',
            'javascript': 'javascript',
            'bash': 'shell'
        }[language];
        codeEditor.setOption('mode', mode);
    });

    document.getElementById('execute-code-btn').addEventListener('click', function () {
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

    // File Upload Functionality
    document.getElementById('upload-btn').addEventListener('click', function () {
        const fileInput = document.getElementById('file-upload');
        const files = fileInput.files;
        if (files.length === 0) {
            alert('Please select a file to upload.');
            return;
        }

        const formData = new FormData();
        for (let file of files) {
            formData.append('file', file);
        }

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.filenames) {
                    alert('Files uploaded successfully!');
                    // Update file status or list if needed
                } else {
                    alert('File upload failed.');
                }
            })
            .catch(error => {
                console.error('Error uploading files:', error);
                alert('An error occurred while uploading the files.');
            });
    });

    // Device Integration (Placeholder)
    // You can add device integration code here if needed

    // History and Logs (Placeholder)
    // You can add code to fetch and display history and logs here

    // User Menu Dropdown
    const userMenu = document.getElementById('user-menu');
    const userDropdown = document.getElementById('user-dropdown');
    userMenu.addEventListener('click', function () {
        userDropdown.classList.toggle('show');
    });

    // Close the dropdown if the user clicks outside of it
    window.addEventListener('click', function (event) {
        if (!userMenu.contains(event.target)) {
            userDropdown.classList.remove('show');
        }
    });
});
