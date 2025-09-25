from functools import wraps
from flask import session, redirect, url_for, current_app

def setup_required(f):
    """
    Перенаправляет на страницу настройки, если начальная настройка не завершена.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Используем current_app для доступа к конфигурации приложения
        if not current_app.config['security']['initial_setup_complete']:
            return redirect(url_for('setup'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """
    Перенаправляет на страницу входа, если пользователь не вошел в систему.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function