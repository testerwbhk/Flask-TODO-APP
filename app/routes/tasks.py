from flask import Blueprint, redirect, request, url_for, render_template, session, flash
from app import db
from app.models import Task, User

tasks_bp = Blueprint('tasks', __name__)


# Display all tasks belonging to the logged-in user
@tasks_bp.route('/')
def view_tasks():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['user']).first()

    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('auth.logout'))

    tasks = Task.query.filter_by(user_id=user.id).all()
    return render_template('tasks.html', tasks=tasks)


# Create a new task
@tasks_bp.route('/add', methods=['POST'])
def add_task():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    title = request.form.get('title')

    if title:
        user = User.query.filter_by(username=session['user']).first()

        new_task = Task(
            title=title,
            status='Pending',
            user_id=user.id
        )

        db.session.add(new_task)
        db.session.commit()

        flash('Task added successfully!', 'success')

    return redirect(url_for('tasks.view_tasks'))


# Cycle task status: Pending -> Working -> Done -> Pending
@tasks_bp.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_status(task_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['user']).first()
    
    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('auth.logout'))

    task = Task.query.filter_by(id=task_id, user_id=user.id).first()

    if task:
        if task.status.lower() == 'pending':
            task.status = 'Working'
        elif task.status.lower() == 'working':
            task.status = 'Done'
        else:
            task.status = 'Pending'

        print(f"Task {task.id} new status: {task.status}")
        db.session.commit()

    return redirect(url_for('tasks.view_tasks'))


# Clear all tasks owned by the current user
@tasks_bp.route('/clear-all', methods=['POST'])
def clear_tasks():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['user']).first()
    
    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('auth.logout'))

    Task.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    flash('All tasks have been removed successfully.', 'info')

    return redirect(url_for('tasks.view_tasks'))


# Delete a single task belonging to the current user
@tasks_bp.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['user']).first()

    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('auth.logout'))

    task = Task.query.filter_by(
        id=task_id,
        user_id=user.id
    ).first()

    if task:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted.', 'info')
    else:
        flash('Task not found or not authorized.', 'error')

    return redirect(url_for('tasks.view_tasks'))


# Task statistics endpoint
# Returns a summary of the current user's tasks
@tasks_bp.route('/stats')
def task_stats():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['user']).first()

    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('auth.logout'))

    tasks = Task.query.filter_by(user_id=user.id).all()

    stats = {
        'total': len(tasks),
        'pending': sum(1 for t in tasks if t.status.lower() == 'pending'),
        'working': sum(1 for t in tasks if t.status.lower() == 'working'),
        'done': sum(1 for t in tasks if t.status.lower() == 'done')
    }

    return stats


# API endpoint to retrieve all tasks in JSON format
# Useful for documentation, mobile apps, or frontend AJAX requests
@tasks_bp.route('/export', methods=['GET'])
def export_tasks():
    if 'user' not in session:
        return {'error': 'Unauthorized. Please log in.'}, 401

    user = User.query.filter_by(username=session['user']).first()

    if not user:
        return {'error': 'User not found.'}, 404

    tasks = Task.query.filter_by(user_id=user.id).all()
    
    # Serialize the tasks into a list of dictionaries
    task_list = [
        {
            'id': task.id,
            'title': task.title,
            'status': task.status
        } for task in tasks
    ]

    return {'tasks': task_list}
