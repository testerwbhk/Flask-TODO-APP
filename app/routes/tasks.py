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
    user = User.query.filter_by(username=session['user']).first()
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
# Route renamed from '/clear' to '/clear-all'
@tasks_bp.route('/clear-all', methods=['POST'])
def clear_tasks():
    user = User.query.filter_by(username=session['user']).first()

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
