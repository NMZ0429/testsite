document.addEventListener('DOMContentLoaded', e => {
    for (const textarea of document.querySelectorAll('textarea.markdown')) {
        const simplemde = new SimpleMDE({
            element: textarea,
            forceSync: true,
            spellChecker: false,
        });

        const display = textarea.parentNode.querySelector('div.CodeMirror');
        display.addEventListener('dragover', e => {
            e.preventDefault();
        });

        display.addEventListener('drop', e => {
            e.preventDefault();
            upload(simplemde, e.dataTransfer.files[0], textarea);
        });
    }
});
