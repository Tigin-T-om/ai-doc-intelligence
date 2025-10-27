# backend/auth_service.py
from passlib.context import CryptContext
# Make sure get_user_by_email is imported if needed for checks here,
# although the main check is now in db_handler.add_user
from backend.db.db_handler import get_user_by_username, add_user, get_session

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

# --- UPDATED: Function Signature ---
def register_user(username: str, password: str, first_name: str, last_name: str, email: str):
# -----------------------------------
    hashed = hash_password(password)
    # Use session context
    with get_session() as db:
        # --- UPDATED: Call to add_user ---
        # Pass the new arguments
        return add_user(
            db=db,
            username=username,
            hashed_password=hashed,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        # ---------------------------------

def authenticate_user(username: str, password: str):
    with get_session() as db:
        user = get_user_by_username(db, username)
        if not user:
            return None
        # Verify password using the plain password and the stored hash
        if not verify_password(password, user.hashed_password):
            return None
        # Return the user object if authentication succeeds
        return user