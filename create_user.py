# --- 1. IMPORTS ---
from getpass import getpass
from app import app, db, User 

# --- 2. MAIN SCRIPT LOGIC ---
def main():
    """Main function to handle the user creation process."""
    with app.app_context():
        print("--- Create a New User ---")

        # --- Get User Input ---
        email = input("Enter user's Email: ")
        name = input("Enter user's Name: ").strip()
        password = getpass(prompt="Enter user's Password: ")

        # --- Validate Input ---
        if not email or not password:
            print("Error: Email and password cannot be empty.")
            return

        if not name:
            name = "user"
            print("Name was empty, setting to 'user'.")

        # --- Check for Existing User ---
        if User.query.filter_by(email=email).first():
            print(f"Error: The email '{email}' is already in use.")
            return

        # --- Create and Save New User ---
        try:
            new_user = User(email=email, password=password, name=name)
            db.session.add(new_user)
            db.session.commit()
            print(f"User '{name}' with email '{email}' was added successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred while creating the user: {e}")

# --- 3. SCRIPT EXECUTION ---
if __name__ == "__main__":
    main()