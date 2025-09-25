import os
import yaml
import pam
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, flash
from .decorators import login_required, setup_required

# --- Constants ---
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'config.yaml'))

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Configuration Loading ---
def load_config():
    """Loads configuration from config.yaml"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        raise SystemExit(f"FATAL: Could not load or parse config.yaml. Error: {e}")

app_config = load_config()
app.config.update(app_config)
app.config['SECRET_KEY'] = app.config['security'].get('secret_key') or os.urandom(32)


# --- User & Password Utilities ---
def update_config_file(new_config_data):
    """Atomically writes the updated configuration back to the file."""
    try:
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(new_config_data, f, default_flow_style=False, sort_keys=False)
        app.config.update(new_config_data)
    except IOError as e:
        flash(f"Critical error updating config file: {e}", "error")

def hash_password(password, salt):
    """Hashes a password with the given salt."""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()


# --- Core Routes ---
@app.route('/')
@setup_required
@login_required
def index():
    """Main application page."""
    return render_template('index.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial setup page for setting admin password and managed directory."""
    if app.config['security']['initial_setup_complete']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        managed_dir = request.form.get('managed_dir')

        if not all([password, password_confirm, managed_dir]):
            flash("All fields are required.", "error")
            return render_template('setup.html')

        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template('setup.html')

        if not os.path.isdir(managed_dir):
            flash("The specified directory does not exist or is not a directory.", "error")
            return render_template('setup.html')

        new_secret_key = os.urandom(32).hex()
        new_salt = os.urandom(16)
        new_password_hash = hash_password(password, new_salt)

        current_config_data = load_config()
        current_config_data['security']['secret_key'] = new_secret_key
        current_config_data['security']['password_hash_salt'] = new_salt.hex()
        current_config_data['security']['admin_password_hash'] = new_password_hash
        current_config_data['security']['initial_setup_complete'] = True
        current_config_data['app_settings']['managed_configs_dir'] = managed_dir

        update_config_file(current_config_data)

        app.config['SECRET_KEY'] = new_secret_key

        flash("Setup complete! Please log in with your new password.", "success")
        return redirect(url_for('login'))

    return render_template('setup.html')

@app.route('/login', methods=['GET', 'POST'])
@setup_required
def login():
    """Login page for system users."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template('login.html')

        p = pam.pam()
        if p.authenticate(username, password):
            session['username'] = username
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid system username or password.", "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logs the user out."""
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# --- РЕГИСТРАЦИЯ API ---
from .api import api_bp
app.register_blueprint(api_bp)


if __name__ == '__main__':
    app.run(
        host=app.config['server']['host'],
        port=app.config['server']['port'],
        debug=True
    )