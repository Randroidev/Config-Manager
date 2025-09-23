# Makefile for the Config Editor application

# Use bash for all shell commands
SHELL := /bin/bash

# Default target
all: setup

# Target to set up the entire application
setup:
	@echo "--- Starting Config Editor Setup ---"
	@echo "[1/4] Installing Python dependencies..."
	pip3 install -r backend/requirements.txt
	@echo "[2/4] Setting up the database..."
	@export FLASK_APP=backend/app.py && \
	if [ ! -d "backend/migrations" ]; then \
		echo "Initializing migrations..."; \
		flask db init -d backend/migrations; \
	fi
	@echo "Applying database migrations..."
	@export FLASK_APP=backend/app.py && flask db upgrade -d backend/migrations
	@echo "[3/4] Seeding initial data (creating admin user)..."
	@export FLASK_APP=backend/app.py && flask seed
	@echo "[4/4] Creating sample config directory..."
	@mkdir -p config/nested
	@echo "--- Setup Complete ---"
	@echo "You can now run the application using:"
	@echo "gunicorn --chdir backend --bind 0.0.0.0:5000 app:app"

# Target to run the development server
run:
	@echo "Starting development server..."
	@FLASK_APP=backend/app.py flask run

# Target to clean up generated files
clean:
	@echo "Cleaning up..."
	@rm -rf backend/migrations
	@rm -f backend/app.db
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
.PHONY: all setup run clean
