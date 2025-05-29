# Semi main file. Initializes flask app and modules needed
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Initialize Flask modules not attached yet
db = SQLAlchemy() 
migrate = Migrate()
login_manager = LoginManager()

# creates app function
def create_app():
    app= Flask(__name__)

    app.config.from_object("config.Config") # load app config from config.py

    db.init_app(app) 
    migrate.init_app(app, db)
    login_manager.init_app(app) 

    from .admin import init_admin
    init_admin(app)

    login_manager.login_view = "main.login" 
    login_manager.login_message_category ="info"

    #imports the User model to use with Flask-Login
    from .dbmodels import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    
    
    # import and register blueprints
    from .routes import main
    app.register_blueprint(main)

    return app