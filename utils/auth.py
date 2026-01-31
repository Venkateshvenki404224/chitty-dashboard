"""Authentication utilities for Chitty Dashboard."""

import json
import os
import uuid
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, redirect, url_for, request
from config import ADMIN_USERNAME, ADMIN_PASSWORD

USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'users.json')

DEFAULT_ADMIN = {
    'username': ADMIN_USERNAME,
    'password': ADMIN_PASSWORD,
    'role': 'admin'
}


def _load_users():
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return []


def _save_users(users):
    """Save users to JSON file."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def init_users():
    """Initialize users file with default admin if it doesn't exist or is empty."""
    users = _load_users()
    if not users:
        admin = {
            'id': str(uuid.uuid4()),
            'username': DEFAULT_ADMIN['username'],
            'password_hash': generate_password_hash(DEFAULT_ADMIN['password']),
            'role': DEFAULT_ADMIN['role'],
            'created_at': datetime.now().isoformat(),
            'created_by': 'system'
        }
        _save_users([admin])
        print("✅ Default admin account created (admin / chitty@2026)")


def authenticate(username, password):
    """Authenticate a user. Returns user dict (without password_hash) or None."""
    users = _load_users()
    for user in users:
        if user['username'] == username and check_password_hash(user['password_hash'], password):
            return {k: v for k, v in user.items() if k != 'password_hash'}
    return None


def get_all_users():
    """Get all users (without password hashes)."""
    users = _load_users()
    return [{k: v for k, v in u.items() if k != 'password_hash'} for u in users]


def create_user(username, password, role, created_by):
    """Create a new user. Returns (user, error)."""
    users = _load_users()
    if any(u['username'] == username for u in users):
        return None, 'Username already exists'
    
    new_user = {
        'id': str(uuid.uuid4()),
        'username': username,
        'password_hash': generate_password_hash(password),
        'role': role,
        'created_at': datetime.now().isoformat(),
        'created_by': created_by
    }
    users.append(new_user)
    _save_users(users)
    return {k: v for k, v in new_user.items() if k != 'password_hash'}, None


def delete_user(user_id):
    """Delete a user by ID. Returns (success, error)."""
    users = _load_users()
    new_users = [u for u in users if u['id'] != user_id]
    if len(new_users) == len(users):
        return False, 'User not found'
    _save_users(new_users)
    return True, None


def get_current_user():
    """Get the current logged-in user from session."""
    return session.get('user', None)


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        if session['user'].get('role') != 'admin':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function
