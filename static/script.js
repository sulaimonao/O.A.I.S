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
            if (data.user) {
                $('#chat-history').append('<div class="user-message">' + data.user + '</div>');
            }
            if (data.code) {
                $('#chat-history').append('<pre class="bot-response"><code>' + extractText(data.code) + '</code></pre><button class="copy-btn" onclick="copyToClipboard(this)">Copy Code</button>');
            }
            if (data.assistant) {
                $('#chat-history').append('<div class="bot-response">' + extractText(data.assistant) + '</div>');
            }
            if (data.image_url) {
                $('#chat-history').append('<img src="' + data.image_url + '" class="generated-image" alt="Generated Image">');
            }
            $('#chat-history').scrollTop($('#chat-history')[0].scrollHeight);
        }
    });

    function copyToClipboard(button) {
        const codeBlock = button.previousElementSibling; // Assumes the button is placed after the code block
        const code = codeBlock.innerText;

        navigator.clipboard.writeText(code).then(() => {
            alert("Code copied to clipboard");
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    }

    function extractText(data) {
        try {
            const parsedData = JSON.parse(data);
            if (parsedData.parts && Array.isArray(parsedData.parts)) {
                return parsedData.parts.map(part => part.text).join('<br>').replace(/\\n/g, '<br>');
            } else {
                return data;
            }
        } catch (e) {
            console.error("Failed to parse response data:", e);
            return data;
        }
    }
});
