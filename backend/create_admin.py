# backend/create_admin.py

import sys
import os
from getpass import getpass

# This is needed to import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.db_handler import get_session
from backend.db.models import User
from backend.auth_service import hash_password

def setup_admin():
    """
    A command-line script to create the first admin user.
    """
    print("--- Create Admin User ---")
    
    # Get user input from the terminal
    username = input("Enter admin username: ")
    password = getpass("Enter admin password: ")
    password_confirm = getpass("Confirm admin password: ")

    if password != password_confirm:
        print("❌ Passwords do not match. Aborting.")
        return

    if not username or not password:
        print("❌ Username and password cannot be empty. Aborting.")
        return

    # Use the database session
    with get_session() as db:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"⚠️ User '{username}' already exists. Aborting.")
            return

        # Hash the password
        hashed = hash_password(password)

        # Create the new user object with the 'admin' role
        admin_user = User(
            username=username,
            hashed_password=hashed,
            role="admin"  # Set the role specifically to admin
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"✅ Admin user '{username}' created successfully!")


if __name__ == "__main__":
    setup_admin()