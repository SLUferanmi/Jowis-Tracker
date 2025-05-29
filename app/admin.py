from flask_admin import Admin
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, request
from wtforms import SelectField
from .dbmodels import Project, User
from . import db

class UserModelView(ModelView):
    # Only allow deletion
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True  # Optional, lets admin view full user info

    # Only show the username and email columns
    column_exclude_list = ['password_hash']

    form_overrides = {
        'role': SelectField
    }

    form_args = {
        'role': {
            'choices': [
                ('employee', 'Employee'),
                ('admin', 'Admin')
            ]
        }
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.login', next=request.url))
admin = Admin(name='Jowis Admin')


class ProjectModelView(ModelView):
    form_columns = ['title', 'description', 'user'] 

    # form_args = {
    #     'user': {
    #         'query_factory': lambda: User.query.all(),
    #         'get_label': 'username'  # show username in the dropdown
    #     }
    # }

    form_extra_fields = {
        'user': QuerySelectField(
            'User',
            query_factory=lambda: User.query.all(),
            get_label='username'
        )
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.login', next=request.url))


def init_admin(app):
    admin.init_app(app)
    admin.add_view(ProjectModelView(Project, db.session))
    admin.add_view(UserModelView(User, db.session))
