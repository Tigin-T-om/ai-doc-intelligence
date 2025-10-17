# backend/verify_db_schema.py

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import inspect
from backend.db.db_handler import engine

def check_schema():
    """
    Connects to the database and inspects the 'users' table schema.
    """
    print("--- Verifying Database Schema ---")
    try:
        inspector = inspect(engine)
        if not inspector.has_table("users"):
            print("❌ ERROR: The 'users' table does not exist in the database.")
            return

        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]

        print(f"✅ Found table 'users' with columns: {column_names}")

        if 'role' in column_names:
            print("✅ SUCCESS: The 'role' column exists in the database.")
        else:
            print("❌ FAILURE: The 'role' column DOES NOT EXIST in the database.")

    except Exception as e:
        print(f"An error occurred while connecting to or inspecting the database: {e}")

if __name__ == "__main__":
    check_schema()