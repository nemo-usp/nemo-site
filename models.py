from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
import uuid
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()

# --- User Model ---
# Represents a user account in the database.
# Inherits from db.Model for SQLAlchemy integration and UserMixin for Flask-Login compatibility.
class User(db.Model, UserMixin):
    __tablename__ = 'user' # Explicitly sets the table name

    # --- Columns ---
    # Primary key, using UUID4 for globally unique IDs.
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # User's email address, must be unique. Used for login.
    email = db.Column(db.String(128), unique=True, nullable=False)
    # User's display name (optional).
    name = db.Column(db.String(100), nullable=True)
    # Stores the hashed password using bcrypt.
    password_hash = db.Column(db.String(128))
    # A short bio or description for the user (optional).
    about_me = db.Column(db.Text, nullable=True)
    # Path to the user's profile picture. Defaults to a standard avatar.
    profile_image_path = db.Column(db.String(255), nullable=True, default='static/uploads/default_avatar.png')

    # --- Initialization ---
    # Constructor for creating a new User instance.
    # Hashes the provided password automatically.
    def __init__(self, email: str, password: str, name: str):
        self.email = email
        # Store the password hash as a UTF-8 decoded string
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.name = name

    # --- Methods ---
    # Checks if a given plain-text password matches the stored hash.
    # Returns True if the password is correct, False otherwise.
    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)
    
# --- Material Model ---
# Represents an item in the "Materials" accordion page
class Material(db.Model):
    __tablename__ = 'material'

    # --- Columns ---
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    pdf_path = db.Column(db.String(255), nullable=False) # Stores path like 'static/uploads/material.pdf'
    
    # This new column will control the sorting
    position = db.Column(db.Integer, default=0) 
    
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, title, description, pdf_path, position):
        self.title = title
        self.description = description
        self.pdf_path = pdf_path
        self.position = position