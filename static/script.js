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
                        socket.send(JSON.stringify({ message: message, model: selectedModel, provider: selectedProvider, filename: response.filename }));
                        $('#user-input').val('');
                        $('#file-input').val('');
                    }
                }
            });
        } else {
            socket.send(JSON.stringify({ message: message, model: selectedModel, provider: selectedProvider }));
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
                // Buffer the bot response chunks
                botResponseBuffer += data.assistant;

                // If bot-response div exists, update it with the buffer
                if ($('#chat-history .bot-response').last().length) {
                    $('#chat-history .bot-response').last().text(botResponseBuffer);  // Update the last response
                } else {
                    $('#chat-history').append('<div class="bot-response">' + botResponseBuffer + '</div>');  // Create new if first chunk
                }
            }

            if (data.image_url) {
                $('#chat-history').append('<img src="' + data.image_url + '" class="generated-image" alt="Generated Image">');
            }

            $('#chat-history').scrollTop($('#chat-history')[0].scrollHeight);
        }
    });
});