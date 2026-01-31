import os
import glob
import markdown2
from datetime import datetime
from config import CLAWD_DIR, MEMORY_DIR, DATA_DIR


# Directories to scan for docs
SCAN_CONFIGS = [
    {'path': MEMORY_DIR, 'label': 'Memory', 'pattern': '*.md', 'recursive': False},
    {'path': CLAWD_DIR, 'label': 'Workspace', 'pattern': '*.md', 'recursive': False},
    {'path': DATA_DIR, 'label': 'Dashboard Data', 'pattern': '*', 'recursive': False},
]


def get_all_docs():
    """Scan all configured directories for documents."""
    docs = []
    seen = set()

    for cfg in SCAN_CONFIGS:
        dirpath = cfg['path']
        if not os.path.isdir(dirpath):
            continue

        pattern = os.path.join(dirpath, cfg['pattern'])
        for filepath in glob.glob(pattern):
            if not os.path.isfile(filepath):
                continue
            if filepath in seen:
                continue
            seen.add(filepath)

            stat = os.stat(filepath)
            name = os.path.basename(filepath)
            ext = os.path.splitext(name)[1].lower()

            docs.append({
                'name': name,
                'path': filepath,
                'relative_path': os.path.relpath(filepath, CLAWD_DIR),
                'type': ext if ext else 'file',
                'size': _fmt_size(stat.st_size),
                'size_bytes': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'modified_ts': stat.st_mtime,
                'label': cfg['label'],
            })

    docs.sort(key=lambda d: d['modified_ts'], reverse=True)
    return docs


def get_doc_content(filepath):
    """Read and optionally render a document."""
    # Security: ensure path is within allowed directories
    real = os.path.realpath(filepath)
    allowed = [os.path.realpath(CLAWD_DIR)]
    if not any(real.startswith(a) for a in allowed):
        return None

    if not os.path.isfile(real):
        return None

    try:
        with open(real, 'r', errors='replace') as f:
            content = f.read(500000)  # 500KB max
    except Exception:
        return None

    ext = os.path.splitext(real)[1].lower()
    html = None
    if ext == '.md':
        html = markdown2.markdown(content, extras=['fenced-code-blocks', 'tables', 'task_list'])

    return {
        'name': os.path.basename(real),
        'path': real,
        'content': content,
        'html': html,
        'type': ext,
    }


def _fmt_size(b):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
