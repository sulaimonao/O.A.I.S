document.addEventListener('DOMContentLoaded', function() {
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
    });

    // Test GPT-2 model interaction
    document.getElementById('test-gpt2-model').addEventListener('click', function() {
        const prompt = prompt("Enter a prompt to test GPT-2:");
        if (prompt) {
            fetch('/api/gpt2_interact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ input_text: prompt })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('gpt2-response').textContent = data.response;
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
            models = ['gpt-2-local'];  // Add Local GPT-2 model option here
        }
        modelSelect.innerHTML = models.map(model => `<option value="${model}">${model}</option>`).join('');
    }

    // Create Profile
    $('#create-profile').click(function() {
        const username = prompt("Enter new profile name:");
        if (username) {
            $.ajax({
                url: '/create_profile',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ username: username }),
                success: function(response) {
                    if (response.success) {
                        alert('Profile created successfully!');
                        $('#profile-select').append(`<option value="${username}">${username}</option>`);
                    } else {
                        alert(response.error);
                    }
                },
                error: function() {
                    alert('Error creating profile.');
                }
            });
        }
    });

    // Toggle Memory
    $('#memory-toggle').change(function() {
        const memoryEnabled = $(this).is(':checked');
        $.ajax({
            url: '/toggle_memory',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ memory_enabled: memoryEnabled }),
            success: function(response) {
                if (response.success) {
                    alert('Memory toggled successfully!');
                } else {
                    alert(response.error);
                }
            },
            error: function() {
                alert('Error toggling memory.');
            }
        });
    });
});
