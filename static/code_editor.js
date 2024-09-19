
// code_editor.js
document.addEventListener('DOMContentLoaded', () => {
    const codeEditor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        lineNumbers: true,
        mode: 'python',
        theme: 'eclipse'
    });

    document.getElementById('run-code').addEventListener('click', () => {
        const code = codeEditor.getValue();
        executeCode(code);
    });

    function executeCode(code) {
        // Here, you would send the code to the server to be executed
        console.log('Executing code:', code);
        // This is a placeholder; integrate with backend to run code
    }
});
