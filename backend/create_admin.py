# backend/create_admin.py

import sys
import os
from getpass import getpass

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.db_handler import get_session
from backend.db.models import User # Import User model
from backend.auth_service import hash_password # Import hash function

def setup_admin():
    """
    A command-line script to create the first admin user,
    including first name, last name, and email.
    """
    print("--- Create Admin User ---")

    # Get user input from the terminal
    username = input("Enter admin username: ").strip()
    password = getpass("Enter admin password: ")
    password_confirm = getpass("Confirm admin password: ")

    # --- ADDED: Get new fields ---
    first_name = input("Enter admin first name: ").strip()
    last_name = input("Enter admin last name: ").strip()
    email = input("Enter admin email address: ").strip()
    # -----------------------------

    if password != password_confirm:
        print("❌ Passwords do not match. Aborting.")
        return

    # --- ADDED: Check new fields ---
    if not all([username, password, first_name, last_name, email]):
        print("❌ All fields (username, password, first name, last name, email) are required. Aborting.")
        return
    # -----------------------------

    # Use the database session
    with get_session() as db:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"⚠️ Username '{username}' already exists. Aborting.")
            return

        # --- ADDED: Check if email already exists ---
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
             print(f"⚠️ Email '{email}' is already registered. Aborting.")
             return
        # --------------------------------------------

        # Hash the password
        hashed = hash_password(password)

        # Create the new user object with the 'admin' role and new fields
        admin_user = User(
            username=username,
            hashed_password=hashed,
            role="admin", # Set the role specifically to admin
            # --- ADDED: Pass new fields ---
            first_name=first_name,
            last_name=last_name,
            email=email
            # -----------------------------
        )

        db.add(admin_user)
        try:
            db.commit() # Commit the changes to the database
            print(f"✅ Admin user '{username}' created successfully!")
        except Exception as e:
             db.rollback() # Rollback in case of error during commit
             print(f"❌ Error creating admin user: {e}")


if __name__ == "__main__":
    setup_admin()