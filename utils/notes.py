import os
import json
import uuid
from datetime import datetime
from config import NOTES_FILE, ACTIVITY_LOG


def _load_notes():
    """Load notes from JSON file."""
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return []


def _save_notes(notes):
    """Save notes to JSON file."""
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2)


def _log_activity(action):
    """Log a dashboard action to activity.log."""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'source': 'dashboard'
    }
    with open(ACTIVITY_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def get_notes():
    """Get all notes, newest first."""
    notes = _load_notes()
    return sorted(notes, key=lambda n: n.get('timestamp', ''), reverse=True)


def add_note(text):
    """Add a new note."""
    notes = _load_notes()
    note = {
        'id': str(uuid.uuid4())[:8],
        'text': text,
        'timestamp': datetime.now().isoformat(),
        'status': 'pending'
    }
    notes.append(note)
    _save_notes(notes)
    _log_activity(f'Note added: {text[:60]}')
    return note


def update_note(note_id, status):
    """Update a note's status."""
    notes = _load_notes()
    for note in notes:
        if note['id'] == note_id:
            note['status'] = status
            note['updated_at'] = datetime.now().isoformat()
            _save_notes(notes)
            _log_activity(f'Note {note_id} marked as {status}')
            return note
    return None
