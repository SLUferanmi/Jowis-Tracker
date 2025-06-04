# this file contains the models for the application
from app import db
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

#create a User model in classes
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    tasks = db.relationship("Task", backref="assigned_to", cascade='all, delete-orphan',passive_deletes=True)
    role = db.Column(db.String(50), nullable=False, default="employee") # or admin
    projects = db.relationship('Project',cascade= "all, delete-orphan", back_populates='user', passive_deletes=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tasks = db.relationship("Task", backref="project", cascade="all, delete-orphan", passive_deletes=True)
    milestones = db.relationship("Milestone", backref="project", cascade="all, delete-orphan", passive_deletes=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    user = db.relationship('User', back_populates='projects')
    deadline = db.Column(db.DateTime, nullable=False, default = datetime.now(timezone.utc)) # default to current time in UTC
    status = db.Column(db.String(20), nullable=False, default="Pending") 
    comment = db.Column(db.Text, nullable=True) 
    def update_status(self):
        if not self.milestones or self.milestones.count() == 0:
            self.status = "Pending"
        elif all(m.status == "Completed" for m in self.milestones):
            self.status = "Completed"
        elif any(m.status == "Pending" for m in self.milestones):
            self.status = "Pending"
        else:
            self.status = "In Progress"

class Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id", ondelete="CASCADE"), nullable=False) # ondelete="CASCADE" ensures that if a project is deleted, its milestones are also deleted
    tasks = db.relationship("Task", backref="milestone", lazy="dynamic")
    status = db.Column(db.String(20), nullable=False, default="Pending")

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Not Started")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)  # ondelete="CASCADE" ensures that if a user is deleted, their tasks are also deleted
    milestone_id = db.Column(db.Integer, db.ForeignKey("milestone.id", ondelete= "CASCADE"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete= "CASCADE"), nullable=False)
