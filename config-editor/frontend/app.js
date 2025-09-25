document.addEventListener('DOMContentLoaded', () => {
    // --- Views ---
    const loginView = document.getElementById('login-view');
    const mainAppView = document.getElementById('main-app-view');
    const filesView = document.getElementById('files-view');
    const adminView = document.getElementById('admin-view');
    const welcomeMessage = document.getElementById('welcome-message');

    // --- Nav Links ---
    const viewFilesLink = document.getElementById('view-files-link');
    const viewAdminLink = document.getElementById('view-admin-link');

    // --- Forms ---
    const loginForm = document.getElementById('login-form');
    const passwordChangeForm = document.getElementById('password-change-form');
    const editorForm = document.getElementById('editor-form');
    const createUserForm = document.getElementById('create-user-form');
    const restoreUploadForm = document.getElementById('restore-upload-form');

    // --- Modals ---
    const passwordChangeModal = document.getElementById('password-change-modal');

    // --- Buttons ---
    const saveButton = document.getElementById('save-button');
    const logoutButton = document.getElementById('logout-button');
    const closeModalButton = document.getElementById('close-modal-button');
    const createBackupButton = document.getElementById('create-backup-button');
    const savePermissionsButton = document.getElementById('save-permissions-button');

    // --- Other ---
    const fileTreeContainer = document.getElementById('file-tree-container');
    const editorContainer = document.getElementById('editor-container');
    const editorHeader = document.getElementById('editor-header');
    const userListTbody = document.getElementById('user-list-tbody');
    const backupListTbody = document.getElementById('backup-list-tbody');
    const permissionsEditor = document.getElementById('permissions-editor');
    const permissionsUsername = document.getElementById('permissions-username');
    const permissionsTbody = document.getElementById('permissions-tbody');
    const themeSwitcher = document.getElementById('theme-switcher');
    const htmlElement = document.documentElement;

    // --- State ---
    let currentUser = null;
    let currentFile = null;
    let activeFileElement = null;
    let selectedUserForPermissions = null;

    // --- Constants ---
    const API_URL = 'http://127.0.0.1:5000';

    // ===================================================================
    // --- View Management & Core Flow ---
    // ===================================================================

    function showMainApp(userData) {
        currentUser = userData;
        loginView.classList.add('hidden');
        mainAppView.classList.remove('hidden');
        if (currentUser.is_admin) {
            viewAdminLink.classList.remove('hidden');
        } else {
            viewAdminLink.classList.add('hidden');
        }
        showFilesView();
    }

    function showLoginView() {
        mainAppView.classList.add('hidden');
        loginView.classList.remove('hidden');
        currentUser = null;
        document.cookie = "session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    }

    function showFilesView() {
        adminView.classList.add('hidden');
        filesView.classList.remove('hidden');
        viewAdminLink.classList.remove('active-nav');
        viewFilesLink.classList.add('active-nav');
        fetchFiles();
    }

    function showAdminView() {
        filesView.classList.add('hidden');
        adminView.classList.remove('hidden');
        viewFilesLink.classList.remove('active-nav');
        viewAdminLink.classList.add('active-nav');
        loadUsers();
        loadBackups();
    }

    async function checkInitialStatus() {
        try {
            const response = await fetch(`${API_URL}/api/status`, {credentials: 'include'});
            if (response.ok) {
                const data = await response.json();
                if (data.auth && data.auth.logged_in) {
                    if (data.auth.must_change_password) {
                        currentUser = data.auth;
                        passwordChangeModal.showModal();
                    } else {
                        showMainApp(data.auth);
                    }
                }
            }
        } catch (e) {
            console.error("Could not reach backend. Showing login page.");
        }
    }

    // ===================================================================
    // --- API & Data Functions ---
    // ===================================================================

    async function fetchFiles() {
        try {
            const response = await fetch(`${API_URL}/api/files`, {credentials: 'include'});
            if (!response.ok) throw new Error('Failed to fetch files.');
            const files = await response.json();
            renderFileTree(files);
        } catch (error) {
            fileTreeContainer.innerHTML = `<p>Error: ${error.message}</p>`;
        }
    }

    async function loadFileContent(filePath) {
        currentFile = filePath;
        editorHeader.textContent = `Editing: ${filePath}`;
        welcomeMessage.classList.add('hidden');
        editorContainer.classList.remove('hidden');
        editorForm.innerHTML = '<p>Loading...</p>';
        saveButton.classList.add('hidden');

        try {
            const response = await fetch(`${API_URL}/api/files/content?path=${encodeURIComponent(filePath)}`, {credentials: 'include'});
            const data = await response.json();
            if (!response.ok) {
                if (data.status === 'parse_error') {
                    editorForm.innerHTML = `<p style="color: red;"><strong>Error parsing file:</strong> ${data.error}</p>`;
                } else {
                    throw new Error(data.error || 'Failed to load file content.');
                }
            } else {
                renderEditor(data);
            }
        } catch (error) {
            editorForm.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    }

    async function loadUsers() {
        try {
            const response = await fetch(`${API_URL}/api/users`, {credentials: 'include'});
            const users = await response.json();
            userListTbody.innerHTML = '';
            users.forEach(user => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${user.username}</td>
                    <td>${user.is_admin ? 'Yes' : 'No'}</td>
                    <td><button class="outline" data-user-id="${user.id}" data-username="${user.username}" ${user.is_admin ? 'disabled' : ''}>Permissions</button></td>
                `;
                tr.querySelector('button').addEventListener('click', (e) => {
                    showPermissionsEditor(e.target.dataset.userId, e.target.dataset.username);
                });
                userListTbody.appendChild(tr);
            });
        } catch (error) {
            console.error("Failed to load users:", error);
        }
    }

    async function loadBackups() {
        try {
            const response = await fetch(`${API_URL}/api/backups`, {credentials: 'include'});
            const backups = await response.json();
            backupListTbody.innerHTML = '';
            backups.forEach(filename => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${filename}</td>
                    <td><button class="outline" data-filename="${filename}">Restore</button></td>
                `;
                tr.querySelector('button').addEventListener('click', () => {
                    const password = prompt(`Enter admin password to restore ${filename}:`);
                    if (password) {
                        restoreFromServer(filename, password);
                    }
                });
                backupListTbody.appendChild(tr);
            });
        } catch (error) {
            console.error("Failed to load backups:", error);
        }
    }

    async function restoreFromServer(filename, password) {
        try {
            const response = await fetch(`${API_URL}/api/backups/restore_from_server`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename, password }),
                credentials: 'include'
            });
            if (!response.ok) throw new Error((await response.json()).error);
            alert('Restore successful! Refreshing file list.');
            fetchFiles();
        } catch (error) {
            alert(`Restore failed: ${error.message}`);
        }
    }

    async function showPermissionsEditor(userId, username) {
        selectedUserForPermissions = userId;
        permissionsUsername.textContent = username;
        permissionsEditor.classList.remove('hidden');
        permissionsTbody.innerHTML = '<tr><td colspan="2">Loading...</td></tr>';

        try {
            const [filesRes, permsRes] = await Promise.all([
                fetch(`${API_URL}/api/files`, {credentials: 'include'}),
                fetch(`${API_URL}/api/permissions/${userId}`, {credentials: 'include'})
            ]);
            const allFiles = await filesRes.json();
            const currentPerms = await permsRes.json();

            permissionsTbody.innerHTML = '';
            allFiles.forEach(file => {
                const currentLevel = currentPerms[file.path] || 'none';
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${file.path}</td>
                    <td>
                        <select data-file-path="${file.path}">
                            <option value="none" ${currentLevel === 'none' ? 'selected' : ''}>None</option>
                            <option value="read" ${currentLevel === 'read' ? 'selected' : ''}>Read</option>
                            <option value="write" ${currentLevel === 'write' ? 'selected' : ''}>Write</option>
                        </select>
                    </td>
                `;
                permissionsTbody.appendChild(tr);
            });
        } catch (error) {
            permissionsTbody.innerHTML = `<tr><td colspan="2" style="color:red;">Error loading permissions.</td></tr>`;
        }
    }

    // ===================================================================
    // --- UI Rendering ---
    // ===================================================================
    function renderFileTree(files) {
        if (files.length === 0) {
            fileTreeContainer.innerHTML = '<p>No files found.</p>';
            return;
        }
        const ul = document.createElement('ul');
        files.forEach(file => {
            const a = document.createElement('a');
            a.href = '#';
            a.textContent = file.path;
            a.dataset.path = file.path;

            a.classList.remove('access-read', 'access-none');
            if (file.access_level === 'read') {
                a.classList.add('access-read');
            } else if (file.access_level === 'none') {
                a.classList.add('access-none');
            }

            if (file.access_level !== 'none') {
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (activeFileElement) activeFileElement.classList.remove('active');
                    activeFileElement = a;
                    a.classList.add('active');
                    loadFileContent(file.path);
                });
            }

            const li = document.createElement('li');
            li.appendChild(a);
            ul.appendChild(li);
        });
        fileTreeContainer.innerHTML = '';
        fileTreeContainer.appendChild(ul);
    }

    function buildFormFragment(data, parentKey = '') {
        const fragment = document.createDocumentFragment();
        for (const key in data) {
            const value = data[key];
            const currentKey = parentKey ? `${parentKey}.${key}` : key;
            const div = document.createElement('div');
            if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                const fieldset = document.createElement('fieldset');
                const legend = document.createElement('legend');
                legend.textContent = key;
                fieldset.appendChild(legend);
                fieldset.appendChild(buildFormFragment(value, currentKey));
                div.appendChild(fieldset);
            } else {
                const label = document.createElement('label');
                label.textContent = key;
                const input = document.createElement('input');
                if (typeof value === 'boolean') {
                    input.type = 'checkbox';
                    input.checked = value;
                } else {
                    input.type = typeof value === 'number' ? 'number' : 'text';
                    input.value = Array.isArray(value) ? JSON.stringify(value) : value;
                }
                input.id = currentKey;
                input.dataset.key = currentKey;
                label.htmlFor = currentKey;
                div.appendChild(label);
                div.appendChild(input);
            }
            fragment.appendChild(div);
        }
        return fragment;
    }

    function renderEditor(data) {
        editorForm.innerHTML = '';
        const formFragment = buildFormFragment(data);
        editorForm.appendChild(formFragment);
        saveButton.classList.remove('hidden');
        saveButton.disabled = true;
    }

    function formToJson() {
        const data = {};
        const inputs = editorForm.querySelectorAll('input');
        inputs.forEach(input => {
            const keys = input.dataset.key.split('.');
            let current = data;
            for (let i = 0; i < keys.length; i++) {
                const key = keys[i];
                if (i === keys.length - 1) {
                    let value;
                    if (input.type === 'checkbox') {
                        value = input.checked;
                    } else if (input.type === 'number') {
                        value = parseFloat(input.value) || 0;
                    } else {
                        try {
                            value = JSON.parse(input.value);
                        } catch (e) {
                            value = input.value;
                        }
                    }
                    current[key] = value;
                } else {
                    current[key] = current[key] || {};
                    current = current[key];
                }
            }
        });
        // The form builder creates a single root object which is what the XML parser expects.
        // For other formats, they expect the raw inner object.
        // This is a simplification; a more robust solution would track the format.
        // For now, we return the whole structure for XML and the inner object for others.
        const isXml = currentFile && currentFile.toLowerCase().endsWith('.xml');
        return isXml ? data : data[Object.keys(data)[0]];
    }

    // ===================================================================
    // --- Event Listeners ---
    // ===================================================================

    viewFilesLink.addEventListener('click', (e) => { e.preventDefault(); showFilesView(); });
    viewAdminLink.addEventListener('click', (e) => { e.preventDefault(); showAdminView(); });

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = loginForm.username.value;
        const password = loginForm.password.value;
        try {
            const response = await fetch(`${API_URL}/api/login`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });
            if (!response.ok) throw new Error((await response.json()).error || 'Login failed.');
            const userData = await response.json();
            if (userData.must_change_password) {
                currentUser = userData;
                passwordChangeModal.showModal();
            } else {
                showMainApp(userData);
            }
        } catch (error) {
            alert(`Login failed: ${error.message}`);
        }
    });

    logoutButton.addEventListener('click', async (e) => {
        e.preventDefault();
        await fetch(`${API_URL}/api/logout`, { method: 'POST', credentials: 'include' });
        showLoginView();
    });

    passwordChangeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const current_password = passwordChangeForm.current_password.value;
        const new_password = passwordChangeForm.new_password.value;
        try {
            const response = await fetch(`${API_URL}/api/users/change_password`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_password, new_password }), credentials: 'include'
            });
            if (!response.ok) throw new Error((await response.json()).error || 'Password change failed.');
            alert('Password changed successfully.');
            passwordChangeModal.close();
            currentUser.must_change_password = false;
            showMainApp(currentUser);
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });

    closeModalButton.addEventListener('click', (e) => { e.preventDefault(); passwordChangeModal.close(); });

    editorForm.addEventListener('input', () => { saveButton.disabled = false; });

    saveButton.addEventListener('click', async () => {
        const updatedData = formToJson();
        saveButton.disabled = true;
        try {
            const response = await fetch(`${API_URL}/api/files/content?path=${encodeURIComponent(currentFile)}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedData),
                credentials: 'include'
            });
            if (!response.ok) throw new Error((await response.json()).error || 'Failed to save.');
            alert('File saved successfully!');
        } catch (error) {
            alert(`Error saving file: ${error.message}`);
            saveButton.disabled = false;
        }
    });

    themeSwitcher.addEventListener('click', (e) => {
        e.preventDefault();
        const newTheme = htmlElement.dataset.theme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        htmlElement.dataset.theme = newTheme;
    });

    createUserForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = createUserForm.new_username.value;
        const password = createUserForm.new_user_password.value;
        const is_admin = createUserForm.new_user_is_admin.checked;
        try {
            const response = await fetch(`${API_URL}/api/users/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, is_admin }),
                credentials: 'include'
            });
            if (!response.ok) throw new Error((await response.json()).error);
            alert('User created successfully!');
            createUserForm.reset();
            loadUsers();
        } catch (error) {
            alert(`Error creating user: ${error.message}`);
        }
    });

    savePermissionsButton.addEventListener('click', async () => {
        const selects = permissionsTbody.querySelectorAll('select');
        const promises = [];
        selects.forEach(select => {
            const file_path = select.dataset.filePath;
            const access_level = select.value;
            const promise = fetch(`${API_URL}/api/permissions/grant`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: selectedUserForPermissions,
                    file_path,
                    access_level
                }),
                credentials: 'include'
            });
            promises.push(promise);
        });

        try {
            await Promise.all(promises);
            alert('Permissions saved successfully!');
            permissionsEditor.classList.add('hidden');
        } catch (error) {
            alert('An error occurred while saving permissions.');
        }
    });

    // --- Initial Load ---
    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlElement.dataset.theme = savedTheme;
    checkInitialStatus();
});