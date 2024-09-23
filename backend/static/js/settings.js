// settings.js
document.addEventListener('DOMContentLoaded', () => {
    const toggleSettingsBtn = document.getElementById('toggle-settings-btn');
    const settingsPanel = document.getElementById('settings-panel');

    // Toggle Settings Panel
    toggleSettingsBtn.addEventListener('click', () => {
        if (settingsPanel.classList.contains('hidden')) {
            settingsPanel.classList.remove('hidden');
        } else {
            settingsPanel.classList.add('hidden');
        }
    });

    // Load settings and profiles on page load
    loadProfiles();
    loadSettings();

    // Save settings
    document.getElementById('save-settings').addEventListener('click', function() {
        const provider = document.getElementById('provider-select').value;
        const model = document.getElementById('model-select').value;
        const memoryEnabled = document.getElementById('memory-toggle').checked;

        fetch('/save_settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, model, memory_enabled: memoryEnabled })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Settings saved successfully!');
            } else {
                alert('Failed to save settings.');
            }
        })
        .catch(() => alert('Error saving settings.'));
    });

    // Load profiles into dropdown
    function loadProfiles() {
        fetch('/get_profiles')
            .then(response => response.json())
            .then(profiles => {
                const profileSelect = document.getElementById('profile-select');
                profileSelect.innerHTML = ""; // Clear current options
                profiles.forEach(profile => {
                    const option = document.createElement('option');
                    option.value = profile.id;
                    option.textContent = profile.username;
                    profileSelect.appendChild(option);
                });
            })
            .catch(error => console.error('Error loading profiles:', error));
    }

    // Load initial settings
    function loadSettings() {
        fetch('/get_settings')
            .then(response => response.json())
            .then(data => {
                document.getElementById('provider-select').value = data.provider;
                updateModelOptions(data.provider);
                document.getElementById('model-select').value = data.model;
                document.getElementById('memory-toggle').checked = data.memory_enabled;
            })
            .catch(error => console.error('Error loading settings:', error));
    }

    // Update model options based on provider
    function updateModelOptions(provider) {
        const modelSelect = document.getElementById('model-select');
        let models = [];
        if (provider === 'openai') {
            models = ['gpt-4o', 'gpt-4o-mini'];
        } else if (provider === 'google') {
            models = ['gemini-1.5-pro', 'gemini-1.5-flash'];
        } else if (provider === 'local') {
            models = ['gpt-2-local'];
        }
        modelSelect.innerHTML = models.map(model => `<option value="${model}">${model}</option>`).join('');
    }

    // Handle provider selection change
    document.getElementById('provider-select').addEventListener('change', function() {
        updateModelOptions(this.value);
    });
});
