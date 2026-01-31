import subprocess
import json
import os
from datetime import datetime
from config import EMAIL_ACCOUNT, EMAIL_PASSWORD, WATCHED_SENDERS, CLAWD_DIR


def check_emails():
    """Run the email monitor check and return results."""
    try:
        result = subprocess.run(
            ['python3', 'email_monitor.py', EMAIL_ACCOUNT, EMAIL_PASSWORD, 'check'],
            capture_output=True, text=True, timeout=30,
            cwd=CLAWD_DIR
        )
        return {
            'status': 'success' if result.returncode == 0 else 'error',
            'output': result.stdout.strip() if result.stdout else '',
            'error': result.stderr.strip() if result.stderr else '',
            'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except subprocess.TimeoutExpired:
        return {
            'status': 'timeout',
            'output': 'Email check timed out after 30 seconds',
            'error': '',
            'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'status': 'error',
            'output': '',
            'error': str(e),
            'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


def _mask_email(email):
    """Mask email for display: ven***@selfmade.ninja"""
    if '@' in email:
        local, domain = email.split('@', 1)
        masked = local[:3] + '***' if len(local) > 3 else local[0] + '***'
        return f"{masked}@{domain}"
    return email


def get_email_status():
    """Get email monitoring status without running a check."""
    return {
        'account': EMAIL_ACCOUNT,
        'account_masked': _mask_email(EMAIL_ACCOUNT),
        'watched_senders': WATCHED_SENDERS,
        'status': 'Active' if EMAIL_ACCOUNT else 'Not configured',
        'monitor_script': os.path.exists(os.path.join(CLAWD_DIR, 'email_monitor.py')),
        'checker_script': os.path.exists(os.path.join(CLAWD_DIR, 'email_checker.py'))
    }
