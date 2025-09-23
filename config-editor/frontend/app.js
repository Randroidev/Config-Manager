document.addEventListener('DOMContentLoaded', () => {
    const fileTreeContainer = document.getElementById('file-tree-container');
    const editorContainer = document.getElementById('editor-container');
    const editorHeader = document.getElementById('editor-header');
    const editorForm = document.getElementById('editor-form');
    const saveButton = document.getElementById('save-button');
    const welcomeMessage = document.getElementById('welcome-message');
    const themeSwitcher = document.getElementById('theme-switcher');
    const htmlElement = document.documentElement;

    let currentFile = null;
    let activeFileElement = null;
    let isXml = false;

    const API_URL = 'http://127.0.0.1:5000';

    async function fetchFiles() {
        try {
            const response = await fetch(`${API_URL}/api/files`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const files = await response.json();
            renderFileTree(files);
        } catch (error) {
            fileTreeContainer.innerHTML = '<p>Error loading files. Is the backend running?</p>';
        }
    }

    function renderFileTree(files) {
        if (files.length === 0) {
            fileTreeContainer.innerHTML = '<p>No config files found.</p>';
            return;
        }
        const ul = document.createElement('ul');
        files.forEach(file => {
            const a = document.createElement('a');
            a.href = '#';
            a.textContent = file.name;
            a.dataset.path = file.path;
            a.addEventListener('click', (e) => {
                e.preventDefault();
                if (activeFileElement) activeFileElement.classList.remove('active');
                activeFileElement = a;
                activeFileElement.classList.add('active');
                loadFileContent(file.path);
            });
            const li = document.createElement('li');
            li.appendChild(a);
            ul.appendChild(li);
        });
        fileTreeContainer.innerHTML = '';
        fileTreeContainer.appendChild(ul);
    }

    async function loadFileContent(filePath) {
        currentFile = filePath;
        isXml = filePath.toLowerCase().endsWith('.xml');
        editorHeader.textContent = `Editing: ${filePath}`;
        welcomeMessage.classList.add('hidden');
        editorContainer.classList.remove('hidden');
        editorForm.innerHTML = '<p>Loading content...</p>';
        saveButton.classList.add('hidden');

        try {
            const response = await fetch(`${API_URL}/api/files/content?path=${encodeURIComponent(filePath)}`);
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || `HTTP error! status: ${response.status}`);
            }
            const content = await response.json();
            renderEditor(content);
        } catch (error) {
            editorForm.innerHTML = `<p style="color: var(--pico-del-color);">Error loading file: ${error.message}</p>`;
        }
    }

    function buildFormFragment(data, parentKey = '') {
        const fragment = document.createDocumentFragment();
        for (const key in data) {
            const value = data[key];
            const currentKey = parentKey ? `${parentKey}.${key}` : key;

            if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                const fieldset = document.createElement('fieldset');
                const legend = document.createElement('legend');
                legend.textContent = key;
                fieldset.appendChild(legend);
                fieldset.appendChild(buildFormFragment(value, currentKey));
                fragment.appendChild(fieldset);
            } else {
                const label = document.createElement('label');
                label.textContent = key;
                const input = document.createElement('input');
                input.type = typeof value === 'number' ? 'number' : 'text';
                if (typeof value === 'boolean') {
                    input.type = 'checkbox';
                    input.checked = value;
                } else {
                    input.value = Array.isArray(value) ? JSON.stringify(value) : value;
                }
                input.id = currentKey;
                input.dataset.key = currentKey;
                label.htmlFor = currentKey;

                const div = document.createElement('div');
                div.appendChild(label);
                div.appendChild(input);
                fragment.appendChild(div);
            }
        }
        return fragment;
    }

    function renderEditor(data) {
        editorForm.innerHTML = '';
        if (isXml) {
            const pre = document.createElement('pre');
            pre.textContent = JSON.stringify(data, null, 2);
            const p = document.createElement('p');
            p.innerHTML = '<i>XML editing is not yet supported. Displaying read-only view.</i>';
            editorForm.appendChild(p);
            editorForm.appendChild(pre);
            saveButton.classList.add('hidden');
        } else {
            const formFragment = buildFormFragment(data);
            editorForm.appendChild(formFragment);
            saveButton.classList.remove('hidden');
            saveButton.disabled = true;
        }
    }

    function formToJson() {
        const data = {};
        const inputs = editorForm.querySelectorAll('input');
        inputs.forEach(input => {
            const keys = input.dataset.key.split('.');
            let current = data;
            keys.forEach((key, index) => {
                if (index === keys.length - 1) {
                    let value = input.value;
                    if (input.type === 'checkbox') value = input.checked;
                    if (input.type === 'number') value = parseFloat(value);
                    try {
                        // Try to parse arrays/objects back from string
                        value = JSON.parse(value);
                    } catch (e) {
                        // Not a JSON string, keep as is
                    }
                    current[key] = value;
                } else {
                    current[key] = current[key] || {};
                    current = current[key];
                }
            });
        });
        return data;
    }

    editorForm.addEventListener('input', () => {
        if (!isXml) saveButton.disabled = false;
    });

    saveButton.addEventListener('click', async () => {
        const updatedData = formToJson();
        saveButton.textContent = 'Saving...';
        saveButton.disabled = true;
        saveButton.setAttribute('aria-busy', 'true');

        try {
            const response = await fetch(`${API_URL}/api/files/content?path=${encodeURIComponent(currentFile)}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData),
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Failed to save.');
            }
            alert('File saved successfully!');
        } catch (error) {
            alert(`Error saving file: ${error.message}`);
        } finally {
            saveButton.textContent = 'Save Changes';
            saveButton.disabled = true;
            saveButton.removeAttribute('aria-busy');
        }
    });

    // --- Theme Switcher Logic ---
    function applyTheme(theme) {
        htmlElement.dataset.theme = theme;
        if (theme === 'dark') {
            themeSwitcher.textContent = 'Switch to Light';
        } else {
            themeSwitcher.textContent = 'Switch to Dark';
        }
    }

    themeSwitcher.addEventListener('click', (e) => {
        e.preventDefault();
        const newTheme = htmlElement.dataset.theme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    });

    // Apply saved theme on load
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);


    // Initial fetch of files
    fetchFiles();
});
