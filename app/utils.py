from flask_mail import Message
from app import mail
from flask import current_app, flash
from .dbmodels import Notification, db
import socket

def send_email(subject, recipients, body):
    msg = Message(subject, recipients=recipients, body=body)
    with current_app.app_context():
        try:
            mail.send(msg)
        except (socket.gaierror, Exception):
            flash("We couldn't send the email. Please check your internet connection or try again later.", "danger")

def notify(user, message):
    notif = Notification(user_id=user.id, message=message)
    db.session.add(notif)
    db.session.commit()