from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import AssetType
from ..extensions import db

asset_types_bp = Blueprint("asset_types", __name__)


@asset_types_bp.route("/", methods=["GET"])
def list_asset_types():
    types = AssetType.query.all()
    return jsonify([{"id": t.id, "name": t.name} for t in types])


@asset_types_bp.route("/", methods=["POST"])
@jwt_required()
def create_asset_type():
    try:
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        user_id = get_jwt_identity()
        print(f"User ID: {user_id}, Claims: {claims}")
        if claims.get("role") != "admin":
            return jsonify({"error": "admin required"}), 403
        data = request.get_json() or {}
        print(f"Request data: {data}")
        name = data.get("name")
        if not name:
            return jsonify({"error": "name required"}), 400
        if AssetType.query.filter_by(name=name).first():
            return jsonify({"error": "already exists"}), 400
        t = AssetType(name=name)
        db.session.add(t)
        db.session.commit()
        return jsonify({"id": t.id, "name": t.name}), 201
    except Exception as e:
        print(f"Error creating asset type: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@asset_types_bp.route("/<int:type_id>", methods=["PUT"])
@jwt_required()
def update_asset_type(type_id):
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "admin required"}), 403
    t = AssetType.query.get(type_id)
    if not t:
        return jsonify({"error": "not found"}), 404
    data = request.get_json() or {}
    name = data.get("name")
    if name:
        t.name = name
        db.session.commit()
    return jsonify({"id": t.id, "name": t.name})


@asset_types_bp.route("/<int:type_id>", methods=["DELETE"])
@jwt_required()
def delete_asset_type(type_id):
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "admin required"}), 403
    t = AssetType.query.get(type_id)
    if not t:
        return jsonify({"error": "not found"}), 404
    db.session.delete(t)
    db.session.commit()
    return jsonify({"message": "deleted"})
