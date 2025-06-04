from flask import render_template, redirect, url_for
from flask import flash, request, Blueprint, abort
from flask_login import login_user, logout_user, login_required, current_user
from .dbmodels import User, db, Project, Milestone, Task
from app import db
from datetime import datetime
from .forms import SignupForm, ProjectForm, MilestoneForm
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Create a blueprint for the main routes
main = Blueprint("main", __name__)

# Route for the home page
@main.route("/")
def index(): 
    return render_template("index.html")

# Route for dashboard page
@main.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        # Fetch all users for manager
        projects = Project.query.all()
    else:
        projects = current_user.projects

    project_data = []
    for project in projects:
        latest_milestone = Milestone.query.filter_by(project_id=project.id).order_by(Milestone.deadline.desc()).first()
        project_data.append({
            "project": project,
            "latest_milestone": latest_milestone
        })
        # Fetch projects for employee
    return render_template("dashboard.html", projects=projects)

# route for more details of a project
@main.route("/project/<int:project_id>")
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id and current_user.role != 'admin':
        abort(403)

    milestones = Milestone.query.filter_by(project_id=project.id).order_by(Milestone.deadline).all()

    return render_template("project_detail.html", project=project, milestones=milestones)


# Route for login page
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method== "POST":
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
    

# Route for signup page
ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'jowisadmin123')
@main.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_mail = User.query.filter_by(email= form.email.data).first()
        existing_username = User.query.filter_by(username= form.username.data).first()

        if existing_mail:
            flash("Email already registered. Please use a different email.", "danger")
            return redirect(url_for("main.signup"))
        
        if existing_username:
            flash("Username already taken. Please choose a different username.", "danger")
            return redirect(url_for("main.signup"))
        
        # Determine role based on admin code
        entered_code = form.admin_code.data.strip() if form.admin_code.data else ""
        role = "admin" if entered_code == ADMIN_SECRET else "employee"
        
        # Create a new user instance
        new_user = User(
            username = form.username.data, 
            email= form.email.data,
            role= role
        )
        new_user.set_password(form.password.data)
        
        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("main.login"))
    
    return render_template("signup.html", form=form)

# Route for creating a new project


@main.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        if current_user.role == "admin":
            assigned_user = form.user.data
        else:
            assigned_user = current_user
        project = Project(
            title=form.title.data,
            description=form.description.data,
            deadline=form.deadline.data,
            user_id=assigned_user.id,
            status=form.status.data
        )
        db.session.add(project)
        db.session.commit()
        flash('Project added successfully!', 'success')
        if current_user.role == "admin":
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    return render_template('add_project.html', form=form)

#Update project form route
@main.route("/project/<int:project_id>/edit", methods=["GET"])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    if int(project.user_id) != int(current_user.id):
        flash("You do not have permission to edit this project.", "danger")
        abort (403)
        return redirect(url_for("main.dashboard"))
    return render_template("edit_project.html", project=project, form=form)

# update project save route
@main.route("/project/<int:project_id>/edit", methods=["POST"])
@login_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        if project.user_id != current_user.id:
            flash("You do not have permission to edit this project.", "danger")
            abort (403)
    project.title = request.form["title"]
    project.description = request.form["description"]
    project.deadline = form.deadline.data
    project.status = form.status.data
    db.session.commit()
    flash("Project updated successfully!", "success")
    return redirect(url_for("main.dashboard"))

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
        project.update_status()  
        db.session.commit()
        flash('Milestone added successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_milestone.html', form=form, project_id=project_id)

# edit milestone form route
@main.route("/milestone/<int:milestone_id>/edit", methods=["GET"])
@login_required
def edit_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    if milestone.project.user_id != current_user.id:
        flash("You do not have permission to edit this milestone.", "danger")
        abort (403)
    return render_template("edit_milestone.html", milestone=milestone)

# update milestone save route
@main.route("/milestone/<int:milestone_id>/edit", methods=["POST"])
@login_required
def update_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    if milestone.project.user_id != current_user.id:
        flash("You do not have permission to edit this milestone.", "danger")
        abort (403)
    milestone.name = request.form["name"]
    deadline_input = request.form.get("deadline")
    if deadline_input:
        try:
            # Adjust format depending on your HTML input (assumed YYYY-MM-DD)
            milestone.deadline = datetime.strptime(deadline_input, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(request.url)
    else:
        milestone.deadline = None  # allow blank deadline
    milestone.status = request.form["status"]
    db.session.commit()
    flash("Milestone updated successfully!", "success")
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
    if status:
        projects = Project.query.filter_by(status=status).all()
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
    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        deadline_input = request.form.get('deadline')
        if deadline_input:
            project.deadline = datetime.strptime(deadline_input, "%Y-%m-%dT%H:%M")
        project.status = request.form.get('status')
        project.comment = request.form.get('comment')
        db.session.commit()
        flash("Project updated successfully!", "success")
        return redirect(url_for('main.admin_project_detail', project_id=project.id))
    return render_template('admin_project_detail.html', project=project)

@main.route('/admin/users/<int:user_id>/projects')
@login_required
def admin_user_projects(user_id):
    if current_user.role != "admin":
        abort(403)
    user = User.query.get_or_404(user_id)
    projects = user.projects
    return render_template('admin_user_projects.html', user=user, projects=projects)



