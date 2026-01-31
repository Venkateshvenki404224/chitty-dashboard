import os
import re
import json
import uuid
from datetime import datetime
from config import TODO_PATHS, TASKS_FILE, ACTIVITY_LOG


# Marker map for TODO.md checkbox states
COLUMN_MARKERS = {
    'todo': '[ ]',
    'in_progress': '[~]',
    'done': '[x]',
}


def _clean_task_text(text):
    """Remove markdown bold formatting from task text."""
    return re.sub(r'\*\*(.+?)\*\*', r'\1', text).strip()


def parse_todo_file(filepath):
    """Parse a TODO.md file into task items."""
    tasks = {'todo': [], 'in_progress': [], 'done': []}

    if not os.path.exists(filepath):
        return tasks

    with open(filepath, 'r') as f:
        content = f.read()

    current_section = ''
    source = os.path.basename(os.path.dirname(filepath)) or os.path.basename(filepath)

    for line_num, line in enumerate(content.split('\n'), 1):
        stripped = line.strip()

        header_match = re.match(r'^#{1,3}\s+(.+)', stripped)
        if header_match:
            current_section = header_match.group(1)
            continue

        todo_match = re.match(r'^-\s+\[\s*\]\s+(.*)', stripped)
        done_match = re.match(r'^-\s+\[x\]\s+(.*)', stripped, re.IGNORECASE)
        progress_match = re.match(r'^-\s+\[~\]\s+(.*)', stripped)

        task_base = {
            'section': current_section,
            'source': source,
            'source_type': 'file',
            'source_file': filepath,
            'priority': 'normal',
            'timestamp': None,
        }

        if done_match:
            raw_text = done_match.group(1)
            tasks['done'].append({
                **task_base,
                'text': _clean_task_text(raw_text),
                'raw_text': raw_text,
                'line_num': line_num,
            })
        elif progress_match:
            raw_text = progress_match.group(1)
            tasks['in_progress'].append({
                **task_base,
                'text': _clean_task_text(raw_text),
                'raw_text': raw_text,
                'line_num': line_num,
            })
        elif todo_match:
            raw_text = todo_match.group(1)
            tasks['todo'].append({
                **task_base,
                'text': _clean_task_text(raw_text),
                'raw_text': raw_text,
                'line_num': line_num,
            })

    return tasks


def _load_dashboard_tasks():
    """Load tasks from dashboard tasks.json."""
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return []


def _save_dashboard_tasks(tasks):
    """Save tasks to dashboard tasks.json."""
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)


def _log_activity(action):
    """Log a dashboard action."""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'source': 'dashboard'
    }
    with open(ACTIVITY_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def get_all_tasks():
    """Get tasks from all TODO files + dashboard tasks."""
    all_tasks = {'todo': [], 'in_progress': [], 'done': []}

    # Parse TODO.md files
    for path in TODO_PATHS:
        if os.path.exists(path):
            tasks = parse_todo_file(path)
            all_tasks['todo'].extend(tasks['todo'])
            all_tasks['in_progress'].extend(tasks['in_progress'])
            all_tasks['done'].extend(tasks['done'])

    extra_paths = [
        '/home/labs/clawd/job-scraper/TODO.md',
    ]
    for path in extra_paths:
        if os.path.exists(path) and path not in TODO_PATHS:
            tasks = parse_todo_file(path)
            all_tasks['todo'].extend(tasks['todo'])
            all_tasks['in_progress'].extend(tasks['in_progress'])
            all_tasks['done'].extend(tasks['done'])

    # Add dashboard-managed tasks
    dash_tasks = _load_dashboard_tasks()
    for t in dash_tasks:
        col = t.get('column', 'todo')
        if col in all_tasks:
            all_tasks[col].append({
                'id': t.get('id'),
                'text': t.get('text', ''),
                'section': t.get('section', ''),
                'source': 'Dashboard',
                'source_type': 'dashboard',
                'priority': t.get('priority', 'normal'),
                'timestamp': t.get('timestamp'),
            })

    return all_tasks


def add_task(text, priority='normal', column='todo'):
    """Add a new dashboard task."""
    tasks = _load_dashboard_tasks()
    task = {
        'id': str(uuid.uuid4())[:8],
        'text': text,
        'priority': priority,
        'column': column,
        'section': '',
        'timestamp': datetime.now().isoformat(),
    }
    tasks.append(task)
    _save_dashboard_tasks(tasks)
    _log_activity(f'Task added: {text[:60]}')
    return task


def move_task(task_id, new_column):
    """Move a dashboard task between columns."""
    tasks = _load_dashboard_tasks()
    for t in tasks:
        if t['id'] == task_id:
            old = t.get('column', 'todo')
            t['column'] = new_column
            t['moved_at'] = datetime.now().isoformat()
            _save_dashboard_tasks(tasks)
            _log_activity(f'Task {task_id} moved from {old} to {new_column}')
            return t
    return None


def move_file_task(source_file, line_num, new_column):
    """Move a file-based task by updating its checkbox marker in the source file.
    
    Args:
        source_file: Path to the TODO.md file
        line_num: 1-indexed line number of the task
        new_column: Target column (todo, in_progress, done)
    
    Returns:
        dict with result or None on failure
    """
    if new_column not in COLUMN_MARKERS:
        return None

    if not os.path.exists(source_file):
        return None

    new_marker = COLUMN_MARKERS[new_column]

    with open(source_file, 'r') as f:
        lines = f.readlines()

    if line_num < 1 or line_num > len(lines):
        return None

    line = lines[line_num - 1]

    # Match any checkbox pattern: [ ], [~], [x], [X]
    match = re.match(r'^(\s*-\s+)\[[ ~xX]\](\s+.*)', line)
    if not match:
        return None

    prefix = match.group(1)
    rest = match.group(2)
    old_line = line.rstrip('\n')
    new_line = f"{prefix}{new_marker}{rest}"
    lines[line_num - 1] = new_line if not line.endswith('\n') else new_line + '\n'

    with open(source_file, 'w') as f:
        f.writelines(lines)

    _log_activity(f'File task moved to {new_column}: {source_file}:{line_num}')

    return {
        'source_file': source_file,
        'line_num': line_num,
        'old_line': old_line.strip(),
        'new_line': new_line.strip(),
        'column': new_column,
    }


def get_task_stats():
    """Get task count statistics."""
    tasks = get_all_tasks()
    return {
        'todo': len(tasks['todo']),
        'in_progress': len(tasks['in_progress']),
        'done': len(tasks['done']),
        'total': len(tasks['todo']) + len(tasks['in_progress']) + len(tasks['done'])
    }
