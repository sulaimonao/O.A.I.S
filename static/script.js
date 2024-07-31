$(document).ready(function() {
    var socket = io();
    var selectedModel = 'gpt-4o';  // Default model
    var selectedProvider = 'openai';  // Default provider

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

    socket.on('message', function(data) {
        if (data.error) {
            alert(data.error);
        } else {
            $('#chat-history').append('<div class="user-message">' + data.user + '</div>');
            $('#chat-history').append('<div class="bot-response">' + data.assistant + '</div>');
            $('#chat-history').scrollTop($('#chat-history')[0].scrollHeight);
        }
    });
});
