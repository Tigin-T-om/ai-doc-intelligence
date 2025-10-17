# backend/db/drop_db.py

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.db.db_handler import engine
from sqlalchemy import text

def drop_tables():
    print("Force dropping all tables with CASCADE...")
    try:
        with engine.connect() as conn:
            # Begin a transaction explicitly
            trans = conn.begin()
            try:
                conn.execute(text("DROP SCHEMA public CASCADE;"))
                conn.execute(text("CREATE SCHEMA public;"))
                # Commit the transaction to make the changes permanent
                trans.commit()
                print("All tables dropped and schema reset!")
            except Exception as e:
                print(f"Error during transaction: {e}")
                # Rollback if anything went wrong
                trans.rollback()
    except Exception as e:
        print(f"Error connecting to the database: {e}")

if __name__ == "__main__":
    drop_tables()