import os
from dotenv import load_dotenv

# Loads environment variables from a .env file if it exists
load_dotenv() 

class Config:
    # --- Database Configuration ---
    # Specifies the database connection string. Uses DATABASE_URL from environment
    # or defaults to a local SQLite database named 'posts.db'.
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///posts.db')

    # --- File Upload Configuration ---
    # Defines the folder where uploaded assets (images, etc.) will be stored.
    UPLOAD_FOLDER = 'static/uploads/'

    # --- Security Configuration ---
    # Secret key for session management, CSRF protection, etc.
    # CRITICAL: Should be set to a strong, unique value in the .env file for production.
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_default_secret_key')

    # --- Flask-FlatPages Configuration ---
    # The file extension for your Markdown post files.
    FLATPAGES_EXTENSION = '.md'
    # The root directory where your Markdown post files are stored.
    FLATPAGES_ROOT = 'posts'
    # Automatically reload FlatPages data when a file changes (useful for development).
    FLATPAGES_AUTO_RELOAD = True