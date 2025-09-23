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
        }
        showFilesView();
    }

    function showLoginView() { /* ... */ }
    function showFilesView() { /* ... */ }

    function showAdminView() {
        filesView.classList.add('hidden');
        adminView.classList.remove('hidden');
        viewFilesLink.classList.remove('active-nav');
        viewAdminLink.classList.add('active-nav');
        loadUsers();
        loadBackups();
    }

    async function checkInitialStatus() { /* ... */ }

    // ===================================================================
    // --- API & Data Functions ---
    // ===================================================================

    async function fetchFiles() { /* ... */ }
    async function loadFileContent(filePath) { /* ... */ }
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
    async function loadBackups() { /* ... */ }
    async function restoreFromServer(filename, password) { /* ... */ }

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
    // ... (All functions are the same)

    // ===================================================================
    // --- Event Listeners ---
    // ===================================================================

    // ... (Most listeners are the same)

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
    checkInitialStatus();
});
// Note: This is a highly condensed version showing only the new/changed parts.
// The full file will be written now.
