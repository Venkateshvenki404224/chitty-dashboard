import os
import json
import subprocess
import glob
from datetime import datetime
from config import STATUS_FILE, HEARTBEAT_STATE, SESSIONS_DIR


def get_ai_status():
    """Determine AI status from multiple signals."""
    status = {
        'ai_status': 'offline',
        'status_emoji': '🔴',
        'status_class': 'danger',
        'current_task': 'Unknown',
        'last_heartbeat': None,
        'heartbeat_ago': None,
        'uptime': None,
        'active_sessions': [],
    }

    # Check if clawdbot gateway is running
    gateway_running = False
    try:
        result = subprocess.run(['pgrep', '-f', 'clawdbot'], capture_output=True, timeout=5)
        gateway_running = result.returncode == 0
    except Exception:
        pass

    # Read status.json for current task
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                sdata = json.load(f)
            status['current_task'] = sdata.get('current_task', 'Monitoring systems')
        except Exception:
            pass

    # Get uptime from clawdbot-gateway process
    try:
        import psutil
        result = subprocess.run(['pgrep', '-f', 'clawdbot-gateway'], capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            pid = int(result.stdout.strip().split('\n')[0])
            proc = psutil.Process(pid)
            create_time = datetime.fromtimestamp(proc.create_time())
            delta = datetime.now() - create_time
            days = delta.days
            hours, rem = divmod(delta.seconds, 3600)
            mins, _ = divmod(rem, 60)
            status['uptime'] = f"{days}d {hours}h {mins}m"
    except Exception:
        try:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r') as f:
                    sdata = json.load(f)
                if sdata.get('started_at'):
                    started = datetime.fromisoformat(sdata['started_at'])
                    delta = datetime.now() - started
                    days = delta.days
                    hours, rem = divmod(delta.seconds, 3600)
                    mins, _ = divmod(rem, 60)
                    status['uptime'] = f"{days}d {hours}h {mins}m"
        except Exception:
            pass

    # Read heartbeat state
    if os.path.exists(HEARTBEAT_STATE):
        try:
            with open(HEARTBEAT_STATE, 'r') as f:
                hb = json.load(f)
            last_checks = hb.get('lastChecks', {})
            # Find the most recent check timestamp
            timestamps = [v for v in last_checks.values() if isinstance(v, (int, float)) and v > 0]
            if timestamps:
                latest = max(timestamps)
                last_dt = datetime.fromtimestamp(latest)
                status['last_heartbeat'] = last_dt.strftime('%Y-%m-%d %H:%M:%S')
                delta = datetime.now() - last_dt
                total_mins = int(delta.total_seconds() / 60)
                if total_mins < 60:
                    status['heartbeat_ago'] = f"{total_mins}m ago"
                elif total_mins < 1440:
                    status['heartbeat_ago'] = f"{total_mins // 60}h {total_mins % 60}m ago"
                else:
                    status['heartbeat_ago'] = f"{total_mins // 1440}d ago"
        except Exception:
            pass

    # Check active sub-agent sessions
    if os.path.isdir(SESSIONS_DIR):
        try:
            session_files = glob.glob(os.path.join(SESSIONS_DIR, '*.json'))
            recent = []
            for sf in sorted(session_files, key=os.path.getmtime, reverse=True)[:10]:
                try:
                    stat = os.stat(sf)
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    delta = datetime.now() - mtime
                    name = os.path.basename(sf).replace('.json', '')
                    recent.append({
                        'name': name,
                        'modified': mtime.strftime('%H:%M:%S'),
                        'age_minutes': int(delta.total_seconds() / 60),
                        'active': delta.total_seconds() < 600,  # active if modified <10 min ago
                    })
                except Exception:
                    continue
            status['active_sessions'] = recent
        except Exception:
            pass

    # Determine overall status with cute emojis
    if gateway_running:
        active_count = sum(1 for s in status['active_sessions'] if s.get('active'))
        task = status.get('current_task', '').lower()

        if active_count > 0:
            status['ai_status'] = 'working'
            status['status_class'] = 'success'
            # Pick emoji based on what we're doing
            if any(w in task for w in ['build', 'creat', 'develop', 'code', 'implement', 'upgrad']):
                status['status_emoji'] = '🔨'  # Building something
            elif any(w in task for w in ['search', 'research', 'look', 'find', 'check']):
                status['status_emoji'] = '🔍'  # Searching/researching
            elif any(w in task for w in ['think', 'plan', 'analyz', 'figur']):
                status['status_emoji'] = '🤔'  # Thinking
            elif any(w in task for w in ['email', 'monitor', 'watch']):
                status['status_emoji'] = '👀'  # Monitoring
            elif any(w in task for w in ['fix', 'debug', 'repair', 'patch']):
                status['status_emoji'] = '🔧'  # Fixing
            elif any(w in task for w in ['deploy', 'launch', 'ship', 'push']):
                status['status_emoji'] = '🚀'  # Deploying
            elif any(w in task for w in ['write', 'draft', 'document']):
                status['status_emoji'] = '✍️'  # Writing
            elif any(w in task for w in ['test', 'verif']):
                status['status_emoji'] = '🧪'  # Testing
            else:
                status['status_emoji'] = '⚡'  # Generic working
        else:
            status['ai_status'] = 'idle'
            status['status_class'] = 'warning'
            # Idle — pick based on time of day
            hour = datetime.now().hour
            if hour < 6 or hour >= 23:
                status['status_emoji'] = '😴'  # Sleeping late night
            elif hour < 9:
                status['status_emoji'] = '🥱'  # Waking up
            elif hour >= 18:
                status['status_emoji'] = '😌'  # Evening chill
            else:
                status['status_emoji'] = '💤'  # Napping/idle
    else:
        status['ai_status'] = 'offline'
        status['status_emoji'] = '💀'  # Dead/offline
        status['status_class'] = 'danger'

    return status


def update_status(current_task=None, ai_status=None):
    """Update the status file."""
    data = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
        except Exception:
            pass

    if current_task is not None:
        data['current_task'] = current_task
    if ai_status is not None:
        data['ai_status'] = ai_status
    data['last_updated'] = datetime.now().isoformat()

    if 'started_at' not in data:
        data['started_at'] = datetime.now().isoformat()

    with open(STATUS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return data
