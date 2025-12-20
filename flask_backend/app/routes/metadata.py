from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import MetadataRecord, SchemaModel, SchemaField, FieldValue
from ..extensions import db
from ..services.schema_matcher import find_best_schema_from_keys, create_schema_from_metadata
from ..services.schema_manager import SchemaManager
from ..services.metadata_catalog import MetadataCatalog

metadata_bp = Blueprint("metadata", __name__)


@metadata_bp.route("/", methods=["GET"])
@jwt_required()
def list_metadata():
    from ..models import AssetType, User
    
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "user not found"}), 404
    
    # Admin sees all records, others see only their own
    asset_type = request.args.get("asset_type")
    q = MetadataRecord.query
    
    if user.role != "admin":
        q = q.filter(MetadataRecord.created_by == user_id)
    
    if asset_type:
        q = q.filter(MetadataRecord.asset_type_id == asset_type)
    
    items = q.order_by(MetadataRecord.created_at.desc()).limit(100).all()
    result = []
    for r in items:
        asset_type_name = None
        creator_name = None
        if r.asset_type_id:
            at = AssetType.query.get(r.asset_type_id)
            asset_type_name = at.name if at else f"AssetType #{r.asset_type_id}"
        if r.created_by:
            creator = User.query.get(r.created_by)
            creator_name = creator.username if creator else f"User #{r.created_by}"
        d = r.to_dict(include_values=True)
        d.update({
            "asset_type_name": asset_type_name,
            "created_by_name": creator_name,
        })
        result.append(d)
    return jsonify(result)


@metadata_bp.route("/suggest-schemas", methods=["POST"])
@jwt_required()
def suggest_schemas():
    """Get all schemas ranked by match score for the given metadata/values."""
    catalog = MetadataCatalog()
    data = request.get_json() or {}
    metadata_json = data.get("metadata_json")
    values = data.get("values")  # New dynamic form: dict of field_name -> value
    asset_type_id = data.get("asset_type_id")
    
    # Determine keys to match on
    incoming_keys = []
    if isinstance(values, dict):
        incoming_keys = list(values.keys())
    elif isinstance(metadata_json, dict):
        incoming_keys = list(metadata_json.keys())
    
    if not incoming_keys:
        return jsonify({"error": "values or metadata_json required"}), 400
    
    # Get candidate schemas (optionally filter by asset type)
    q = SchemaModel.query
    if asset_type_id:
        q = q.filter(SchemaModel.asset_type_id == asset_type_id)
    schemas = q.all()
    
    # Score by overlapping field names
    def score_schema(s: SchemaModel) -> float:
        field_names = {f.field_name for f in s.fields if not f.is_deleted}
        common = field_names.intersection(incoming_keys)
        return len(common) / len(incoming_keys) if incoming_keys else 0.0
    
    ranked_schemas = [
        {
            "id": s.id,
            "name": s.name,
            "version": s.version,
            "asset_type_id": s.asset_type_id,
            "fields": [f.field_name for f in s.fields if not f.is_deleted],
            "match_score": round(score_schema(s) * 100, 1)
        }
        for s in schemas
    ]
    ranked_schemas.sort(key=lambda x: x["match_score"], reverse=True)
    
    return jsonify({
        "suggested_schemas": ranked_schemas,
        "incoming_keys": incoming_keys,
    })


@metadata_bp.route("/", methods=["POST"])
@jwt_required()
def create_metadata():
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403

    data = request.get_json() or {}
    # New preferred input
    values = data.get("values")  # dict of field_name -> value
    asset_type_id = data.get("asset_type_id")
    tag = data.get("tag")
    name = data.get("name", "Unnamed Record")
    schema_id = data.get("schema_id")
    create_new_schema = data.get("create_new_schema", False)
    allow_additional = data.get("allow_additional_fields", True)

    # Backward compatibility
    metadata_json = data.get("metadata_json")
    if not values and isinstance(metadata_json, dict):
        values = metadata_json

    if not isinstance(values, dict) or not values:
        return jsonify({"error": "values (field map) required"}), 400

    # Resolve schema
    schema: SchemaModel = None
    if schema_id:
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            return jsonify({"error": "schema not found"}), 400
    else:
        # Try to find best schema based on keys
        keys = list(values.keys())
        schema, score = find_best_schema_from_keys(keys, asset_type_id=asset_type_id)
        if not schema:
            if not asset_type_id:
                return jsonify({"error": "asset_type_id required to create new schema"}), 400
            if not create_new_schema:
                return jsonify({"error": "no matching schema found; set create_new_schema=true to auto-create"}), 400
            # Auto-create schema from incoming values
            schema = create_schema_from_metadata(
                name=f"AutoSchema-{name}",
                metadata=values,
                asset_type_id=asset_type_id,
                user_id=user_id,
                allow_additional_fields=allow_additional,
            )

    # Create metadata record
    r = MetadataRecord(
        name=name,
        schema_id=schema.id,
        asset_type_id=asset_type_id,
        tag=tag,
        created_by=user_id,
        metadata_json=metadata_json  # optional legacy storage
    )
    db.session.add(r)
    db.session.flush()

    # Persist field values
    # Build mapping of field_name -> SchemaField
    fields = {f.field_name: f for f in SchemaField.query.filter_by(schema_id=schema.id, is_deleted=False).all()}
    for k, v in values.items():
        if k not in fields:
            if schema.allow_additional_fields:
                # Skip unknown fields (or could add as new field via manager)
                continue
            else:
                db.session.rollback()
                return jsonify({"error": f"field '{k}' not defined in schema"}), 400
        f = fields[k]
        fv = FieldValue(record_id=r.id, schema_field_id=f.id)
        # Temporarily set field type for set_value convenience
        f_type_backup = f.field_type
        try:
            fv.schema_field = f
            fv.set_value(v)
        finally:
            f.field_type = f_type_backup
        db.session.add(fv)

    db.session.commit()
    return jsonify(r.to_dict(include_values=True)), 201


@metadata_bp.route("/<int:record_id>", methods=["GET"])
@jwt_required()
def get_metadata(record_id):
    from ..models import User
    
    user_id = int(get_jwt_identity())
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    # Users can only see their own records, admins see all
    if user.role != "admin" and r.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    return jsonify(r.to_dict(include_values=True))


@metadata_bp.route("/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_metadata(record_id):
    from flask_jwt_extended import get_jwt, get_jwt_identity
    from ..models import User
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    # Users can only edit their own records, admins can edit all
    if user.role != "admin" and r.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    data = request.get_json() or {}
    if "name" in data:
        r.name = data["name"]
    # Update dynamic values if provided
    values = data.get("values")
    if isinstance(values, dict):
        fields = {f.field_name: f for f in SchemaField.query.filter_by(schema_id=r.schema_id, is_deleted=False).all()}
        for k, v in values.items():
            if k not in fields:
                if r.schema.allow_additional_fields:
                    continue
                else:
                    return jsonify({"error": f"field '{k}' not defined in schema"}), 400
            f = fields[k]
            fv = FieldValue.query.filter_by(record_id=r.id, schema_field_id=f.id).first()
            if not fv:
                fv = FieldValue(record_id=r.id, schema_field_id=f.id)
                db.session.add(fv)
            # For set_value convenience
            f_type_backup = f.field_type
            try:
                fv.schema_field = f
                fv.set_value(v)
            finally:
                f.field_type = f_type_backup
    if "tag" in data:
        r.tag = data["tag"]
    if "schema_id" in data:
        r.schema_id = data["schema_id"]
    if "asset_type_id" in data:
        r.asset_type_id = data["asset_type_id"]
    db.session.commit()
    return jsonify(r.to_dict(include_values=True))


@metadata_bp.route("/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_metadata(record_id):
    from flask_jwt_extended import get_jwt, get_jwt_identity
    from ..models import User
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    # Users can delete their own records, only admins can delete others
    if role != "admin" and r.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "deleted"})
