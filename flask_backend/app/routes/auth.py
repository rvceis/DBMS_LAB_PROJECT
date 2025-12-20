from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "viewer")
    if not username or not email or not password:
        return jsonify({"error": "username, email and password required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 400
    user = User(username=username, email=email, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "email": user.email})
    return jsonify({"user": user.to_dict(), "access_token": token}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "email": user.email})
    return jsonify({"user": user.to_dict(), "access_token": token})
