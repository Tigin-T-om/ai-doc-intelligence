# backend/auth_service.py
from passlib.context import CryptContext
from backend.db.db_handler import get_user_by_username, add_user, get_session
from backend.db.db_handler import get_session as _get_session

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def register_user(username: str, password: str):
    hashed = hash_password(password)
    # use session context
    with get_session() as db:
        return add_user(db, username, hashed)

def authenticate_user(username: str, password: str):
    with get_session() as db:
        user = get_user_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
