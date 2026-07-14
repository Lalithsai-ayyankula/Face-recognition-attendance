// Dark Mode Toggle
function toggleDarkMode() {
    const body = document.body;
    body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', body.classList.contains('dark-mode'));

    // Update dark mode button icon
    const darkModeButton = document.querySelector('.dark-mode-toggle');
    if (darkModeButton) {
        const icon = darkModeButton.querySelector('i');
        if (body.classList.contains('dark-mode')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    }
}

// Apply saved dark mode preference
function applySavedDarkMode() {
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
}

// Image Preview and Validation
function previewImages(event) {
    const preview = document.getElementById('imagePreview');
    if (!preview) return;

    preview.innerHTML = ''; // Clear previous previews
    const files = event.target.files;

    // Validate file size and type
    for (const file of files) {
        if (file.size > 5 * 1024 * 1024) { // 5MB limit
            alert('File size exceeds 5MB. Please upload smaller files.');
            event.target.value = ''; // Clear the input
            return;
        }

        if (!file.type.startsWith('image/')) {
            alert('Only image files are allowed.');
            event.target.value = ''; // Clear the input
            return;
        }

        // Create and append image preview
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.classList.add('img-thumbnail', 'me-2');
        img.style.maxWidth = '100px';
        img.style.maxHeight = '100px';
        preview.appendChild(img);
    }
}

// Delete Confirmation Dialog
function confirmDelete(event) {
    if (!confirm('Are you sure you want to delete this record?')) {
        event.preventDefault(); // Prevent form submission if user cancels
    }
}

// Initialize DataTables
function initializeDataTables() {
    const attendanceTable = document.getElementById('attendanceTable');
    if (attendanceTable) {
        $(attendanceTable).DataTable({
            paging: true,
            searching: true,
            ordering: true,
            info: true,
            responsive: true,
        });
    }
}

// Initialize the page
function initialize() {
    // Apply saved dark mode preference
    applySavedDarkMode();

    // Dark mode button event listener
    const darkModeButton = document.querySelector('.dark-mode-toggle');
    if (darkModeButton) {
        darkModeButton.addEventListener('click', toggleDarkMode);
    }

    // Image upload preview event listener
    const imageInput = document.getElementById('images');
    if (imageInput) {
        imageInput.addEventListener('change', previewImages);
    }

    // Delete button confirmation
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', confirmDelete);
    });

    // Initialize DataTables
    initializeDataTables();
}

// Event Listener for DOM Load
document.addEventListener('DOMContentLoaded', initialize);