from flask import render_template, redirect, url_for, flash, request, Blueprint, abort
from flask_login import login_user, logout_user, login_required, current_user
from .dbmodels import User, db, Project, Milestone, Task, ProjectInvite, Notification
from datetime import datetime, timedelta
from .forms import SignupForm, ProjectForm, MilestoneForm
import os
from app.utils import send_email, notify
import random
import secrets
import string

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/dashboard")
@login_required
def dashboard():
    show_completed = request.args.get('show_completed')
    show_all = request.args.get('show_all')
    show_pending = request.args.get('show_pending')
    if show_all:
        if current_user.role == "admin":
            projects = Project.query.all()
        else:
            projects = current_user.projects
    elif show_completed:
        if current_user.role == "admin":
            projects = Project.query.filter_by(status='Completed').all()
        else:
            projects = [p for p in current_user.projects if p.status == 'Completed']
    elif show_pending:
        if current_user.role == "admin":
            projects = Project.query.filter(Project.status != 'Completed').all()
        else:
            projects = [p for p in current_user.projects if p.status != 'Completed']
    else:
        # Default to pending
        if current_user.role == "admin":
            projects = Project.query.filter(Project.status != 'Completed').all()
        else:
            projects = [p for p in current_user.projects if p.status != 'Completed']

    pending_invites = ProjectInvite.query.filter_by(email=current_user.email, accepted=False).all()

    if current_user.role == "admin":
        active_count = Project.query.filter(Project.status != 'Completed').count()
        pending_tasks = Milestone.query.filter(Milestone.status != 'Completed').count()
    else:
        active_count = len([p for p in current_user.projects if p.status != 'Completed'])
        # Count all milestones in user's projects that are not completed
        pending_tasks = sum(
            1 for p in current_user.projects for m in p.milestones if m.status != 'Completed'
        )

    return render_template(
        "dashboard.html",
        projects=projects,
        pending_invites=pending_invites,
        active_count=active_count,
        pending_tasks=pending_tasks
    )

@main.route("/go_dashboard")
@login_required
def go_dashboard():
    if current_user.role == "admin":
        return redirect(url_for('main.admin_dashboard'))
    else:
        return redirect(url_for('main.dashboard'))

@main.route("/project/<int:project_id>")
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user.role != 'admin' and current_user not in project.users:
        abort(403)
    milestones = Milestone.query.filter_by(project_id=project.id).order_by(Milestone.deadline).all()
    return render_template("project_detail.html", project=project, milestones=milestones)

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            if user.role == "admin":
                return redirect(url_for("main.admin_dashboard"))
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))

ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'jowisadmin123')
@main.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_mail = User.query.filter_by(email=form.email.data).first()
        existing_username = User.query.filter_by(username=form.username.data).first()
        if existing_mail:
            flash("Email already registered. Please use a different email.", "danger")
            return redirect(url_for("main.signup"))
        if existing_username:
            flash("Username already taken. Please choose a different username.", "danger")
            return redirect(url_for("main.signup"))
        entered_code = form.admin_code.data.strip() if form.admin_code.data else ""
        role = "admin" if entered_code == ADMIN_SECRET else "employee"
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role=role
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("main.login"))
    return render_template("signup.html", form=form)

@main.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    form = ProjectForm()
    employees = User.query.filter_by(role='employee').all() if current_user.role == "admin" else []
    if current_user.role != "admin" and hasattr(form, 'users'):
        del form.users

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        deadline_str = request.form.get('deadline')
        status = request.form.get('status')

        # Validate required fields
        if not title or not description or not deadline_str or not status:
            flash("Please fill in all required fields.", "danger")
            return render_template('add_project.html', form=form, employees=employees)

        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid deadline format. Please use the date picker.", "danger")
            return render_template('add_project.html', form=form, employees=employees)

        project = Project(
            title=title,
            description=description,
            deadline=deadline,
            status=status
        )
        if current_user.role == "admin":
            selected_user_ids = request.form.getlist('assigned_users')
            selected_users = User.query.filter(User.id.in_(selected_user_ids)).all()
            project.users = selected_users
        else:
            project.users = [current_user]
        db.session.add(project)
        db.session.commit()
        flash('Project added successfully!', 'success')
        for user in project.users:
            if user == current_user:
                notify(user, f"You successfully created the project '{project.title}'.")
            else:
                notify(user, f"You have been assigned to a new project: '{project.title}'.")
        if current_user.role == "admin":
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    return render_template('add_project.html', form=form, employees=employees)

@main.route("/project/<int:project_id>/edit", methods=["GET"])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    if current_user.role == "admin":
        form.users.choices = [(u.id, u.username) for u in User.query.all()]
    else:
        if hasattr(form, 'users'):
            del form.users
    if current_user.role != 'admin' and current_user not in project.users:
        flash("You do not have permission to edit this project.", "danger")
        abort(403)
    return render_template("edit_project.html", project=project, form=form)

@main.route("/project/<int:project_id>/edit", methods=["POST"])
@login_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    if current_user.role == "admin":
        form.users.choices = [(u.id, u.username) for u in User.query.all()]
    else:
        if hasattr(form, 'users'):
            del form.users
    if form.validate_on_submit():
        if current_user.role != 'admin' and current_user not in project.users:
            flash("You do not have permission to edit this project.", "danger")
            abort(403)
        project.title = form.title.data
        project.description = form.description.data
        project.deadline = form.deadline.data
        project.status = form.status.data
        if current_user.role == "admin":
            selected_users = User.query.filter(User.id.in_(form.users.data)).all()
            project.users = selected_users
        db.session.commit()
        flash("Project updated successfully!", "success")
        # Notify users about the project update
        for user in project.users:
            if user == current_user:
                notify(user, f"You updated the project '{project.title}'.")
            else:
                notify(user, f"Project '{project.title}' was updated.")
        return redirect(url_for("main.dashboard"))
    # If not valid, re-render form
    else:
        if request.method == "POST":
            flash("Please correct the errors in the form.", "danger")
    return render_template("edit_project.html", project=project, form=form)

@main.route('/project/<int:project_id>/add_milestone', methods=['GET', 'POST'])
@login_required
def add_milestone(project_id):
    form = MilestoneForm()
    project = Project.query.get_or_404(project_id)
    if form.validate_on_submit():
        milestone = Milestone(
            name=form.name.data,
            deadline=form.deadline.data,
            status=form.status.data,
            project_id=project_id
        )
        db.session.add(milestone)
        db.session.commit()
        if hasattr(project, "update_status"):
            project.update_status()
            db.session.commit()
        flash('Milestone added successfully!', 'success')
        for user in project.users:
            if user == current_user:
                notify(user, f"You added a new milestone '{milestone.name}' to project '{project.title}'.")
            else:
                notify(user, f"A new milestone '{milestone.name}' was added to project '{project.title}'.")
        return redirect(url_for('main.dashboard'))
    else:
        if request.method == "POST":
            flash("Please correct the errors in the form.", "danger")
    return render_template('add_milestone.html', form=form, project_id=project_id)

@main.route("/milestone/<int:milestone_id>/edit", methods=["GET"])
@login_required
def edit_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    if current_user.role != 'admin' and current_user not in milestone.project.users:
        flash("You do not have permission to edit this milestone.", "danger")
        abort(403)
    return render_template("edit_milestone.html", milestone=milestone)

@main.route("/milestone/<int:milestone_id>/edit", methods=["POST"])
@login_required
def update_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    if current_user.role != 'admin' and current_user not in milestone.project.users:
        flash("You do not have permission to edit this milestone.", "danger")
        abort(403)
    milestone.name = request.form["name"]
    deadline_input = request.form.get("deadline")
    if deadline_input:
        try:
            milestone.deadline = datetime.strptime(deadline_input, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(request.url)
    else:
        milestone.deadline = None
    milestone.status = request.form["status"]
    db.session.commit()
    flash("Milestone updated successfully!", "success")
    # Notify users about the milestone update
    for user in milestone.project.users:
        if user == current_user:
            notify(user, f"You updated milestone '{milestone.name}' in project '{milestone.project.title}'.")
        else:
            notify(user, f"Milestone '{milestone.name}' in project '{milestone.project.title}' was updated.")
    return redirect(url_for("main.dashboard"))

@main.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        abort(403)
    user_count = User.query.count()
    project_count = Project.query.count()
    completed_count = Project.query.filter_by(status='Completed').count()
    projects = Project.query.order_by(Project.deadline.desc()).all()
    return render_template(
        'admin_dashboard.html',
        user_count=user_count,
        project_count=project_count,
        completed_count=completed_count,
        projects=projects
    )

@main.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != "admin":
        abort(403)
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@main.route('/admin/projects')
@login_required
def admin_projects():
    if current_user.role != "admin":
        abort(403)
    status = request.args.get('status')
    show_completed = request.args.get('show_completed')
    if status:
        projects = Project.query.filter_by(status=status).all()
    elif show_completed:
        projects = Project.query.filter_by(status='Completed').all() if current_user.role == "admin" else [p for p in current_user.projects if p.status == 'Completed']
    else:
        projects = Project.query.all()
    return render_template('admin_projects.html', projects=projects)

@main.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        abort(403)
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for('main.admin_users'))

@main.route('/admin/users/<int:user_id>')
@login_required
def view_user(user_id):
    if current_user.role != "admin":
        abort(403)
    user = User.query.get_or_404(user_id)
    return render_template('view_user.html', user=user)

@main.route('/admin/projects/<int:project_id>', methods=['GET', 'POST'])
@login_required
def admin_project_detail(project_id):
    if current_user.role != "admin":
        abort(403)
    project = Project.query.get_or_404(project_id)
    employees = User.query.filter_by(role='employee').all()
    assigned_user_ids = [u.id for u in project.users]
    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        deadline_input = request.form.get('deadline')
        if deadline_input:
            project.deadline = datetime.strptime(deadline_input, "%Y-%m-%dT%H:%M")
        project.status = request.form.get('status')
        project.comment = request.form.get('comment')
        selected_user_ids = request.form.getlist('assigned_users')
        selected_users = User.query.filter(User.id.in_(selected_user_ids)).all()
        project.users = selected_users
        db.session.commit()
        flash("Project updated successfully!", "success")
        for user in project.users:
            if user.email:
                send_email(
                    subject="Admin Comment on Your Project",
                    recipients=[user.email],
                    body=f"Hi {user.username},\n\nAn admin commented on your project '{project.title}':\n\n{project.comment}\n\nPlease log in to view details."
                )
        return redirect(url_for('main.admin_project_detail', project_id=project.id))
    return render_template('admin_project_detail.html', project=project,  employees=employees, assigned_user_ids=assigned_user_ids)

@main.route('/admin/users/<int:user_id>/projects')
@login_required
def admin_user_projects(user_id):
    if current_user.role != "admin":
        abort(403)
    user = User.query.get_or_404(user_id)
    projects = user.projects
    return render_template('admin_user_projects.html', user=user, projects=projects)

@main.route('/admin/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    if current_user.role != "admin":
        abort(403)
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "success")
    return redirect(url_for('main.admin_projects'))

@main.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def employee_delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user.role != "admin" and current_user not in project.users:
        abort(403)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "success")
    # Notify users about the project deletion
    for user in project.users:
        if user == current_user:
            notify(user, f"You deleted the project '{project.title}'.")
        else:
            notify(user, f"Project '{project.title}' was deleted.")
    if current_user.role == "admin":
        return redirect(url_for('main.admin_projects'))
    else:
        return redirect(url_for('main.dashboard'))

@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            code = ''.join(random.choices(string.digits, k=6))
            user.reset_code = code
            user.reset_code_expiry = datetime.utcnow() + timedelta(minutes=15)
            db.session.commit()
            send_email(
                subject="Password Reset Code",
                recipients=[user.email],
                body=f"Your password reset code is: {code}\nThis code expires in 15 minutes."
            )
            return redirect(url_for('main.reset_password', user_id=user.id))
        else:
            flash("No account found with that email.", "danger")
    return render_template('forgot_password.html')

@main.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        code = request.form.get('code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password.html', user=user)
        if (user.reset_code == code and 
            user.reset_code_expiry and 
            user.reset_code_expiry > datetime.utcnow()):
            user.set_password(new_password)
            user.reset_code = None
            user.reset_code_expiry = None
            db.session.commit()
            flash("Password reset successful! You can now log in.", "success")
            return redirect(url_for('main.login'))
        else:
            flash("Invalid or expired code.", "danger")
    return render_template('reset_password.html', user=user)

@main.route('/project/<int:project_id>/invite', methods=['GET', 'POST'])
@login_required
def invite_user(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        email = request.form.get('email')
        token = secrets.token_urlsafe(32)
        invite = ProjectInvite(email=email, project_id=project.id, inviter_id=current_user.id, token=token)
        db.session.add(invite)
        db.session.commit()
        accept_url = url_for('main.dashboard', _external=True)
        send_email(
            subject="Project Collaboration Invite",
            recipients=[email],
            body=f"You've been invited to join the project '{project.title}'.\n"
                 f"Login to your dashboard to accept the invite.\n"
                 f"Project details:\nTitle: {project.title}\nDescription: {project.description}\nDeadline: {project.deadline}\n"
                 f"Invited by: {current_user.username}\n"
                 f"Or click: {accept_url}"
        )
        flash("Invitation sent.", "success")
        notify(current_user, f"You sent an invite to {email} for project '{project.title}'.")
        # Optionally, notify the invited user if they already exist in the system:
        invited_user = User.query.filter_by(email=email).first()
        if invited_user:
            notify(invited_user, f"You have been invited to join the project '{project.title}'.")
        if current_user.role == "admin":
            return redirect(url_for('main.admin_project_detail', project_id=project.id))
        else:
            return redirect(url_for('main.project_detail', project_id=project.id))
    return render_template('invite_user.html', project=project)

@main.route('/accept_invite/<int:invite_id>', methods=['POST'])
@login_required
def accept_invite(invite_id):
    invite = ProjectInvite.query.get_or_404(invite_id)
    if invite.email != current_user.email or invite.accepted:
        abort(403)
    if hasattr(invite.project, 'users'):
        invite.project.users.append(current_user)
    invite.accepted = True
    db.session.commit()
    flash("You have joined the project!", "success")
    notify(current_user, f"You accepted the invite to '{invite.project.title}'.")
    notify(invite.inviter, f"{current_user.username} accepted your invite to '{invite.project.title}'.")
    return redirect(url_for('main.dashboard'))

@main.route('/decline_invite/<int:invite_id>', methods=['POST'])
@login_required
def decline_invite(invite_id):
    invite = ProjectInvite.query.get_or_404(invite_id)
    if invite.email != current_user.email or invite.accepted:
        abort(403)
    invite.accepted = False
    db.session.commit()
    notify(invite.inviter, f"{current_user.username} declined your invite to '{invite.project.title}'.")
    flash("You have declined the invitation.", "info")
    notify(current_user, f"You declined the invite to '{invite.project.title}'.")
    notify(invite.inviter, f"{current_user.username} declined your invite to '{invite.project.title}'.")
    return redirect(url_for('main.dashboard'))

@main.route('/invitations')
@login_required
def invitation_details():
    pending_invites = ProjectInvite.query.filter_by(email=current_user.email, accepted=False).all()
    return render_template('invitation_details.html', pending_invites=pending_invites)

@main.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        old_username = current_user.username
        old_email = current_user.email
        username = request.form.get('username')
        email = request.form.get('email')
        changed = False

        if username and username != current_user.username:
            current_user.username = username
            changed = True
        if email and email != current_user.email:
            current_user.email = email
            changed = True

        if changed:
            db.session.commit()
            send_email(
                subject="Account Details Changed",
                recipients=[current_user.email],
                body=f"Hi {current_user.username},\n\nYour account details have been updated.\n\nIf you did not make this change, please contact support."
            )
            flash("Account details updated and notification sent to your email.", "success")
            notify(current_user, "Your account details were updated.")
        else:
            flash("No changes made.", "info")
    return render_template('account.html')

@main.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        # Send code to email
        code = ''.join(random.choices(string.digits, k=6))
        current_user.reset_code = code
        current_user.reset_code_expiry = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
        send_email(
            subject="Password Change Code",
            recipients=[current_user.email],
            body=f"Your password change code is: {code}\nThis code expires in 15 minutes."
        )
        flash("A code has been sent to your email. Enter it below to change your password.", "info")
        return redirect(url_for('main.confirm_change_password'))
    return render_template('change_password.html')

@main.route('/confirm_change_password', methods=['GET', 'POST'])
@login_required
def confirm_change_password():
    
    if request.method == 'POST':
        code = request.form.get('code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password.html', user=current_user)
        if (current_user.reset_code == code and
            current_user.reset_code_expiry and
            current_user.reset_code_expiry > datetime.utcnow()):
            current_user.set_password(new_password)
            current_user.reset_code = None
            current_user.reset_code_expiry = None
            db.session.commit()
            send_email(
                subject="Password Changed",
                recipients=[current_user.email],
                body="Your password has been changed successfully. If you did not perform this action, contact support immediately."
            )
            flash("Password changed successfully.", "success")
            notify(current_user, "Your password was changed.")
            return redirect(url_for('main.account'))
        else:
            flash("Invalid or expired code.", "danger")
    return render_template('confirm_change_password.html')

@main.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    # Mark all as read
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)



