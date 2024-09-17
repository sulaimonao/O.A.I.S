document.addEventListener('DOMContentLoaded', function () {
    fetch('/get_settings')
        .then(response => response.json())
        .then(data => {
            document.getElementById('provider-select').value = data.provider;
            document.getElementById('model-select').value = data.model;
        });

    document.getElementById('save-settings').addEventListener('click', function (e) {
        e.preventDefault();
        const provider = document.getElementById('provider-select').value;
        const model = document.getElementById('model-select').value;

        fetch('/save_settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, model })
        })
            .then(response => response.json())
            .then(data => alert('Settings saved successfully!'))
            .catch(() => alert('Failed to save settings.'));
    });
});
