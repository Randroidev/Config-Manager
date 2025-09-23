document.addEventListener('DOMContentLoaded', () => {
    // --- Views ---
    const loginView = document.getElementById('login-view');
    const mainAppView = document.getElementById('main-app-view');
    const filesView = document.getElementById('files-view');
    const adminView = document.getElementById('admin-view');

    // --- Nav Links ---
    const viewFilesLink = document.getElementById('view-files-link');
    const viewAdminLink = document.getElementById('view-admin-link');

    // --- Forms ---
    const loginForm = document.getElementById('login-form');
    const passwordChangeForm = document.getElementById('password-change-form');
    const editorForm = document.getElementById('editor-form');
    const createUserForm = document.getElementById('create-user-form');

    // --- Modals ---
    const passwordChangeModal = document.getElementById('password-change-modal');

    // --- Main App Components ---
    const fileTreeContainer = document.getElementById('file-tree-container');
    const editorContainer = document.getElementById('editor-container');
    const editorHeader = document.getElementById('editor-header');
    const saveButton = document.getElementById('save-button');
    const logoutButton = document.getElementById('logout-button');
    const closeModalButton = document.getElementById('close-modal-button');
    const userListTbody = document.getElementById('user-list-tbody');

    // --- State ---
    let currentUser = null;

    // --- Constants ---
    const API_URL = 'http://127.0.0.1:5000';

    // ===================================================================
    // --- View Management ---
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
    }

    // ===================================================================
    // --- Admin Panel Functions ---
    // ===================================================================

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
                    <td><button class="outline" data-user-id="${user.id}">Manage Permissions</button></td>
                `;
                userListTbody.appendChild(tr);
            });
        } catch (error) {
            console.error("Failed to load users:", error);
        }
    }

    // ===================================================================
    // --- Event Listeners ---
    // ===================================================================

    viewFilesLink.addEventListener('click', (e) => { e.preventDefault(); showFilesView(); });
    viewAdminLink.addEventListener('click', (e) => { e.preventDefault(); showAdminView(); });

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        // ... (login logic is the same)
    });

    logoutButton.addEventListener('click', async (e) => {
        e.preventDefault();
        await fetch(`${API_URL}/api/logout`, { method: 'POST', credentials: 'include' });
        showLoginView();
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
            loadUsers(); // Refresh the user list
        } catch (error) {
            alert(`Error creating user: ${error.message}`);
        }
    });

    // ... (other event listeners are the same)

    // --- Initial Load ---
    // ... (checkInitialStatus is the same)
});
