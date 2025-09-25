#!/bin/bash
echo "--- Starting Config Editor Setup ---"
echo "This script will install system packages, create a Python virtual environment, and set up the systemd service."

# Exit on any error
set -e

# --- Configuration ---
# The user the service will run as.
# The script will create this user if it doesn't exist.
SERVICE_USER="configeditor"
# The absolute path to the project directory.
# We get this from the script's own location.
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_PATH="${PROJECT_DIR}/backend/venv"

# --- Root Check ---
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root or with sudo."
  exit 1
fi

echo "Setup will be performed for user '${SERVICE_USER}' in directory '${PROJECT_DIR}'."

# --- Step 1: System Dependencies ---
echo "[1/5] Installing system dependencies (python3, pip, venv)..."
apt-get update
apt-get install -y python3 python3-pip python3-venv

# --- Step 2: Create Service User ---
echo "[2/5] Setting up service user '${SERVICE_USER}'..."
if id -u ${SERVICE_USER} >/dev/null 2>&1; then
    echo "User '${SERVICE_USER}' already exists. Skipping creation."
else
    useradd --system --no-create-home --shell /bin/false ${SERVICE_USER}
    echo "User '${SERVICE_USER}' created."
fi
# Grant ownership of the project directory to the service user
chown -R ${SERVICE_USER}:${SERVICE_USER} ${PROJECT_DIR}

# --- Step 3: Python Virtual Environment & Dependencies ---
echo "[3/5] Creating Python virtual environment and installing packages..."
# Run the following commands as the service user
sudo -u ${SERVICE_USER} bash << EOF
set -e
python3 -m venv ${VENV_PATH}
source ${VENV_PATH}/bin/activate
pip3 install -r ${PROJECT_DIR}/backend/requirements.txt
EOF

# --- Step 4: Database Setup ---
echo "[4/5] Setting up the database..."
# Run flask commands using the venv's python
sudo -u ${SERVICE_USER} bash << EOF
set -e
source ${VENV_PATH}/bin/activate
export FLASK_APP=${PROJECT_DIR}/backend/app.py
if [ ! -d "${PROJECT_DIR}/backend/migrations" ]; then
    echo "Initializing migrations..."
    flask db init -d ${PROJECT_DIR}/backend/migrations
fi
echo "Applying database migrations..."
flask db upgrade -d ${PROJECT_DIR}/backend/migrations
echo "Seeding initial data..."
flask seed
EOF

# --- Step 5: Systemd Service ---
echo "[5/5] Creating and enabling systemd service..."
# Note: This dynamically creates the service file with correct paths.
SERVICE_FILE_PATH="/etc/systemd/system/config-editor.service"
cat > ${SERVICE_FILE_PATH} << EOF
[Unit]
Description=Gunicorn instance to serve the Config Editor application
After=network.target

[Service]
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}/backend
ExecStart=${VENV_PATH}/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd daemon and enabling service..."
systemctl daemon-reload
systemctl enable config-editor.service
systemctl start config-editor.service

echo "--- Setup Complete ---"
echo "The Config Editor service is now running."
echo "You can check its status with: sudo systemctl status config-editor.service"