
// uiInteractions.js

// Show and hide sections
function showSection(sectionId) {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = section.id === sectionId + '-section' ? 'block' : 'none';
    });
}

// User Menu Dropdown
const userMenu = document.getElementById('user-menu');
const userDropdown = document.getElementById('user-dropdown');
userMenu.addEventListener('click', function () {
    userDropdown.classList.toggle('show');
});

// Close the dropdown if the user clicks outside of it
window.addEventListener('click', function (event) {
    if (!userMenu.contains(event.target)) {
        userDropdown.classList.remove('show');
    }
});
