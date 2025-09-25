#!/bin/bash
echo "--- Starting Config Editor Setup ---"

# Exit on any error
set -e

# Change to the script's directory to ensure paths are correct
cd "$(dirname "$0")"

# 1. Check for Python and Pip
echo "[1/4] Checking for Python 3 and Pip..."
if ! command -v python3 &> /dev/null
then
    echo "Python 3 could not be found. Please install it."
    exit 1
fi
if ! command -v pip3 &> /dev/null
then
    echo "Pip3 could not be found. Please install it (e.g., sudo apt install python3-pip)."
    exit 1
fi

# 2. Install dependencies
echo "[2/4] Installing Python dependencies..."
pip3 install -r backend/requirements.txt

# 3. Setup Database
echo "[3/4] Setting up the database..."
export FLASK_APP=backend/app.py
# This will create the migrations folder on first run
if [ ! -d "backend/migrations" ]; then
    echo "Initializing migrations..."
    flask db init -d backend/migrations
fi
echo "Applying database migrations..."
flask db upgrade -d backend/migrations

# 4. Seed initial data
echo "[4/4] Seeding initial data (creating admin user)..."
flask seed

echo "--- Setup Complete ---"
echo "You can now run the application using:"
echo "gunicorn --chdir backend --bind 0.0.0.0:5000 app:app"
echo "Or by enabling the systemd service."