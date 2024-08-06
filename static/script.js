$(document).ready(function() {
    var socket = io();
    var selectedModel = 'gpt-4o';  // Default model
    var selectedProvider = 'openai';  // Default provider

    // Login/Registration Form Handling
    $('#login-form').submit(function(event) {  // Assuming your login form has the ID 'login-form'
        event.preventDefault(); 

        // Retrieve username and password from the form
        const username = $('#username-input').val();  // Adjust the ID if needed
        const password = $('#password-input').val();  // Adjust the ID if needed

        // Send AJAX request to the server for login
        $.ajax({
            url: '/',  // Assuming your login route is at the root URL
            type: 'POST',
            data: { username: username, password: password },  // You might need to adjust this based on your Flask backend
            success: function(response) {
                if (response.redirect) {
                    // Redirect to the chat interface on successful login
                    window.location.href = response.redirect;
                } else {
                    // Display an error message if login fails
                    alert(response.error); 
                }
            },
            error: function() {
                alert('An error occurred during login. Please try again.');
            }
        });
    });

    // New Profile Creation Form Handling
    $('#new-profile-form').submit(function(event) {  // Assuming your new profile form has the ID 'new-profile-form'
        event.preventDefault(); 

        // Retrieve new profile name from the form
        const newProfileName = $('#new-profile-name').val();  // Adjust the ID if needed

        // Send AJAX request to the server to create a new profile
        $.ajax({
            url: '/', 
            type: 'POST',
            data: { username: newProfileName, new_profile: true },  // Indicate new profile creation
            success: function(response) {
                if (response.redirect) {
                    // Redirect to the chat interface after creating a new profile
                    window.location.href = response.redirect;
                } else {
                    // Display an error message if profile creation fails
                    alert(response.error); 
                }
            },
            error: function() {
                alert('An error occurred while creating a new profile. Please try again.');
            }
        });
    });

    // Profile Selection Handling (if applicable)
    $('#profile-select').change(function() {  // Assuming your profile dropdown has the ID 'profile-select'
        const selectedProfile = $(this).val();

        // Send AJAX request to the server with the selected profile
        $.ajax({
            url: '/', 
            type: 'POST',
            data: { username: selectedProfile }, 
            success: function(response) {
                if (response.redirect) {
                    // Redirect to the chat interface after selecting a profile
                    window.location.href = response.redirect;
                } else {
                    // Handle any errors from the server
                    alert(response.error); 
                }
            },
            error: function() {
                alert('An error occurred while selecting a profile. Please try again.');
            }
        });
    });
    
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
        const message = $('#user-input').val();
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
                    if (response.error) {
                        alert(response.error);
                    } else {
                        socket.send(JSON.stringify({ message: message, model: modelToUse, provider: selectedProvider, filename: response.filename, config: config }));
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
            socket.send(JSON.stringify({ message: message, model: modelToUse, provider: selectedProvider, config: config }));
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
            if (data.image_url) {
                $('#chat-history').append('<img src="' + data.image_url + '" class="generated-image" alt="Generated Image">');
            }
            $('#chat-history').scrollTop($('#chat-history')[0].scrollHeight);
        }
    });
});

function readCode(filepath) {
    $.post('/read_code', { filepath: filepath }, function(response) {
        if (response.error) {
            alert(response.error);
        } else {
            console.log('File content:', response.content);
        }
    });
}

function writeCode(filepath, content) {
    $.post('/write_code', { filepath: filepath, content: content }, function(response) {
        if (response.error) {
            alert(response.error);
        } else {
            console.log(response.message);
        }
    });
}

function executeCode(filepath) {
    $.post('/execute_code', { filepath: filepath }, function(response) {
        console.log('Execution output:', response.stdout);
        console.log('Execution errors:', response.stderr);
    });
}
