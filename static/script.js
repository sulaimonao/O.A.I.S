$(document).ready(function() {
    var socket = io();
    var selectedModel = '';  // Default model
    var selectedProvider = '';  // Default provider
    var botResponseBuffer = "";  // Buffer to store bot response chunks

    // Centralized model options
    const modelsByProvider = {
        'openai': ['gpt-4o', 'gpt-4o-mini'],
        'google': ['gemini-1.5-pro', 'gemini-1.5-flash']
    };

    // Function to update model options based on provider
    function updateModelOptions(provider) {
        const modelOptions = modelsByProvider[provider] || [];
        let optionsHtml = '';
        modelOptions.forEach(model => {
            optionsHtml += `<option value="${model}">${model}</option>`;
        });
        $('#model-select').html(optionsHtml);
    }

    // Initialize model options based on provider
    updateModelOptions($('#provider-select').val());

    // Default config values
    const defaultConfig = {
        temperature: 0.8,
        maxTokens: 4000,
        topP: 1.0
    };

    // Initialize temperature, max tokens, and top-p
    $('#temperature').val(defaultConfig.temperature);
    $('#max-tokens').val(defaultConfig.maxTokens);
    $('#top-p').val(defaultConfig.topP);

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

    // Submit form and send message
    $('form').submit(function(event) {
        event.preventDefault();
        const message = $('#user-input').val();
        const fileInput = $('#file-input')[0];

        // Fetch config values (temperature, maxTokens, topP) from user input
        const config = {
            temperature: parseFloat($('#temperature').val()) || defaultConfig.temperature,
            maxTokens: parseInt($('#max-tokens').val(), 10) || defaultConfig.maxTokens,
            topP: parseFloat($('#top-p').val()) || defaultConfig.topP
        };

        // Append the user's message to the chat
        $('#chat-history').append('<div class="user-message">' + message + '</div>');

        // Handle file upload and message sending
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
                            model: modelToUse,
                            provider: selectedProvider,
                            filename: response.filename,
                            config: config
                        }));
                        $('#user-input').val(''); // Reset input
                        $('#file-input').val('');  // Reset file input
                    }
                }
            });
        } else {
            socket.send(JSON.stringify({
                message: message,
                model: selectedModel,
                provider: selectedProvider,
                config: config
            }));
            $('#user-input').val(''); // Reset input
        }
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
                botResponseBuffer += data.assistant;

                if ($('#chat-history .bot-response').last().length === 0) {
                    $('#chat-history').append('<div class="bot-response"></div>');
                }

                $('#chat-history .bot-response').last().text(botResponseBuffer);
            }

            $('#chat-history').scrollTop($('#chat-history')[0].scrollHeight);  // Scroll to bottom
        }
    });

    // Reset bot response buffer when message stream ends
    socket.on('message_end', function() {
        botResponseBuffer = "";  // Reset for next message
    });
});
