import os
import yaml
import pam
import hashlib
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

# --- Constants ---
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'config.yaml'))


# --- Configuration Loading ---
def load_config():
    """Loads configuration from config.yaml"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        # This is a critical error, app cannot start without config
        raise SystemExit(f"FATAL: Could not load or parse config.yaml. Error: {e}")

config = load_config()


# --- Flask App Initialization ---
app = Flask(__name__)
# Load secret key from config, but handle the case where it's not set yet
app.config['SECRET_KEY'] = config['security'].get('secret_key') or os.urandom(32)

# Import and register the API blueprint
from .api import api_bp
app.register_blueprint(api_bp)


# --- Decorators for Authentication & Setup ---
def setup_required(f):
    """Redirects to setup page if initial setup is not complete."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not config['security']['initial_setup_complete']:
            return redirect(url_for('setup'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """Redirects to login page if user is not logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# --- User & Password Utilities ---
def update_config_file(new_config):
    """Atomically writes the updated configuration back to the file."""
    global config
    try:
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)
        config = new_config # Update in-memory config
    except IOError as e:
        # Handle file write error
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
    if config['security']['initial_setup_complete']:
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

        # Generate new security credentials
        new_secret_key = os.urandom(32).hex()
        new_salt = os.urandom(16)
        new_password_hash = hash_password(password, new_salt)

        # Update the config object
        new_config = config.copy()
        new_config['security']['secret_key'] = new_secret_key
        new_config['security']['password_hash_salt'] = new_salt.hex()
        new_config['security']['admin_password_hash'] = new_password_hash
        new_config['security']['initial_setup_complete'] = True
        new_config['app_settings']['managed_configs_dir'] = managed_dir

        # Write to file
        update_config_file(new_config)

        # Update flask app's secret key
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

        # Use PAM for system user authentication
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


if __name__ == '__main__':
    # This is for development only. Use a proper WSGI server in production.
    app.run(
        host=config['server']['host'],
        port=config['server']['port'],
        debug=True
    )