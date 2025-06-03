from flask_wtf import FlaskForm
from wtforms.fields import DateTimeLocalField
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField, BooleanField, DateTimeField, SelectField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo
from .dbmodels import User

class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    admin_code = StringField("Admin Code (Optional)", validators=[Optional()])  # Optional field for admin
    submit = SubmitField("Sign Up")

def employee_query():
    return User.query.filter_by(role='employee')

class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    user = QuerySelectField('Assign User', query_factory=employee_query, get_label='username', allow_blank=False)
    deadline = DateTimeLocalField("Project Deadline", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Create Project')


class MilestoneForm(FlaskForm):
    name = StringField('Milestone Name', validators=[DataRequired()])
    deadline = DateTimeLocalField("Deadline (YYYY-MM-DD HH:MM:SS)", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    status = SelectField("Status", choices=[
        ("Pending", "Pending"),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Milestone')