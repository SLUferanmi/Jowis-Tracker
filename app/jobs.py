from app import scheduler
from app.dbmodels import User, Project
from app.utils import send_email

@scheduler.task('interval', id='remind_projects', hours=24)
def remind_projects():
    with scheduler.app.app_context():
        for user in User.query.filter_by(role='employee').all():
            projects = user.projects
            if projects:
                send_email(
                    subject="Project Reminder",
                    recipients=[user.email],
                    body=f"Hi {user.username},\n\nYou have {len(projects)} active projects. Please check your dashboard."
                )