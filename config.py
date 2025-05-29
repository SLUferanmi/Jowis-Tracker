import os

# Define the base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Define the configuration class
class Config:
    SECRET_KEY = "@Busayoranmi*80"  # Replace with something tough
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications to save resources