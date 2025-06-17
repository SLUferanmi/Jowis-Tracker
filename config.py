import os

# Define the base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Define the configuration class
class Config:
    SECRET_KEY = "@Busayoranmi*80"  # Replace with something tough
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications to save resources

    # Email server settings
    MAIL_SERVER = 'smtp.zoho.com' 
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'feranmi.j@jowistudio.com'  # Replace with your email address
    MAIL_PASSWORD = 'rNFiUiSpcKqN'
    MAIL_DEFAULT_SENDER = 'feranmi.j@jowistudio.com' 
    MAIL_USE_SSL = False