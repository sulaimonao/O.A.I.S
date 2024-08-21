$(document).ready(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var selectedModel = 'gpt-4o';  // Default model
    var selectedProvider = 'openai';  // Default provider

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

    updateModelOptions($('#provider-select').val());

    $('#provider-select').change(function() {
        selectedProvider = $(this).val();
        updateModelOptions(selectedProvider);
    });

    $('#model-select').change(function() {
        if ($(this).val() === 'custom') {
            $('#custom-engine').show();
        } else {
            $('#custom-engine').hide();
        }
    });

    $('#save-settings').click(function() {
        selectedModel = $('#model-select').val();
        selectedProvider = $('#provider-select').val();
        alert('Settings saved! Using provider: ' + selectedProvider + ', model: ' + selectedModel);
    });

    $('form').submit(function(event) {
        event.preventDefault();
        const message = $('#user-input').val();
        const fileInput = $('#file-input')[0];

        if (fileInput.files.length > 0) {
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

            for (const file of fileInput.files) {
                formData.append('files[]', file);  // Note the 'files[]' to allow multiple files
            }

            $.ajax({
                url: '/upload',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.error) {
                        alert(response.error);
                    } else {
                        socket.emit('message', JSON.stringify({
                            message: message,
                            model: modelToUse,
                            provider: selectedProvider,
                            filenames: response.filenames,  // Updated to handle multiple filenames
                            config: config
                        }));
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
            socket.emit('message', JSON.stringify({
                message: message,
                model: modelToUse,
                provider: selectedProvider,
                config: config
            }));
            $('#user-input').val('');
        }
        return false;
    });

    socket.on('message', function(data) {
        if (data.error) {
            alert(data.error);
        } else {
            $('#chat-history').append('<div class="user-message">' + data.user + '</div>');
            $('#chat-history').append('<div class="bot-response">' + data.assistant + '</div>');
            if (data.filepath) {
                $('#chat-history').append('<div class="execution-result"><strong>Execution Result:</strong><pre>' + data.execution_result + '</pre></div>');
                $('#chat-history').append('<div class="generated-file"><strong>Generated File:</strong> <a href="' + data.filepath + '" download>Download Script</a></div>');
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
        const isMemoryEnabled = memoryToggle.checked;
        if (!isMemoryEnabled) {
            alert("Please enable memory before creating a profile.");
            return;
        }

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
        fetch('/api/profiles')
            .then(response => response.json())
            .then(profiles => {
                profileSelect.innerHTML = ''; // Clear existing options
                profiles.forEach(profile => {
                    const option = document.createElement('option');
                    option.value = profile;
                    option.textContent = profile;
                    profileSelect.appendChild(option);
                });
            });
    }

    function loadMemorySetting() {
        fetch('/api/memory')
            .then(response => response.json())
            .then(data => {
                memoryToggle.checked = data.enabled;
            });
    }

    function updateMemorySetting(isEnabled) {
        fetch('/api/memory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled: isEnabled })
        });
    }

    function createProfile(profileName) {
        fetch('/api/profiles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: profileName })
        })
        .then(response => response.json())
        .then(profile => {
            if (!profile.error) {
                const option = document.createElement('option');
                option.value = profile.name;
                option.textContent = profile.name;
                profileSelect.appendChild(option);
                profileSelect.value = profile.name;
            } else {
                alert(profile.error);
            }
        });
    }

    function selectProfile(profileName) {
        fetch('/api/profiles/select', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: profileName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            }
        });
    }
});
