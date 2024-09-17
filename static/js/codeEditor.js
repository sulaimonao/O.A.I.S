const codeEditor = CodeMirror.fromTextArea(document.getElementById('code-input'), {
    lineNumbers: true,
    mode: 'python',
    theme: 'eclipse'
});

document.getElementById('execute-code-btn').addEventListener('click', function () {
    const code = codeEditor.getValue();
    const language = document.getElementById('language-select').value;

    fetch('/execute_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language })
    })
        .then(response => response.json())
        .then(result => {
            document.getElementById('code-output').textContent = result.output;
        })
        .catch(() => {
            document.getElementById('execution-status').textContent = 'Execution failed.';
        });
});
