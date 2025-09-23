# Config Editor

Config Editor is a web-based application designed for managing configuration files on a Linux server. It provides a user-friendly interface to view, edit, and manage various configuration file formats in a centralized location.

## Features

- **Web-based UI:** Modern, clean interface for editing files. Light and dark themes are supported.
- **Multi-Format Support:** Out-of-the-box support for `.ini`, `.cfg`, `.conf`, `.json`, `.xml`, and `.yaml` files.
- **Recursive File Discovery:** Automatically finds configuration files in the specified directory and its subdirectories.
- **User Authentication:** Secure login system for multiple users.
- **Granular Permissions:** Admins can create users and grant per-file 'read' or 'write' access.
- **Encrypted Backups:** Admins can create and restore encrypted, password-protected backups of the entire configuration directory.
- **Systemd Service:** A template service file is provided for running the application as a system service in production.
- **Automated Setup:** Includes a setup script to install dependencies and initialize the database.

## Prerequisites

- Python 3.8+
- `pip` for Python 3

## Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd config-editor
    ```

2.  **Run the Setup Script:**
    The provided setup script will install dependencies, create the database, and create the initial `admin` user (password: `admin`).

    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```
    *Note: The script may require `sudo` if you are installing packages system-wide or if it needs to create directories in protected locations.*

## Configuration

The application is configured via the `config/app_config.json` file. You can edit this file to change the application's behavior.

```json
{
    "server_host": "0.0.0.0",
    "server_port": 5000,
    "config_files_directory": "../config",
    "database_path": "../backend/app.db",
    "backup_directory": "../backups"
}
```

- `server_host`: The IP address the web server will bind to. `0.0.0.0` makes it accessible on the network.
- `server_port`: The port the web server will listen on.
- `config_files_directory`: The path (relative to the `backend` directory) where your configuration files are stored.
- `database_path`: The path where the application's SQLite database will be stored.
- `backup_directory`: The path where encrypted backups will be saved.

**Important:** For changes to `server_host` or `server_port` to take effect, you must restart the application.

## Running the Application

### Development Mode

For development, you can use the built-in Flask server. From the `config-editor` directory:

```bash
export FLASK_APP=backend/app.py
flask run --host=0.0.0.0 --port=5000
```

### Production Mode

For production, it is highly recommended to use a WSGI server like Gunicorn. The `setup.sh` script installs Gunicorn for you. From the `config-editor` directory:

```bash
gunicorn --chdir backend --workers 4 --bind 0.0.0.0:5000 app:app
```

## Deployment as a Systemd Service

A template service file, `config-editor.service`, is provided.

1.  **Edit the Service File:**
    Open `config-editor.service` and replace the placeholders:
    - `User=your_user`: Change to the user you want the service to run as.
    - `WorkingDirectory=/path/to/your/project/config-editor`: Change to the absolute path of this project directory.
    - `ExecStart=/path/to/gunicorn`: Change to the absolute path of your `gunicorn` executable (find with `which gunicorn`).

2.  **Install and Enable the Service:**
    ```bash
    # Copy the file to the systemd directory
    sudo cp config-editor.service /etc/systemd/system/config-editor.service

    # Reload the systemd daemon to recognize the new service
    sudo systemctl daemon-reload

    # Enable the service to start on boot
    sudo systemctl enable config-editor.service

    # Start the service immediately
    sudo systemctl start config-editor.service
    ```

3.  **Check Service Status:**
    ```bash
    sudo systemctl status config-editor.service
    ```
