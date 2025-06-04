import os

# Define the base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Define the configuration class
class Config:
    SECRET_KEY = "@Busayoranmi*80"  # Replace with something tough
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications to save resources

    # Email server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your_email@gmail.com'
    MAIL_PASSWORD = 'your_email_password'
    MAIL_DEFAULT_SENDER = 'your_email@gmail.com'