from backend.db.db_handler import SessionLocal, add_user, get_all_users

db = SessionLocal()
user = add_user(db, "testuser", "secret123")
print("Inserted user:", user.username)

users = get_all_users(db)
print("All users:", [u.username for u in users])
db.close()