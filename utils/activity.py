import os
import re
import glob
import json
from datetime import datetime, date
from config import MEMORY_DIR, ACTIVITY_LOG


CATEGORY_MAP = {
    'email': {'icon': 'email', 'emoji': '📧', 'label': 'Email'},
    'message': {'icon': 'chat', 'emoji': '💬', 'label': 'Message'},
    'system': {'icon': 'settings', 'emoji': '🔧', 'label': 'System'},
    'memory': {'icon': 'psychology', 'emoji': '📝', 'label': 'Memory'},
    'task': {'icon': 'check_circle', 'emoji': '✅', 'label': 'Task'},
    'ai': {'icon': 'smart_toy', 'emoji': '🤖', 'label': 'AI Action'},
    'other': {'icon': 'fiber_manual_record', 'emoji': '⚪', 'label': 'Other'},
}


def _categorize(text):
    """Categorize activity text."""
    t = text.lower()
    if any(w in t for w in ['email', 'mail', 'inbox', 'smtp', 'imap']):
        return 'email'
    if any(w in t for w in ['message', 'telegram', 'discord', 'chat', 'sent', 'replied']):
        return 'message'
    if any(w in t for w in ['deploy', 'server', 'docker', 'system', 'restart', 'service', 'port']):
        return 'system'
    if any(w in t for w in ['memory', 'remember', 'note', 'heartbeat', 'journal']):
        return 'memory'
    if any(w in t for w in ['task', 'todo', 'done', 'complete', 'kanban', 'assign']):
        return 'task'
    if any(w in t for w in ['ai', 'agent', 'clawdbot', 'chitty', 'model', 'claude', 'sub-agent']):
        return 'ai'
    return 'other'


def parse_memory_file(filepath):
    """Parse a memory markdown file into structured activity entries."""
    entries = []
    if not os.path.exists(filepath):
        return entries

    with open(filepath, 'r') as f:
        content = f.read()

    filename = os.path.basename(filepath)
    file_date = filename.replace('.md', '')

    current_section = ''
    current_time = ''

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue

        header_match = re.match(r'^#{1,3}\s+(.+)', line)
        if header_match:
            current_section = header_match.group(1)
            time_match = re.search(r'(\d{1,2}:\d{2})', current_section)
            if time_match:
                current_time = time_match.group(1)
            continue

        if line.startswith('- ') or line.startswith('* '):
            text = line[2:].strip()
            time_match = re.match(r'\*?\*?(\d{1,2}:\d{2})\*?\*?\s*[-:]\s*(.*)', text)
            if time_match:
                current_time = time_match.group(1)
                text = time_match.group(2)

            if text:
                cat = _categorize(text)
                entry = {
                    'date': file_date,
                    'time': current_time or '',
                    'section': current_section,
                    'text': text,
                    'icon': CATEGORY_MAP[cat]['icon'],
                    'emoji': CATEGORY_MAP[cat]['emoji'],
                    'category': cat,
                    'category_label': CATEGORY_MAP[cat]['label'],
                    'source': 'memory',
                }
                entries.append(entry)

    return entries


def _load_dashboard_activity():
    """Load entries from the dashboard activity log (JSONL)."""
    entries = []
    if not os.path.exists(ACTIVITY_LOG):
        return entries

    try:
        with open(ACTIVITY_LOG, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    ts = data.get('timestamp', '')
                    dt = datetime.fromisoformat(ts) if ts else datetime.now()
                    cat = _categorize(data.get('action', ''))
                    entries.append({
                        'date': dt.strftime('%Y-%m-%d'),
                        'time': dt.strftime('%H:%M'),
                        'section': 'Dashboard',
                        'text': data.get('action', ''),
                        'icon': CATEGORY_MAP[cat]['icon'],
                        'emoji': CATEGORY_MAP[cat]['emoji'],
                        'category': cat,
                        'category_label': CATEGORY_MAP[cat]['label'],
                        'source': 'dashboard',
                    })
                except Exception:
                    continue
    except Exception:
        pass
    return entries


def get_activities(target_date=None, limit=None, category=None):
    """Get activities, optionally filtered by date and category."""
    if target_date:
        filepath = os.path.join(MEMORY_DIR, f'{target_date}.md')
        entries = parse_memory_file(filepath)
    else:
        entries = []
        pattern = os.path.join(MEMORY_DIR, '*.md')
        for filepath in sorted(glob.glob(pattern), reverse=True):
            filename = os.path.basename(filepath)
            if not re.match(r'\d{4}-\d{2}-\d{2}\.md', filename):
                continue
            entries.extend(parse_memory_file(filepath))

    # Add dashboard activity log entries
    dash_entries = _load_dashboard_activity()
    if target_date:
        dash_entries = [e for e in dash_entries if e['date'] == target_date]
    entries.extend(dash_entries)

    # Sort by date+time descending (newest first)
    entries.sort(key=lambda e: (e['date'], e['time']), reverse=True)

    if category:
        entries = [e for e in entries if e.get('category') == category]

    if limit:
        entries = entries[:limit]
    return entries


def get_today_activities(limit=10):
    """Get today's activities."""
    today = date.today().strftime('%Y-%m-%d')
    return get_activities(target_date=today, limit=limit)


def get_available_dates():
    """Get list of dates that have memory files."""
    dates = []
    pattern = os.path.join(MEMORY_DIR, '*.md')
    for filepath in sorted(glob.glob(pattern), reverse=True):
        filename = os.path.basename(filepath)
        match = re.match(r'(\d{4}-\d{2}-\d{2})\.md', filename)
        if match:
            dates.append(match.group(1))
    return dates


def get_categories():
    """Return available categories for filtering."""
    return CATEGORY_MAP
