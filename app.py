#!/usr/bin/env python3
"""Chitty Dashboard - Flask web dashboard for Clawdbot monitoring."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, request, abort, redirect, url_for, session, flash
from datetime import datetime, date
from utils.system import get_system_info, get_services
from utils.memory import get_memory_files, get_memory_content, get_main_memory, get_memory_stats
from utils.activity import get_activities, get_today_activities, get_available_dates, get_categories
from utils.tasks import get_all_tasks, get_task_stats, add_task, move_task, move_file_task
from utils.emails import check_emails, get_email_status
from utils.notes import get_notes, add_note, update_note
from utils.docs import get_all_docs, get_doc_content
from utils.status import get_ai_status, update_status
from utils.auth import (
    init_users, authenticate, get_all_users, create_user, delete_user,
    get_current_user, login_required, admin_required
)
import json
from config import HEARTBEAT_STATE, FLASK_HOST, FLASK_PORT, FLASK_DEBUG, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize default admin user
init_users()


@app.context_processor
def inject_user():
    """Make current user available in all templates."""
    return dict(current_user=get_current_user())


def get_heartbeat_state():
    """Read heartbeat state file."""
    try:
        if os.path.exists(HEARTBEAT_STATE):
            with open(HEARTBEAT_STATE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


# ─── Auth Routes ───

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember')
        user = authenticate(username, password)
        if user:
            session['user'] = user
            if remember:
                session.permanent = True
            next_url = request.args.get('next', url_for('dashboard'))
            return redirect(next_url)
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ─── Admin Routes ───

@app.route('/admin')
@admin_required
def admin_panel():
    users = get_all_users()
    return render_template('admin.html', page='admin', users=users, now=datetime.now())


@app.route('/admin/create-user', methods=['GET', 'POST'])
@admin_required
def admin_create_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        role = request.form.get('role', 'viewer')
        if not username or not password:
            flash('Username and password are required', 'danger')
        elif password != confirm:
            flash('Passwords do not match', 'danger')
        elif role not in ('admin', 'viewer'):
            flash('Invalid role', 'danger')
        else:
            user, error = create_user(username, password, role, session['user']['username'])
            if error:
                flash(error, 'danger')
            else:
                flash(f'User "{username}" created successfully', 'success')
                return redirect(url_for('admin_panel'))
    return render_template('create_user.html', page='admin', now=datetime.now())


@app.route('/admin/delete-user/<user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if user_id == session['user']['id']:
        flash('You cannot delete your own account', 'danger')
    else:
        success, error = delete_user(user_id)
        if success:
            flash('User deleted successfully', 'success')
        else:
            flash(error or 'Failed to delete user', 'danger')
    return redirect(url_for('admin_panel'))


# ─── Page Routes ───

@app.route('/')
@login_required
def dashboard():
    sys_info = get_system_info()
    mem_stats = get_memory_stats()
    task_stats = get_task_stats()
    activities = get_today_activities(limit=10)
    heartbeat = get_heartbeat_state()
    email_status = get_email_status()
    ai_status = get_ai_status()

    return render_template('dashboard.html',
                           page='dashboard',
                           sys_info=sys_info,
                           mem_stats=mem_stats,
                           task_stats=task_stats,
                           activities=activities,
                           heartbeat=heartbeat,
                           email_status=email_status,
                           ai_status=ai_status,
                           now=datetime.now())


@app.route('/activity')
@login_required
def activity():
    target_date = request.args.get('date', None)
    category = request.args.get('category', None)
    activities = get_activities(target_date=target_date, category=category)
    dates = get_available_dates()
    categories = get_categories()
    return render_template('activity.html',
                           page='activity',
                           activities=activities,
                           dates=dates,
                           categories=categories,
                           selected_date=target_date,
                           selected_category=category,
                           now=datetime.now())


@app.route('/tasks')
@login_required
def tasks():
    all_tasks = get_all_tasks()
    return render_template('tasks.html',
                           page='tasks',
                           tasks=all_tasks,
                           now=datetime.now())


@app.route('/emails')
@login_required
def emails():
    status = get_email_status()
    return render_template('emails.html',
                           page='emails',
                           email_status=status,
                           now=datetime.now())


@app.route('/memory')
@login_required
def memory():
    files = get_memory_files()
    filename = request.args.get('file', None)
    content = None
    if filename:
        content = get_memory_content(filename)
    main_memory = get_main_memory()
    return render_template('memory.html',
                           page='memory',
                           files=files,
                           content=content,
                           main_memory=main_memory,
                           selected_file=filename,
                           now=datetime.now())


@app.route('/system')
@login_required
def system():
    sys_info = get_system_info()
    services = get_services()
    return render_template('system.html',
                           page='system',
                           sys_info=sys_info,
                           services=services,
                           now=datetime.now())


@app.route('/notes')
@login_required
def notes():
    all_notes = get_notes()
    return render_template('notes.html',
                           page='notes',
                           notes=all_notes,
                           now=datetime.now())


@app.route('/docs')
@login_required
def docs():
    all_docs = get_all_docs()
    filepath = request.args.get('file', None)
    doc_content = None
    if filepath:
        doc_content = get_doc_content(filepath)
    return render_template('docs.html',
                           page='docs',
                           docs=all_docs,
                           doc_content=doc_content,
                           now=datetime.now())


# ─── API Routes ───

@app.route('/api/status')
@login_required
def api_status():
    sys_info = get_system_info()
    heartbeat = get_heartbeat_state()
    ai = get_ai_status()
    return jsonify({
        'status': 'online',
        'ai_status': ai,
        'uptime': sys_info['uptime'],
        'cpu': sys_info['cpu']['percent'],
        'memory': sys_info['memory']['percent'],
        'disk': sys_info['disk']['percent'],
        'heartbeat': heartbeat,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/activity')
@login_required
def api_activity():
    target_date = request.args.get('date', None)
    limit = request.args.get('limit', None, type=int)
    category = request.args.get('category', None)
    activities = get_activities(target_date=target_date, limit=limit, category=category)
    return jsonify({'activities': activities, 'count': len(activities)})


@app.route('/api/tasks', methods=['GET'])
@login_required
def api_tasks():
    tasks = get_all_tasks()
    return jsonify(tasks)


@app.route('/api/tasks/add', methods=['POST'])
@login_required
def api_tasks_add():
    data = request.get_json(force=True)
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'text is required'}), 400
    priority = data.get('priority', 'normal')
    column = data.get('column', 'todo')
    task = add_task(text, priority=priority, column=column)
    return jsonify({'status': 'ok', 'task': task})


@app.route('/api/tasks/move', methods=['POST'])
@login_required
def api_tasks_move():
    data = request.get_json(force=True)
    new_column = data.get('column', '').strip()
    if new_column not in ('todo', 'in_progress', 'done'):
        return jsonify({'error': 'valid column (todo/in_progress/done) required'}), 400

    source_type = data.get('source_type', 'dashboard')

    if source_type == 'file':
        # Move a file-based task (TODO.md)
        source_file = data.get('source_file', '').strip()
        line_num = data.get('line_num')
        if not source_file or not line_num:
            return jsonify({'error': 'source_file and line_num required for file tasks'}), 400
        try:
            line_num = int(line_num)
        except (ValueError, TypeError):
            return jsonify({'error': 'line_num must be an integer'}), 400
        result = move_file_task(source_file, line_num, new_column)
        if not result:
            return jsonify({'error': 'failed to move file task — line not found or invalid'}), 404
        return jsonify({'status': 'ok', 'task': result})
    else:
        # Move a dashboard task
        task_id = data.get('id', '').strip()
        if not task_id:
            return jsonify({'error': 'id required for dashboard tasks'}), 400
        task = move_task(task_id, new_column)
        if not task:
            return jsonify({'error': 'task not found'}), 404
        return jsonify({'status': 'ok', 'task': task})


@app.route('/api/emails')
@login_required
def api_emails():
    status = get_email_status()
    return jsonify(status)


@app.route('/api/emails/check')
@login_required
def api_emails_check():
    result = check_emails()
    return jsonify(result)


@app.route('/api/memory')
@login_required
def api_memory():
    files = get_memory_files()
    filename = request.args.get('file', None)
    content = None
    if filename:
        content = get_memory_content(filename)
    return jsonify({'files': files, 'content': content})


@app.route('/api/system')
@login_required
def api_system():
    sys_info = get_system_info()
    services = get_services()
    return jsonify({'system': sys_info, 'services': services})


@app.route('/api/notes', methods=['GET'])
@login_required
def api_notes():
    notes = get_notes()
    return jsonify({'notes': notes, 'count': len(notes)})


@app.route('/api/notes/add', methods=['POST'])
@login_required
def api_notes_add():
    data = request.get_json(force=True)
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'text is required'}), 400
    note = add_note(text)
    return jsonify({'status': 'ok', 'note': note})


@app.route('/api/notes/update', methods=['POST'])
@login_required
def api_notes_update():
    data = request.get_json(force=True)
    note_id = data.get('id', '').strip()
    status = data.get('status', '').strip()
    if not note_id or status not in ('pending', 'seen', 'processed'):
        return jsonify({'error': 'id and valid status (pending/seen/processed) required'}), 400
    note = update_note(note_id, status)
    if not note:
        return jsonify({'error': 'note not found'}), 404
    return jsonify({'status': 'ok', 'note': note})


@app.route('/api/docs', methods=['GET'])
@login_required
def api_docs():
    docs = get_all_docs()
    return jsonify({'docs': docs, 'count': len(docs)})


@app.route('/api/docs/view', methods=['GET'])
@login_required
def api_docs_view():
    filepath = request.args.get('path', '')
    if not filepath:
        return jsonify({'error': 'path is required'}), 400
    content = get_doc_content(filepath)
    if not content:
        return jsonify({'error': 'file not found or access denied'}), 404
    return jsonify(content)


@app.route('/api/ai-status', methods=['GET'])
@login_required
def api_ai_status():
    return jsonify(get_ai_status())


if __name__ == '__main__':
    print(f"🤖 Chitty Dashboard starting on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
