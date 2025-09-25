import os
import io
import json
import tarfile
import datetime
import shutil
from functools import wraps
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import click

from parsers import get_parser
import crypto

# --- App Initialization & Config Loading ---
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = 'a-very-secret-key-that-should-be-changed'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# A default config path used to find the config file itself
DEFAULT_CONFIG_DIR = os.path.normpath(os.path.join(APP_DIR, '../config'))

# Load app_config.json
try:
    with open(os.path.join(DEFAULT_CONFIG_DIR, 'app_config.json')) as f:
        app_config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    app_config = {
        "server_host": "0.0.0.0", "server_port": 5000,
        "config_files_directory": "../config",
        "database_path": "app.db",
        "backup_directory": "../backups"
    }

# --- Path and DB Configuration ---
# Use the loaded config to define the actual paths
CONFIG_DIR = os.path.normpath(os.path.join(APP_DIR, app_config['config_files_directory']))
DB_PATH = os.path.normpath(os.path.join(APP_DIR, app_config['database_path']))
BACKUP_DIR = os.path.normpath(os.path.join(APP_DIR, app_config['backup_directory']))
SUPPORTED_EXTENSIONS = ['.ini', '.cfg', '.conf', '.config', '.xml', '.yml', '.yaml', '.json']

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

# --- Extensions Initialization ---
db = SQLAlchemy(app)
migrate = Migrate(app, db) # Using Migrate for schema management
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    must_change_password = db.Column(db.Boolean, default=True, nullable=False)
    permissions = db.relationship('Permission', backref='user', lazy='dynamic')

    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False)
    access_level = db.Column(db.String(10), nullable=False) # 'read' or 'write'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# --- Decorators & Flask-Login ---
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin: return jsonify(error="Admin privileges required."), 403
        return f(*args, **kwargs)
    return decorated
@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))
@login_manager.unauthorized_handler
def unauthorized(): return jsonify(error="Authentication required."), 401

# --- API Endpoints ---
@app.route('/api/status')
def status():
    auth_status = {'logged_in': False}
    if current_user.is_authenticated:
        auth_status = {'logged_in': True, 'username': current_user.username, 'is_admin': current_user.is_admin}
    return jsonify(auth=auth_status)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    if user and user.check_password(data.get('password')):
        login_user(user, remember=True)
        return jsonify(
            username=user.username,
            is_admin=user.is_admin,
            must_change_password=user.must_change_password
        )
    return jsonify(error="Invalid username or password."), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify(message="Logged out successfully.")

# --- User Management Endpoints ---
@app.route('/api/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'is_admin': u.is_admin} for u in users])

@app.route('/api/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)

    if not username or not password:
        return jsonify(error="Username and password are required."), 400
    if User.query.filter_by(username=username).first():
        return jsonify(error="User already exists."), 409

    new_user = User(username=username, is_admin=is_admin)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message=f"User {username} created successfully."), 201

@app.route('/api/users/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify(error="Current and new passwords are required."), 400

    if not current_user.check_password(current_password):
        return jsonify(error="Invalid current password."), 401

    current_user.set_password(new_password)
    current_user.must_change_password = False
    db.session.commit()
    return jsonify(message="Password changed successfully.")

@app.route('/api/permissions/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_permissions(user_id):
    user = User.query.get_or_404(user_id)
    permissions = Permission.query.filter_by(user_id=user.id).all()
    # Return a dictionary mapping file_path to access_level for easy lookup
    return jsonify({p.file_path: p.access_level for p in permissions})

@app.route('/api/permissions/grant', methods=['POST'])
@login_required
@admin_required
def grant_permission():
    data = request.get_json()
    user_id = data.get('user_id')
    file_path = data.get('file_path')
    access_level = data.get('access_level')

    if not all([user_id, file_path, access_level]):
        return jsonify(error="user_id, file_path, and access_level are required."), 400
    if access_level not in ['read', 'write']:
        return jsonify(error="Invalid access level. Must be 'read' or 'write'."), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify(error="User not found."), 404

    # Remove existing permission for this file to avoid duplicates
    Permission.query.filter_by(user_id=user_id, file_path=file_path).delete()

    new_permission = Permission(user_id=user_id, file_path=file_path, access_level=access_level)
    db.session.add(new_permission)
    db.session.commit()
    return jsonify(message=f"Permission '{access_level}' granted for '{file_path}' to user '{user.username}'."), 201

@app.route('/api/backups', methods=['GET'])
@login_required
@admin_required
def list_backups():
    if not os.path.isdir(BACKUP_DIR): os.makedirs(BACKUP_DIR)
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.enc')], reverse=True)
    return jsonify(backups)

@app.route('/api/backups/create', methods=['POST'])
@login_required
@admin_required
def create_backup():
    data = request.get_json()
    password = data.get('password')
    if not password: return jsonify(error="Admin password is required"), 400
    admin_user = User.query.filter_by(username=current_user.username).first()
    if not admin_user.check_password(password): return jsonify(error="Invalid admin password."), 401

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w:gz') as tar:
        tar.add(CONFIG_DIR, arcname=os.path.basename(CONFIG_DIR))
    tar_stream.seek(0)
    encrypted_data = crypto.encrypt(tar_stream.read(), password)

    if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_filename = f'backup-{timestamp}.tar.gz.enc'
    with open(os.path.join(BACKUP_DIR, backup_filename), 'wb') as f:
        f.write(encrypted_data)
    return jsonify(message="Backup saved to server.", filename=backup_filename), 201

@app.route('/api/backups/restore_from_upload', methods=['POST'])
@login_required
@admin_required
def restore_backup_from_upload():
    password = request.form.get('password')
    if not password: return jsonify(error="Admin password is required"), 400
    admin_user = User.query.filter_by(username=current_user.username).first()
    if not admin_user.check_password(password): return jsonify(error="Invalid admin password."), 401

    if 'file' not in request.files: return jsonify(error="No file part in the request"), 400
    file = request.files['file']
    if file.filename == '': return jsonify(error="No selected file"), 400

    try:
        encrypted_data = file.read()
        decrypted_data = crypto.decrypt(encrypted_data, password)
        tar_stream = io.BytesIO(decrypted_data)
        with tarfile.open(fileobj=tar_stream, mode='r:gz') as tar:
            tar.extractall(path=os.path.dirname(CONFIG_DIR))
        return jsonify(message="Restore from upload successful.")
    except Exception as e:
        return jsonify(error=f"Restore failed: {repr(e)}"), 500

@app.route('/api/backups/restore_from_server', methods=['POST'])
@login_required
@admin_required
def restore_backup_from_server():
    data = request.get_json()
    password = data.get('password')
    filename = data.get('filename')
    if not password or not filename: return jsonify(error="Filename and admin password are required"), 400

    admin_user = User.query.filter_by(username=current_user.username).first()
    if not admin_user.check_password(password): return jsonify(error="Invalid admin password."), 401

    backup_path = os.path.normpath(os.path.join(BACKUP_DIR, filename))
    if not os.path.isfile(backup_path): return jsonify(error="Backup file not found on server."), 404

    try:
        with open(backup_path, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = crypto.decrypt(encrypted_data, password)
        tar_stream = io.BytesIO(decrypted_data)
        with tarfile.open(fileobj=tar_stream, mode='r:gz') as tar:
            tar.extractall(path=os.path.dirname(CONFIG_DIR))
        return jsonify(message="Restore from server successful.")
    except Exception as e:
        return jsonify(error=f"Restore failed: {repr(e)}"), 500

@app.route('/api/files')
@login_required
def get_files():
    if not os.path.isdir(CONFIG_DIR): return jsonify(error=f"Config dir not found"), 500

    all_files = []
    for root, dirs, files in os.walk(CONFIG_DIR):
        relative_root = os.path.relpath(root, CONFIG_DIR)
        if relative_root == '.': relative_root = ''
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                all_files.append({'name': file, 'path': os.path.join(relative_root, file)})

    if current_user.is_admin:
        for file in all_files:
            file['access_level'] = 'write'
    else:
        user_perms = {p.file_path: p.access_level for p in current_user.permissions}
        for file in all_files:
            file['access_level'] = user_perms.get(file['path'], 'none')

    return jsonify(sorted(all_files, key=lambda x: x['path']))


@app.route('/api/files/content', methods=['GET', 'POST'])
@login_required
def file_content():
    file_path_rel = request.args.get('path')

    # Authorization Check
    has_read_permission = False
    has_write_permission = False
    if current_user.is_admin:
        has_read_permission = True
        has_write_permission = True
    else:
        permissions = Permission.query.filter_by(user_id=current_user.id, file_path=file_path_rel).all()
        for p in permissions:
            if p.access_level == 'read': has_read_permission = True
            if p.access_level == 'write': has_write_permission = True; has_read_permission = True

    if request.method == 'GET':
        if not has_read_permission: return jsonify(error="Read access denied."), 403
    if request.method == 'POST':
        if not has_write_permission: return jsonify(error="Write access denied."), 403

    # Path safety and file access
    safe_path_str = os.path.join(*[secure_filename(part) for part in file_path_rel.split(os.sep)])
    full_path = os.path.normpath(os.path.join(CONFIG_DIR, safe_path_str))
    if os.path.commonprefix([full_path, os.path.abspath(CONFIG_DIR)]) != os.path.abspath(CONFIG_DIR):
        return jsonify({"error": "Directory traversal attempt detected."}), 400
    if not os.path.isfile(full_path): return jsonify({"error": "File not found."}), 404

    try:
        parser = get_parser(full_path)
        if request.method == 'GET':
                content = parser.read(full_path)
                return jsonify(content)
        else: # POST
            data = request.get_json()
            parser.write(full_path, data)
            return jsonify({"message": "File saved successfully."})
    except ValueError as e:
        # This catches parsing errors from the read() methods
        return jsonify(status="parse_error", error=str(e)), 400

# --- CLI Commands for Setup ---
@app.cli.command("seed")
def seed_db():
    """Seeds the database with an initial admin user."""
    if User.query.filter_by(username='admin').first():
        click.echo('Admin user already exists.')
    else:
        admin = User(
            username='admin',
            is_admin=True,
            must_change_password=True
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        click.echo('Admin user created successfully (password: admin).')
