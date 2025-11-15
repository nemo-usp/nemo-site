from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, bcrypt, User # Import db, bcrypt, User AFTER initializing them in models.py
from routes import register_routes

# --- App Initialization ---
app = Flask(__name__)
# Load configuration from config.py
app.config.from_object(Config)

# --- Security Check ---
# Ensure a strong SECRET_KEY is set for production environments
if not app.debug and app.config['SECRET_KEY'] == 'a_default_secret_key':
    # This stops the app if the default key is used outside of debug mode
    raise ValueError('A proper SECRET_KEY must be set in the .env file for production.')

# --- Extension Initialization ---
db.init_app(app) # Initialize SQLAlchemy
bcrypt.init_app(app) # Initialize Bcrypt
migrate = Migrate(app, db) # Handles database migrations
csrf = CSRFProtect(app)    # Adds Cross-Site Request Forgery protection

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app) # Initialize Flask-Login
login_manager.login_view = 'login' # The route name for the login page

# User loader function required by Flask-Login
@login_manager.user_loader
def user_loader(user_id):
    # Fetches the user object from the database based on their ID
    # Uses db.session.get() which is the recommended way to get by primary key
    return db.session.get(User, user_id)

# --- Route Registration ---
# Import and register all application routes defined in routes.py
register_routes(app)

# --- Development Server Runner ---
# This block runs only when the script is executed directly (e.g., python app.py)
if __name__ == "__main__":
    # Runs the built-in Flask development server
    # Note: For production, use a WSGI server like Gunicorn or uWSGI
    app.run(host='0.0.0.0', port=5000)