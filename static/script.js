$(document).ready(function() {
    var socket = io();
    var selectedModel = '';  // Default model
    var selectedProvider = '';  // Default provider
    var botResponseBuffer = "";  // Buffer to store bot response chunks

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

    // Initialize temperature, maxTokens, and topP with default values from config.py (as an example)
    $('#temperature').val(0.8);  // Default from config.py
    $('#max-tokens').val(4000);  // Default from config.py
    $('#top-p').val(1.0);        // Default from config.py

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

    // Submit the form with the user's message
$('form').submit(function(event) {
    event.preventDefault();
    const message = $('#user-input').val();
    const fileInput = $('#file-input')[0];

    // Fetch config values (temperature, maxTokens, topP) from user input and ensure they are numbers
    const config = {
        temperature: parseFloat($('#temperature').val()) || 0.8,  // Convert to float
        maxTokens: parseInt($('#max-tokens').val(), 10) || 4000,  // Convert to integer
        topP: parseFloat($('#top-p').val()) || 1.0  // Convert to float
    };

    // Append the user's message to the chat
    $('#chat-history').append('<div class="user-message">' + message + '</div>');

    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const formData = new FormData();
        const customEngine = $('#custom-engine').val();

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
                    socket.send(JSON.stringify({
                        message: message, 
                        model: selectedModel, 
                        provider: selectedProvider, 
                        filename: response.filename, 
                        config: config  // Send config to the backend
                    }));
                    $('#user-input').val('');
                    $('#file-input').val('');
                }
            }
        });
    } else {
        socket.send(JSON.stringify({
            message: message, 
            model: selectedModel, 
            provider: selectedProvider,
            config: config  // Send config to the backend
        }));
        $('#user-input').val('');
    }
    return false;
});

    // Handle streaming response chunks
    socket.on('message', function(data) {
        if (data.error) {
            alert(data.error);
        } else {
            if (data.user) {
                $('#chat-history').append('<div class="user-message">' + data.user + '</div>');
            }

            if (data.assistant) {
                // Append the streaming response chunks to the botResponseBuffer
                botResponseBuffer += data.assistant;

                // Check if a bot-response div exists; if not, create it
                if (!$('#chat-history .bot-response').last().length) {
                    $('#chat-history').append('<div class="bot-response">' + botResponseBuffer + '</div>');
                } else {
                    // Update the last bot-response div with the new chunk
                    $('#chat-history .bot-response').last().text(botResponseBuffer);
                }
            }

            $('#chat-history').scrollTop($('#chat-history')[0].scrollHeight);
        }
    });

    // Reset the bot response buffer when the response ends
    socket.on('message_end', function() {
        botResponseBuffer = "";  // Reset the buffer for the next message
    });
});
