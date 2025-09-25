#!/bin/bash

# Скрипт для установки Config Editor как системного сервиса
# ЗАПУСКАТЬ С ПРАВАМИ ROOT (sudo ./install.sh)

# --- Переменные ---
APP_USER="config-editor"
APP_GROUP="config-editor"
APP_DIR="/opt/config-editor"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/config-editor"
SERVICE_NAME="config-editor"

# --- Функции ---
print_info() {
    echo -e "\e[34m[INFO]\e[0m $1"
}

print_success() {
    echo -e "\e[32m[SUCCESS]\e[0m $1"
}

print_error() {
    echo -e "\e[31m[ERROR]\e[0m $1"
    exit 1
}

# 1. Проверка прав root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (using sudo)."
fi

# 2. Установка системных зависимостей
print_info "Updating package list and installing dependencies..."
apt-get update >/dev/null || print_error "Failed to update package lists."
apt-get install -y python3 python3-venv python3-pip libpam-dev >/dev/null || print_error "Failed to install system dependencies."
print_success "System dependencies installed."

# 3. Создание пользователя и группы для приложения
if id "$APP_USER" &>/dev/null; then
    print_info "User '$APP_USER' already exists."
else
    print_info "Creating user '$APP_USER'..."
    useradd -r -s /bin/false -m -d $APP_DIR $APP_USER || print_error "Failed to create user '$APP_USER'."
fi
print_success "Application user '$APP_USER' is ready."

# 4. Копирование файлов приложения и настройка прав
print_info "Copying application files to $APP_DIR..."
# Копируем из директории, где лежит скрипт
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
mkdir -p $APP_DIR
cp -r "$SCRIPT_DIR/.."/* $APP_DIR/ || print_error "Failed to copy application files."

# Создание директории для логов
mkdir -p $LOG_DIR
chown $APP_USER:$APP_GROUP $LOG_DIR

# Установка прав
chown -R $APP_USER:$APP_GROUP $APP_DIR
chmod -R 750 $APP_DIR
print_success "Application files copied and permissions set."

# 5. Создание виртуального окружения и установка зависимостей
print_info "Creating Python virtual environment..."
python3 -m venv $VENV_DIR || print_error "Failed to create virtual environment."

print_info "Installing Python dependencies..."
# Запускаем от имени пользователя приложения для безопасности
sudo -u $APP_USER bash -c "source $VENV_DIR/bin/activate && pip install -r $APP_DIR/requirements.txt" >/dev/null || print_error "Failed to install Python dependencies."
print_success "Python environment is ready."

# 6. Настройка Sudo
SUDOERS_FILE="/etc/sudoers.d/99-config-editor"
HELPER_SCRIPT_PATH="$APP_DIR/scripts/file_operations.py"
SUDO_RULE="$APP_USER ALL=(ALL) NOPASSWD: /usr/bin/python3 $HELPER_SCRIPT_PATH"

print_info "Configuring sudo rules..."
echo "$SUDO_RULE" > $SUDOERS_FILE || print_error "Failed to write sudoers file."
chmod 440 $SUDOERS_FILE || print_error "Failed to set permissions on sudoers file."
print_success "Sudo rule created at $SUDOERS_FILE."

# 7. Создание systemd сервиса
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

print_info "Creating systemd service file at $SERVICE_FILE..."

cat > $SERVICE_FILE << EOF
[Unit]
Description=Config Editor Web Application
After=network.target

[Service]
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$APP_DIR/gunicorn.sock -m 007 'app.main:app' --access-logfile $LOG_DIR/access.log --error-logfile $LOG_DIR/error.log
Restart=always

[Install]
WantedBy=multi-user.target
EOF

print_success "Service file created."

# 8. Запуск сервиса
print_info "Enabling and starting the service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME.service >/dev/null
systemctl start $SERVICE_NAME.service
systemctl status $SERVICE_NAME.service --no-pager

print_success "Installation complete!"
echo "The application should be running. You may need to configure a reverse proxy (like Nginx) to access it via a domain name."
echo "Initial setup is required. Open the application in your browser and set the admin password."
echo "Logs are available in $LOG_DIR"