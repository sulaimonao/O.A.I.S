$(document).ready(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var selectedModel = 'gpt-4o';  // Default model
    var selectedProvider = 'openai';  // Default provider

    // Function to update model options based on provider
    function updateModelOptions(provider) {
        var modelOptions = '';
        if (provider === 'openai') {
            modelOptions += '<option value="gpt-4o">GPT-4o</option>';
            modelOptions += '<option value="gpt-4o-mini">GPT-4o-mini</option>';
        } else if (provider === 'google') {
            modelOptions += '<option value="gemini-1.5-pro">Gemini 1.5 Pro</option>';
            modelOptions += '<option value="gemini-1.5-flash">Gemini 1.5 Flash</option>';
        }
        $('#model-select').html(modelOptions);
        $('#custom-engine').hide();
        $('#model-select').change();
    }

    // Initialize model options
    updateModelOptions($('#provider-select').val());

    // Update model options when provider changes
    $('#provider-select').change(function() {
        selectedProvider = $(this).val();
        updateModelOptions(selectedProvider);
    });

    // Show or hide custom engine text box based on model selection
    $('#model-select').change(function() {
        if ($(this).val() === 'custom') {
            $('#custom-engine').show();
        } else {
            $('#custom-engine').hide();
        }
    });

    // Save settings
    $('#save-settings').click(function() {
        selectedModel = $('#model-select').val();
        selectedProvider = $('#provider-select').val();
        alert('Settings saved! Using provider: ' + selectedProvider + ', model: ' + selectedModel);
    });

    $('form').submit(function(event) {
        event.preventDefault();
        console.log('Form submitted'); // Debug statement

        const message = $('#user-input').val();
        console.log('User input:', message); // Debug statement

        const fileInput = $('#file-input')[0];
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const formData = new FormData();
            const customEngine = $('#custom-engine').val();
            const config = {
                temperature: $('#temperature').val(),
                maxTokens: $('#max-tokens').val(),
                topP: $('#top-p').val()
            };

            let modelToUse = selectedModel;
            if (selectedModel === 'custom') {
                modelToUse = customEngine;
            }
            formData.append('file', file);
            $.ajax({
                url: '/upload',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    console.log('File upload response:', response); // Debug statement
                    if (response.error) {
                        alert(response.error);
                    } else {
                        socket.emit('message', JSON.stringify({ message: message, model: modelToUse, provider: selectedProvider, filename: response.filename, config: config }));
                        $('#user-input').val('');
                        $('#file-input').val('');
                    }
                }
            });
        } else {
            const config = {
                temperature: $('#temperature').val(),
                maxTokens: $('#max-tokens').val(),
                topP: $('#top-p').val()
            };
            let modelToUse = selectedModel;
            if (selectedModel === 'custom') {
                modelToUse = $('#custom-engine').val();
            }
            console.log('Sending message to server:', { message: message, model: modelToUse, provider: selectedProvider, config: config }); // Debug statement
            socket.emit('message', JSON.stringify({ message: message, model: modelToUse, provider: selectedProvider, config: config }));
            $('#user-input').val('');
        }
        return false;
    });

    socket.on('message', function(data) {
        console.log('Received message:', data);  // Debug statement
        if (data.error) {
            alert(data.error);
        } else {
            $('#chat-history').append('<div class="user-message">' + data.user + '</div>');
            $('#chat-history').append('<div class="bot-response">' + data.assistant + '</div>');
            if (data.image_url) {
                $('#chat-history').append('<img src="' + data.image_url + '" class="generated-image" alt="Generated Image">');
            }
            $('#chat-history').scrollTop($('#chat-history')[0].scrollHeight);
        }
    });

    // Memory and profile settings initialization
    const memoryToggle = document.getElementById('memory-toggle');
    const profileSelect = document.getElementById('profile-select');
    const createProfileButton = document.getElementById('create-profile');

    // Load existing profiles and memory setting
    loadProfiles();
    loadMemorySetting();

    memoryToggle.addEventListener('change', function() {
        const isEnabled = memoryToggle.checked;
        updateMemorySetting(isEnabled);
    });

    createProfileButton.addEventListener('click', function() {
        const profileName = prompt('Enter new profile name:');
        if (profileName) {
            createProfile(profileName);
        }
    });

    profileSelect.addEventListener('change', function() {
        const selectedProfile = profileSelect.value;
        if (selectedProfile) {
            selectProfile(selectedProfile);
        }
    });

    function loadProfiles() {
        // Fetch profiles from backend and populate the select element
        fetch('/api/profiles')
            .then(response => response.json())
            .then(profiles => {
                profiles.forEach(profile => {
                    const option = document.createElement('option');
                    option.value = profile;
                    option.textContent = profile;
                    profileSelect.appendChild(option);
                });
            });
    }

    function loadMemorySetting() {
        // Fetch current memory setting from backend
        fetch('/api/memory')
            .then(response => response.json())
            .then(data => {
                memoryToggle.checked = data.enabled;
            });
    }

    function updateMemorySetting(isEnabled) {
        // Update memory setting on backend
        fetch('/api/memory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled: isEnabled })
        });
    }

    function createProfile(profileName) {
        // Create new profile on backend
        fetch('/api/profiles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: profileName })
        })
        .then(response => response.json())
        .then(profile => {
            const option = document.createElement('option');
            option.value = profile.name;
            option.textContent = profile.name;
            profileSelect.appendChild(option);
            profileSelect.value = profile.name;
        });
    }

    function selectProfile(profileName) {
        // Select profile on backend
        fetch('/api/profiles/select', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: profileName })
        });
    }
});
