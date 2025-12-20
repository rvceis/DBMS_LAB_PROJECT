from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User
from ..extensions import db

users_bp = Blueprint("users", __name__)


@users_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify(user.to_dict())


@users_bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "admin required"}), 403
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])
