from flask_mail import Message
from app import mail
from flask import current_app
from .dbmodels import Notification, db

def send_email(subject, recipients, body):
    msg = Message(subject, recipients=recipients, body=body)
    with current_app.app_context():
        mail.send(msg)

def notify(user, message):
    notif = Notification(user_id=user.id, message=message)
    db.session.add(notif)
    db.session.commit()    