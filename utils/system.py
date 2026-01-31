import psutil
import platform
import subprocess
import datetime


def get_system_info():
    """Get comprehensive system information."""
    # Clawdbot gateway uptime (not system boot time)
    try:
        result = subprocess.run(['pgrep', '-f', 'clawdbot-gateway'], capture_output=True, text=True)
        if result.stdout.strip():
            pid = result.stdout.strip().split('\n')[0]
            proc = psutil.Process(int(pid))
            create_time = datetime.datetime.fromtimestamp(proc.create_time())
            uptime = datetime.datetime.now() - create_time
        else:
            raise Exception("No clawdbot-gateway process")
    except Exception:
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time

    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m"

    return {
        'hostname': platform.node(),
        'os': f"{platform.system()} {platform.release()}",
        'arch': platform.machine(),
        'python': platform.python_version(),
        'uptime': uptime_str,
        'boot_time': datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
        'cpu': {
            'percent': cpu_percent,
            'cores': psutil.cpu_count(),
            'freq': round(psutil.cpu_freq().current, 0) if psutil.cpu_freq() else 'N/A'
        },
        'memory': {
            'total': _fmt_bytes(memory.total),
            'used': _fmt_bytes(memory.used),
            'available': _fmt_bytes(memory.available),
            'percent': memory.percent
        },
        'disk': {
            'total': _fmt_bytes(disk.total),
            'used': _fmt_bytes(disk.used),
            'free': _fmt_bytes(disk.free),
            'percent': disk.percent
        }
    }


def get_services():
    """Get running services status."""
    services = []

    # Check clawdbot
    try:
        result = subprocess.run(['pgrep', '-f', 'clawdbot'], capture_output=True, timeout=5)
        services.append({
            'name': 'Clawdbot',
            'status': 'running' if result.returncode == 0 else 'stopped',
            'icon': 'smart_toy'
        })
    except Exception:
        services.append({'name': 'Clawdbot', 'status': 'unknown', 'icon': 'smart_toy'})

    # Check Docker containers
    try:
        result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    services.append({
                        'name': f'Docker: {parts[0]}',
                        'status': 'running' if 'Up' in parts[1] else 'stopped',
                        'icon': 'cloud'
                    })
    except Exception:
        pass

    # Check Flask job-scraper on port 5000
    try:
        result = subprocess.run(['lsof', '-i', ':5000', '-t'], capture_output=True, text=True, timeout=5)
        services.append({
            'name': 'Job Scraper (5000)',
            'status': 'running' if result.stdout.strip() else 'stopped',
            'icon': 'work'
        })
    except Exception:
        services.append({'name': 'Job Scraper (5000)', 'status': 'unknown', 'icon': 'work'})

    return services


def _fmt_bytes(b):
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"
