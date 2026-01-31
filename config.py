"""
Chitty Dashboard Configuration

All settings are loaded from environment variables (via .env file).
Copy .env.example to .env and customize for your setup.
"""
import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# =============================================================================
# Flask Settings
# =============================================================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.environ.get('FLASK_PORT', 5001))
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')

# Legacy alias (used in some imports)
PORT = FLASK_PORT

# =============================================================================
# Default Admin Account
# =============================================================================
# Created automatically on first run if no users exist
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'chitty@2026')

# =============================================================================
# Clawd Workspace Paths
# =============================================================================
WORKSPACE_DIR = os.environ.get('WORKSPACE_DIR', '/home/labs/clawd')

# Derived paths
CLAWD_DIR = WORKSPACE_DIR  # Alias for backward compatibility
MEMORY_DIR = os.path.join(WORKSPACE_DIR, 'memory')
MEMORY_FILE = os.path.join(WORKSPACE_DIR, 'MEMORY.md')
HEARTBEAT_STATE = os.path.join(MEMORY_DIR, 'heartbeat-state.json')

# =============================================================================
# Dashboard Data Directory
# =============================================================================
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
STATUS_FILE = os.path.join(DATA_DIR, 'status.json')
TASKS_FILE = os.path.join(DATA_DIR, 'tasks.json')
NOTES_FILE = os.path.join(DATA_DIR, 'notes.json')
ACTIVITY_LOG = os.path.join(DATA_DIR, 'activity.log')

# =============================================================================
# Email Monitoring (optional)
# =============================================================================
EMAIL_ACCOUNT = os.environ.get('EMAIL_ACCOUNT', '')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')

# Watched senders — configure in code or extend to parse from env
# Format: {'email': 'someone@example.com', 'context': 'Description'}
WATCHED_SENDERS_RAW = os.environ.get('WATCHED_SENDERS', '')
WATCHED_SENDERS = []
if WATCHED_SENDERS_RAW:
    # Parse "email:context,email:context" format
    for entry in WATCHED_SENDERS_RAW.split(','):
        entry = entry.strip()
        if ':' in entry:
            email, context = entry.split(':', 1)
            WATCHED_SENDERS.append({'email': email.strip(), 'context': context.strip()})

# =============================================================================
# TODO File Paths (shown on dashboard)
# =============================================================================
TODO_PATHS = [
    os.path.join(WORKSPACE_DIR, 'TODO.md'),
]

# =============================================================================
# Sessions Directory (sub-agent tracking)
# =============================================================================
SESSIONS_DIR = os.environ.get(
    'SESSIONS_DIR',
    os.path.expanduser('~/.clawdbot/agents/main/sessions')
)

# =============================================================================
# Document Browser Directories
# =============================================================================
DOCS_SCAN_DIRS = [
    {'path': MEMORY_DIR, 'label': 'Memory Files'},
    {'path': WORKSPACE_DIR, 'label': 'Workspace Root', 'depth': 1},
    {'path': DATA_DIR, 'label': 'Dashboard Data'},
]
