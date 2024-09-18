
// profile.js

// Fetch and populate profiles from the database
fetch('/get_profiles')
    .then(response => response.json())
    .then(profiles => {
        const profileSelect = document.getElementById('profile-select');
        profiles.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile.id;
            option.textContent = profile.username;
            profileSelect.appendChild(option);
        });
    });

// Create Profile
document.getElementById('create-profile').addEventListener('click', function () {
    const username = prompt("Enter new profile name:");
    if (username) {
        fetch('/create_profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Profile created successfully!');
                const profileSelect = document.getElementById('profile-select');
                const option = document.createElement('option');
                option.value = data.id;
                option.textContent = username;
                profileSelect.appendChild(option);
            } else {
                alert(data.error);
            }
        })
        .catch(() => {
            alert('Error creating profile.');
        });
    }
});
