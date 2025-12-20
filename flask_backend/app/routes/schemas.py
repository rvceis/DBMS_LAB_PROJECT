from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import SchemaModel
from ..extensions import db

schemas_bp = Blueprint("schemas", __name__)


@schemas_bp.route("/", methods=["GET"])
def list_schemas():
    from ..models import User
    schemas = SchemaModel.query.order_by(SchemaModel.version.desc()).all()
    result = []
    for s in schemas:
        user_name = None
        if s.created_by:
            user = User.query.get(s.created_by)
            user_name = user.username if user else f"User #{s.created_by}"
        result.append({
            "id": s.id,
            "version": s.version,
            "schema_json": s.schema_json,
            "created_by": s.created_by,
            "created_by_name": user_name,
        })
    return jsonify(result)


@schemas_bp.route("/", methods=["POST"])
@jwt_required()
def create_schema():
    from flask_jwt_extended import get_jwt, get_jwt_identity
    from ..models import ChangeLog
    claims = get_jwt()
    user_id = get_jwt_identity()
    if claims.get("role") not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    data = request.get_json() or {}
    schema_json = data.get("schema_json")
    if not schema_json:
        return jsonify({"error": "schema_json required"}), 400
    # compute next version
    latest = SchemaModel.query.order_by(SchemaModel.version.desc()).first()
    version = (latest.version + 1) if latest else 1
    s = SchemaModel(version=version, schema_json=schema_json, created_by=int(user_id))
    db.session.add(s)
    db.session.flush()  # Get the schema ID before committing
    
    # Create change log entry
    log = ChangeLog(
        schema_id=s.id,
        change_type="created",
        description=f"Schema v{version} created",
        changed_by=int(user_id)
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"id": s.id, "version": s.version}), 201


@schemas_bp.route("/<int:schema_id>/logs", methods=["GET"])
def get_schema_logs(schema_id):
    """Get change log history for a specific schema"""
    from ..models import ChangeLog, User
    
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({"error": "schema not found"}), 404
    
    logs = ChangeLog.query.filter_by(schema_id=schema_id).order_by(ChangeLog.timestamp.desc()).all()
    result = []
    for log in logs:
        user_name = None
        if log.changed_by:
            user = User.query.get(log.changed_by)
            user_name = user.username if user else f"User #{log.changed_by}"
        result.append({
            "id": log.id,
            "change_type": log.change_type,
            "description": log.description,
            "changed_by": log.changed_by,
            "changed_by_name": user_name,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        })
    return jsonify(result)


@schemas_bp.route("/logs", methods=["GET"])
def get_all_logs():
    """Get all schema change logs (admin view)"""
    from ..models import ChangeLog, User
    
    logs = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).limit(100).all()
    result = []
    for log in logs:
        user_name = None
        if log.changed_by:
            user = User.query.get(log.changed_by)
            user_name = user.username if user else f"User #{log.changed_by}"
        
        schema = SchemaModel.query.get(log.schema_id) if log.schema_id else None
        result.append({
            "id": log.id,
            "schema_id": log.schema_id,
            "schema_version": schema.version if schema else None,
            "change_type": log.change_type,
            "description": log.description,
            "changed_by": log.changed_by,
            "changed_by_name": user_name,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        })
    return jsonify(result)
