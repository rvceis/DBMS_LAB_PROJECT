from werkzeug.security import generate_password_hash, check_password_hash
from ..models import User
from ..extensions import db


def create_user(username: str, email: str, password: str, role: str = "viewer") -> User:
    pw_hash = generate_password_hash(password)
    user = User(username=username, email=email, password_hash=pw_hash, role=role)
    db.session.add(user)
    db.session.commit()
    return user


def verify_password(user: User, password: str) -> bool:
    return check_password_hash(user.password_hash, password)


def get_user_by_email(email: str):
    return User.query.filter_by(email=email).first()
