import os
import glob
import markdown2
from config import MEMORY_DIR, MEMORY_FILE


def get_memory_files():
    """List all memory files sorted by date descending."""
    files = []
    pattern = os.path.join(MEMORY_DIR, '*.md')
    for filepath in sorted(glob.glob(pattern), reverse=True):
        filename = os.path.basename(filepath)
        if filename == 'heartbeat-state.json':
            continue
        stat = os.stat(filepath)
        files.append({
            'filename': filename,
            'date': filename.replace('.md', ''),
            'size': f"{stat.st_size / 1024:.1f} KB",
            'path': filepath
        })
    return files


def get_memory_content(filename):
    """Read and render a memory file as HTML."""
    filepath = os.path.join(MEMORY_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        content = f.read()
    html = markdown2.markdown(content, extras=['fenced-code-blocks', 'tables', 'task_list'])
    return {'raw': content, 'html': html, 'filename': filename}


def get_main_memory():
    """Read MEMORY.md."""
    if not os.path.exists(MEMORY_FILE):
        return None
    with open(MEMORY_FILE, 'r') as f:
        content = f.read()
    html = markdown2.markdown(content, extras=['fenced-code-blocks', 'tables', 'task_list'])
    return {'raw': content, 'html': html}


def get_memory_stats():
    """Get memory file statistics."""
    files = get_memory_files()
    return {
        'total_files': len(files),
        'has_main_memory': os.path.exists(MEMORY_FILE)
    }
