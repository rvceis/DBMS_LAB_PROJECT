from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import MetadataRecord, SchemaModel, SchemaField, FieldValue
from ..extensions import db
from ..services.schema_matcher import find_best_schema_from_keys, create_schema_from_metadata
from ..services.schema_manager import SchemaManager
from ..services.metadata_catalog import MetadataCatalog

metadata_bp = Blueprint("metadata", __name__)


@metadata_bp.route("/", methods=["GET"])
@metadata_bp.route("/", methods=["POST"])
@jwt_required()
def create_metadata():
    from flask_jwt_extended import get_jwt
    import json, io, csv, werkzeug
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403

    # Accept both JSON and multipart/form-data
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        data = request.form.to_dict()
        file = request.files.get("file")
    else:
        data = request.get_json() or {}
        file = None

    values = data.get("values")
    asset_type_id = data.get("asset_type_id")
    tag = data.get("tag")
    name = data.get("name", "Unnamed Record")
    schema_id = data.get("schema_id")
    create_new_schema = data.get("create_new_schema", False)
    allow_additional = data.get("allow_additional_fields", True)
    metadata_json = data.get("metadata_json")
    raw_data = data.get("raw_data")
    input_format = (data.get("format") or "json").lower()

    # If values not provided but legacy metadata_json exists
    if not values and isinstance(metadata_json, dict):
        values = metadata_json

    # If values missing but raw_data is provided, try to parse based on format
    if (not isinstance(values, dict) or not values) and raw_data:
        try:
            if input_format == 'json':
                parsed = json.loads(raw_data)
                if isinstance(parsed, dict):
                    values = parsed
                elif isinstance(parsed, list) and parsed:
                    values = parsed[0]
                else:
                    return jsonify({"error": "raw_data JSON must be an object or non-empty array"}), 400
            elif input_format == 'ndjson':
                for line in raw_data.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    values = json.loads(line)
                    break
                if not values:
                    return jsonify({"error": "No JSON objects found in NDJSON raw_data"}), 400
            elif input_format in ('csv', 'tsv'):
                sep = ',' if input_format == 'csv' else '\t'
                f = io.StringIO(raw_data)
                reader = csv.reader(f, delimiter=sep)
                rows = [r for r in reader if any(cell.strip() for cell in r)]
                if len(rows) < 2:
                    return jsonify({"error": "CSV/TSV raw_data must include header and at least one row"}), 400
                headers = [h.strip() for h in rows[0]]
                first = rows[1]
                values = {headers[i]: first[i] if i < len(first) else None for i in range(len(headers))}
            else:
                values = None
        except Exception as e:
            return jsonify({"error": f"Failed to parse raw_data: {str(e)}"}), 400

    # If file is uploaded, save it and set file_path
    file_path = None
    if file and isinstance(file, werkzeug.datastructures.FileStorage):
        upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        safe_name = werkzeug.utils.secure_filename(file.filename)
        file_path = os.path.join(upload_dir, safe_name)
        file.save(file_path)

    # Allow record creation if any of: values is a dict, file is uploaded, or raw_data is present
    if not (isinstance(values, dict) and values) and not file_path and not raw_data:
        return jsonify({"error": "values (field map), raw_data, or file upload required"}), 400

    # Resolve schema
    schema: SchemaModel = None
    if schema_id:
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            return jsonify({"error": "schema not found"}), 400
    else:
        keys = list(values.keys()) if values else []
        schema, score = find_best_schema_from_keys(keys, asset_type_id=asset_type_id)
        if not schema:
            if not create_new_schema:
                return jsonify({"error": "no matching schema found; set create_new_schema=true to auto-create"}), 400
            schema = create_schema_from_metadata(
                name=f"AutoSchema-{name}",
                metadata=values or {},
                asset_type_id=asset_type_id,
                user_id=user_id,
                allow_additional_fields=allow_additional,
            )

    # Validate values against schema if present
    if values and schema:
        from ..services.validation_engine import ValidationEngine
        validator = ValidationEngine()
        validation_errors = validator.validate_record_values(schema, values)
        if validation_errors:
            return jsonify({
                "error": "Validation failed",
                "validation_errors": validation_errors
            }), 400

    import json as _json
    r = MetadataRecord(
        name=name,
        schema_id=schema.id,
        asset_type_id=asset_type_id,
        tag=tag,
        created_by=user_id,
        metadata_json=metadata_json,
        raw_data=raw_data if raw_data is not None else (_json.dumps(values) if isinstance(values, dict) else None),
        file_path=file_path
    )
    db.session.add(r)
    db.session.flush()

    # Persist field values if values present
    if values:
        fields = {f.field_name: f for f in SchemaField.query.filter_by(schema_id=schema.id, is_deleted=False).all()}
        for k, v in values.items():
            if k not in fields:
                if schema.allow_additional_fields:
                    continue
                else:
                    db.session.rollback()
                    return jsonify({"error": f"field '{k}' not defined in schema"}), 400
            f = fields[k]
            fv = FieldValue(record_id=r.id, schema_field_id=f.id)
            f_type_backup = f.field_type
            try:
                fv.schema_field = f
                fv.set_value(v)
            finally:
                f.field_type = f_type_backup
            db.session.add(fv)

    db.session.commit()
    return jsonify(r.to_dict(include_values=True)), 201
    
    # Validate values against schema
    from ..services.validation_engine import ValidationEngine
    validator = ValidationEngine()
    validation_errors = validator.validate_record_values(schema, values)
    
    if validation_errors:
        return jsonify({
            "error": "Validation failed",
            "validation_errors": validation_errors
        }), 400

    # Create metadata record - store raw_data for full fidelity if provided
    import json as _json
    r = MetadataRecord(
        name=name,
        schema_id=schema.id,
        asset_type_id=asset_type_id,
        tag=tag,
        created_by=user_id,
        metadata_json=metadata_json,  # optional legacy storage
        raw_data=raw_data if raw_data is not None else (_json.dumps(values) if isinstance(values, dict) else None)
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


@metadata_bp.route("/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_metadata_record(record_id):
    from ..models import User
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return {"error": "Admin privileges required"}, 403

    record = MetadataRecord.query.get(record_id)
    if not record:
        return {"error": "Record not found"}, 404

    db.session.delete(record)
    db.session.commit()
    return {"success": True}
