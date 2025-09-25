document.addEventListener('DOMContentLoaded', () => {
    const fileTreeContainer = document.getElementById('file-tree');
    const editorSpace = document.getElementById('editor-space');
    let activeFilePath = null;

    // --- Утилиты ---
    function showLoader(container) {
        container.innerHTML = '<div class="loader">Loading...</div>';
    }

    function showError(container, message) {
        container.innerHTML = `<div class="error-message">${message}</div>`;
    }

    // --- Логика дерева файлов ---
    function renderFileTree(nodes) {
        if (!nodes || nodes.length === 0) {
            return '<em>No files found.</em>';
        }
        // 'error' is a special key returned by the backend script
        if (nodes.error) {
             return `<div class="error-message">Error loading file tree: ${nodes.error}</div>`;
        }

        let html = '<ul>';
        nodes.forEach(node => {
            const isDir = node.type === 'directory';
            const perms = node.permissions || {};
            let classes = `tree-node ${node.type}`;
            if (!perms.readable) classes += ' no-read';
            if (perms.readable && !perms.writable) classes += ' read-only';

            html += `<li class="${classes}" data-path="${node.path}" data-type="${node.type}">`;
            html += `<span class="node-name">${isDir ? '&#128194;' : '&#128441;'} ${node.name}</span>`;

            if (isDir && node.children) {
                html += renderFileTree(node.children);
            }
            html += '</li>';
        });
        html += '</ul>';
        return html;
    }

    async function loadFileTree() {
        showLoader(fileTreeContainer);
        try {
            const response = await fetch('/api/files/tree');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const treeData = await response.json();
            fileTreeContainer.innerHTML = renderFileTree(treeData);
        } catch (error) {
            showError(fileTreeContainer, `Failed to load file tree: ${error.message}`);
        }
    }

    // --- Логика редактора ---
    function renderEditor(data) {
        // Эта функция будет сложной, пока сделаем заглушку
        editorSpace.innerHTML = `
            <h3>Editing: ${data.path}</h3>
            <textarea class="raw-editor">${data.raw_content}</textarea>
            <hr>
            <h4>Parsed Data:</h4>
            <pre>${JSON.stringify(data.data, null, 2)}</pre>
            <div class="editor-actions">
                <button id="save-btn" class="btn btn-primary">Save</button>
            </div>
        `;
    }

    async function loadAndRenderFile(path) {
        showLoader(editorSpace);
        activeFilePath = path;
        try {
            const response = await fetch(`/api/files/content?path=${encodeURIComponent(path)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const fileData = await response.json();

            if (fileData.error) {
                showError(editorSpace, `Error loading file: ${fileData.error}`);
                return;
            }

            renderEditor(fileData);

        } catch (error) {
            showError(editorSpace, `Failed to load file content: ${error.message}`);
        }
    }


    // --- Обработчики событий ---
    fileTreeContainer.addEventListener('click', (event) => {
        const targetNode = event.target.closest('.tree-node');
        if (!targetNode) return;

        const path = targetNode.dataset.path;
        const type = targetNode.dataset.type;

        if (type === 'file') {
            loadAndRenderFile(path);

            // Подсветка активного файла
            document.querySelectorAll('.tree-node.active').forEach(n => n.classList.remove('active'));
            targetNode.classList.add('active');
        } else if (type === 'directory') {
            // "Сворачивание" и "разворачивание" папок
            targetNode.classList.toggle('collapsed');
        }
    });


    // --- Инициализация ---
    loadFileTree();
});