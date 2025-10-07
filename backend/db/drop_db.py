# backend/db/drop_db.py

from backend.db.db_handler import engine
from sqlalchemy import text

def drop_tables():
    print("Force dropping all tables with CASCADE...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
    print("All tables dropped and schema reset!")

if __name__ == "__main__":
    drop_tables()
