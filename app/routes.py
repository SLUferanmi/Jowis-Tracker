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
                return redirect ("admin")
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
    # Check if the user is an admin 
    if current_user.role != "admin":
        del form.user  # Remove the user field from the form if not admin
    if form.validate_on_submit():
        if current_user.role == "admin":
            assigned_user = form.user.data
        else:
            assigned_user = current_user
        project = Project(
            title=form.title.data,
            description=form.description.data,
            deadline=form.deadline.data,
            user_id=assigned_user.id
        )
        db.session.add(project)
        db.session.commit()
        flash('Project added successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_project.html', form=form)

#Update project form route
@main.route("/project/<int:project_id>/edit", methods=["GET"])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if int(project.user_id) != int(current_user.id):
        flash("You do not have permission to edit this project.", "danger")
        abort (403)
        return redirect(url_for("main.dashboard"))
    return render_template("edit_project.html", project=project)

# update project save route
@main.route("/project/<int:project_id>/edit", methods=["POST"])
@login_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id != current_user.id:
        flash("You do not have permission to edit this project.", "danger")
        abort (403)
    project.title = request.form["title"]
    project.description = request.form["description"]
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



