# Semi main file. Initializes flask app and modules needed
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_apscheduler import APScheduler
from dotenv import load_dotenv
import os

# Initialize Flask modules not attached yet
db = SQLAlchemy() 
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
scheduler = APScheduler()
load_dotenv()

# creates app function
def create_app():
    app= Flask(__name__)

    app.config.from_object("config.Config") # load app config from config.py

    db.init_app(app) 
    migrate.init_app(app, db)
    login_manager.init_app(app) 
    mail.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    from . import jobs  # <-- Import jobs to register them

    from .admin import init_admin
    init_admin(app)

    login_manager.login_view = "main.login" 
    login_manager.login_message_category ="info"

    #imports the User model to use with Flask-Login
    from .dbmodels import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        
        db.create_all()
    
    # import and register blueprints
    from .routes import main
    app.register_blueprint(main)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    return app