# backend/db/init_db.py
from backend.db.db_handler import create_tables

def create():
    print("Creating database tables (including users)...")
    create_tables()
    print("Tables created successfully!")

if __name__ == "__main__":
    create()
