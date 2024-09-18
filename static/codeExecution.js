
// codeExecution.js

const codeTextarea = document.getElementById('code-input');
const codeOutput = document.getElementById('code-output');
const executionStatus = document.getElementById('execution-status');
const terminalWindow = document.getElementById('terminal-window');
const languageSelect = document.getElementById('language-select');

const codeEditor = CodeMirror.fromTextArea(codeTextarea, {
    lineNumbers: true,
    mode: 'python',  // Default mode
    theme: 'eclipse',
    indentUnit: 4,
    tabSize: 4
});

// Toggle terminal window visibility
document.getElementById('toggle-terminal-btn').addEventListener('click', function () {
    if (terminalWindow.style.display === 'none' || terminalWindow.style.display === '') {
        terminalWindow.style.display = 'block';
    } else {
        terminalWindow.style.display = 'none';
    }
});

languageSelect.addEventListener('change', function () {
    const language = this.value;
    const mode = {
        'python': 'python',
        'javascript': 'javascript',
        'bash': 'shell'
    }[language];
    codeEditor.setOption('mode', mode);
});

document.getElementById('execute-code-btn').addEventListener('click', function () {
    const code = codeEditor.getValue();
    const language = languageSelect.value;

    if (code.trim() === '') {
        alert('Please enter some code to execute.');
        return;
    }

    executionStatus.textContent = 'Executing code...';
    executionStatus.style.color = 'blue';

    fetch('/execute_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code, language: language })
    })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                codeOutput.textContent = result.output;
                codeOutput.style.color = 'black';
                executionStatus.textContent = 'Execution successful.';
                executionStatus.style.color = 'green';
            } else {
                codeOutput.textContent = result.output;
                codeOutput.style.color = 'red';
                executionStatus.textContent = 'Execution failed.';
                executionStatus.style.color = 'red';
            }
        })
        .catch(error => {
            console.error('Error executing code:', error);
            executionStatus.textContent = 'An error occurred.';
            executionStatus.style.color = 'red';
        });
});
