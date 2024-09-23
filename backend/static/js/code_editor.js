// code_editor.js
document.addEventListener('DOMContentLoaded', () => {
    const codeEditor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        lineNumbers: true,
        mode: 'python',
        theme: 'eclipse'
    });

    // Execute code button
    document.getElementById('run-code').addEventListener('click', () => {
        const code = codeEditor.getValue();
        const language = document.getElementById('language-select').value;
        executeCode(code, language);
    });

    // Function to execute code
    function executeCode(code, language) {
        if (code.trim() === '') {
            alert('Please enter some code to execute.');
            return;
        }

        fetch('/execute_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language })
        })
        .then(response => response.json())
        .then(result => {
            const codeOutput = document.getElementById('code-output');
            if (result.status === 'success') {
                codeOutput.textContent = result.output;
                codeOutput.style.color = 'black';
            } else {
                codeOutput.textContent = result.output;
                codeOutput.style.color = 'red';
            }
        })
        .catch(error => {
            console.error('Error executing code:', error);
            alert('An error occurred while executing code.');
        });
    }
});
