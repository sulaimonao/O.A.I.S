
// settings.js

// Fetch settings from session and restore
fetch('/get_settings')
    .then(response => response.json())
    .then(data => {
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
