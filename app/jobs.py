from app import scheduler
from app.dbmodels import User, Project
from app.utils import send_email

@scheduler.task('interval', id='remind_projects', hours=24)
def remind_projects():
    with scheduler.app.app_context():
        for user in User.query.filter_by(role='employee').all():
            active_projects = [p for p in user.projects if p.status != 'Completed']
            if active_projects:
                send_email(
                    subject="Jowis Tracker: Project Reminder",
                    recipients=[user.email],
                    body=(
                        f"Hello {user.username},\n\n"
                        "This is an automated reminder from Jowis Tracker.\n\n"
                        f"You have {len(active_projects)} active project(s) assigned to you.\n"
                        "Please review your dashboard for details and deadlines.\n\n"
                        "Access your dashboard here:\n"
                        "https://jowis-tracker.onrender.com/dashboard"
                        "If you have any questions or need assistance, please contact your admin."
                    )
                )