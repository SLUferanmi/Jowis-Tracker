# this file contains the models for the application
from app import db
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

project_users = db.Table(
    'project_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE")),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id', ondelete="CASCADE"))
)

#create a User model in classes
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    tasks = db.relationship("Task", backref="assigned_to", cascade='all, delete-orphan',passive_deletes=True)
    role = db.Column(db.String(50), nullable=False, default="employee") # or admin
    projects = db.relationship(
        'Project',
        secondary=project_users,
        back_populates='users'
    )
    reset_code = db.Column(db.String(8), nullable=True)
    reset_code_expiry = db.Column(db.DateTime, nullable=True)

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
    deadline = db.Column(db.DateTime, nullable=False, default = datetime.now(timezone.utc)) # default to current time in UTC
    status = db.Column(db.String(20), nullable=False, default="Pending") 
    comment = db.Column(db.Text, nullable=True) 
    users = db.relationship(
        'User',
        secondary=project_users,
        back_populates='projects'
    )
    
    def update_status(self):
        if not self.milestones or len(self.milestones) == 0:
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

class ProjectInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete="CASCADE"))
    inviter_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    token = db.Column(db.String(64), nullable=False, unique=True, default=lambda: secrets.token_urlsafe(32))
    accepted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project = db.relationship('Project', backref='invites')
    inviter = db.relationship('User', foreign_keys=[inviter_id])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    message = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref='notifications')
