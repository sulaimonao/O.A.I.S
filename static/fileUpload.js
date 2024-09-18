
// fileUpload.js

document.getElementById('upload-btn').addEventListener('click', function () {
    const fileInput = document.getElementById('file-upload');
    const files = fileInput.files;
    if (files.length === 0) {
        alert('Please select a file to upload.');
        return;
    }

    const formData = new FormData();
    for (let file of files) {
        formData.append('file', file);
    }

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.filenames) {
                alert('Files uploaded successfully!');
            } else {
                alert('File upload failed.');
            }
        })
        .catch(error => {
            console.error('Error uploading files:', error);
            alert('An error occurred while uploading the files.');
        });
});
