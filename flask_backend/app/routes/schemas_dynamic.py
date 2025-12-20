"""
Dynamic Schema Routes - Enhanced endpoints for dynamic schema management
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..models import SchemaModel, SchemaField, AssetType
from ..extensions import db
from ..services.schema_manager import SchemaManager
from ..services.schema_version_control import SchemaVersionControl
from ..services.migration_generator import MigrationGenerator, ImpactAnalyzer
from ..services.metadata_catalog import MetadataCatalog

schemas_bp = Blueprint("schemas", __name__)

# Initialize services
schema_manager = SchemaManager()
version_control = SchemaVersionControl()
migration_gen = MigrationGenerator()
impact_analyzer = ImpactAnalyzer()
catalog = MetadataCatalog()


@schemas_bp.route("/", methods=["GET"])
def list_schemas():
    """List all schemas with optional filtering"""
    asset_type_id = request.args.get("asset_type_id", type=int)
    active_only = request.args.get("active_only", "true").lower() == "true"
    
    query = SchemaModel.query
    
    if asset_type_id:
        query = query.filter_by(asset_type_id=asset_type_id)
    if active_only:
        query = query.filter_by(is_active=True)
    
    schemas = query.order_by(SchemaModel.version.desc()).all()
    
    result = []
    for s in schemas:
        from ..models import User
        user_name = None
        if s.created_by:
            user = User.query.get(s.created_by)
            user_name = user.username if user else f"User #{s.created_by}"
        
        schema_dict = s.to_dict(include_fields=True)
        schema_dict["created_by_name"] = user_name
        
        # Add statistics
        schema_dict["statistics"] = catalog.get_schema_statistics(s.id)
        
        result.append(schema_dict)
    
    return jsonify(result)


@schemas_bp.route("/", methods=["POST"])
@jwt_required()
def create_schema():
    """Create a new dynamic schema"""
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    data = request.get_json() or {}
    
    # Required fields
    name = data.get("name")
    asset_type_id = data.get("asset_type_id")
    fields = data.get("fields", [])
    
    if not name or not asset_type_id or not fields:
        return jsonify({"error": "name, asset_type_id, and fields required"}), 400
    
    # Verify asset type exists
    asset_type = AssetType.query.get(asset_type_id)
    if not asset_type:
        return jsonify({"error": f"Asset type {asset_type_id} not found"}), 404
    
    # Optional fields
    allow_additional_fields = data.get("allow_additional_fields", True)
    parent_schema_id = data.get("parent_schema_id")
    
    try:
        schema = schema_manager.create_schema(
            name=name,
            asset_type_id=asset_type_id,
            fields=fields,
            user_id=user_id,
            allow_additional_fields=allow_additional_fields,
            parent_schema_id=parent_schema_id
        )
        
        return jsonify({
            "success": True,
            "schema": schema.to_dict(include_fields=True)
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create schema: {str(e)}"}), 500


@schemas_bp.route("/<int:schema_id>", methods=["GET"])
def get_schema(schema_id):
    """Get detailed schema information"""
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({"error": "Schema not found"}), 404
    
    schema_dict = schema.to_dict(include_fields=True)
    schema_dict["statistics"] = catalog.get_schema_statistics(schema_id)
    
    return jsonify(schema_dict)


@schemas_bp.route("/<int:schema_id>/fields", methods=["POST"])
@jwt_required()
def add_field(schema_id):
    """Add a new field to schema"""
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    data = request.get_json() or {}
    
    field_name = data.get("field_name")
    field_type = data.get("field_type", "string")
    
    if not field_name:
        return jsonify({"error": "field_name required"}), 400
    
    try:
        field = schema_manager.add_field(
            schema_id=schema_id,
            field_name=field_name,
            field_type=field_type,
            user_id=user_id,
            is_required=data.get("is_required", False),
            default_value=data.get("default_value"),
            constraints=data.get("constraints"),
            description=data.get("description")
        )
        
        return jsonify({
            "success": True,
            "field": field.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to add field: {str(e)}"}), 500


@schemas_bp.route("/<int:schema_id>/fields/<field_name>", methods=["DELETE"])
@jwt_required()
def remove_field(schema_id, field_name):
    """Remove a field from schema"""
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    permanent = request.args.get("permanent", "false").lower() == "true"
    
    try:
        success = schema_manager.remove_field(
            schema_id=schema_id,
            field_name=field_name,
            user_id=user_id,
            permanent=permanent
        )
        
        return jsonify({
            "success": success,
            "message": f"Field '{field_name}' removed"
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to remove field: {str(e)}"}), 500


@schemas_bp.route("/<int:schema_id>/fields/<field_name>", methods=["PUT"])
@jwt_required()
def modify_field(schema_id, field_name):
    """Modify field properties"""
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    data = request.get_json() or {}
    
    try:
        field = schema_manager.modify_field(
            schema_id=schema_id,
            field_name=field_name,
            user_id=user_id,
            new_type=data.get("type"),
            new_required=data.get("required"),
            new_constraints=data.get("constraints"),
            new_description=data.get("description")
        )
        
        return jsonify({
            "success": True,
            "field": field.to_dict()
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to modify field: {str(e)}"}), 500


@schemas_bp.route("/<int:schema_id>/fork", methods=["POST"])
@jwt_required()
def fork_schema(schema_id):
    """Fork (create variant of) an existing schema"""
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    data = request.get_json() or {}
    new_name = data.get("name")
    
    if not new_name:
        return jsonify({"error": "name required"}), 400
    
    try:
        new_schema = schema_manager.fork_schema(
            schema_id=schema_id,
            new_name=new_name,
            user_id=user_id,
            modifications=data.get("modifications")
        )
        
        return jsonify({
            "success": True,
            "schema": new_schema.to_dict(include_fields=True)
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to fork schema: {str(e)}"}), 500


# Version Control Endpoints

@schemas_bp.route("/<int:schema_id>/versions", methods=["GET"])
def list_versions(schema_id):
    """List all versions of a schema"""
    limit = request.args.get("limit", 50, type=int)
    versions = version_control.list_versions(schema_id, limit=limit)
    return jsonify(versions)


@schemas_bp.route("/<int:schema_id>/versions/<int:version_number>", methods=["GET"])
def get_version(schema_id, version_number):
    """Get a specific version"""
    version = version_control.get_version(schema_id, version_number)
    if not version:
        return jsonify({"error": "Version not found"}), 404
    return jsonify(version)


@schemas_bp.route("/<int:schema_id>/versions/compare", methods=["GET"])
def compare_versions(schema_id):
    """Compare two versions"""
    v1 = request.args.get("v1", type=int)
    v2 = request.args.get("v2", type=int)
    
    if not v1 or not v2:
        return jsonify({"error": "v1 and v2 query params required"}), 400
    
    try:
        diff = version_control.compare_versions(schema_id, v1, v2)
        return jsonify(diff)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@schemas_bp.route("/<int:schema_id>/rollback", methods=["POST"])
@jwt_required()
def rollback_schema(schema_id):
    """Rollback schema to a previous version"""
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role != "admin":
        return jsonify({"error": "admin required"}), 403
    
    data = request.get_json() or {}
    target_version = data.get("target_version")
    
    if not target_version:
        return jsonify({"error": "target_version required"}), 400
    
    preserve_data = data.get("preserve_data", True)
    
    try:
        result = version_control.rollback(
            schema_id=schema_id,
            target_version=target_version,
            user_id=user_id,
            preserve_data=preserve_data
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@schemas_bp.route("/<int:schema_id>/logs", methods=["GET"])
def get_schema_logs(schema_id):
    """Get change log history for schema"""
    limit = request.args.get("limit", 100, type=int)
    logs = version_control.get_change_history(schema_id, limit=limit)
    return jsonify(logs)


# Migration & Impact Analysis Endpoints

@schemas_bp.route("/<int:schema_id>/migration", methods=["POST"])
@jwt_required()
def generate_migration(schema_id):
    """Generate migration script"""
    data = request.get_json() or {}
    
    from_version = data.get("from_version")
    to_version = data.get("to_version")
    dialect = data.get("dialect", "postgresql")
    
    if not from_version or not to_version:
        return jsonify({"error": "from_version and to_version required"}), 400
    
    try:
        script = migration_gen.generate_migration(
            schema_id, from_version, to_version, dialect
        )
        
        return jsonify({
            "success": True,
            "script": script,
            "from_version": from_version,
            "to_version": to_version,
            "dialect": dialect
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@schemas_bp.route("/<int:schema_id>/ddl", methods=["GET"])
def get_schema_ddl(schema_id):
    """Get full DDL for current schema"""
    dialect = request.args.get("dialect", "postgresql")
    
    try:
        ddl = migration_gen.generate_full_schema_ddl(schema_id, dialect)
        return jsonify({"ddl": ddl})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@schemas_bp.route("/<int:schema_id>/impact/add-field", methods=["POST"])
@jwt_required()
def analyze_add_field_impact(schema_id):
    """Analyze impact of adding a field"""
    data = request.get_json() or {}
    field_def = data.get("field")
    
    if not field_def:
        return jsonify({"error": "field definition required"}), 400
    
    analysis = impact_analyzer.analyze_field_addition(schema_id, field_def)
    return jsonify(analysis)


@schemas_bp.route("/<int:schema_id>/impact/remove-field/<field_name>", methods=["GET"])
@jwt_required()
def analyze_remove_field_impact(schema_id, field_name):
    """Analyze impact of removing a field"""
    analysis = impact_analyzer.analyze_field_removal(schema_id, field_name)
    return jsonify(analysis)


@schemas_bp.route("/<int:schema_id>/impact/change-type/<field_name>", methods=["POST"])
@jwt_required()
def analyze_type_change_impact(schema_id, field_name):
    """Analyze impact of changing field type"""
    data = request.get_json() or {}
    new_type = data.get("new_type")
    
    if not new_type:
        return jsonify({"error": "new_type required"}), 400
    
    analysis = impact_analyzer.analyze_type_change(schema_id, field_name, new_type)
    return jsonify(analysis)


# Utility endpoints

@schemas_bp.route("/<int:schema_id>/statistics", methods=["GET"])
def get_statistics(schema_id):
    """Get usage statistics for schema"""
    stats = catalog.get_schema_statistics(schema_id)
    return jsonify(stats)


@schemas_bp.route("/<int:schema_id>/fields", methods=["GET"])
def get_fields(schema_id):
    """Get all fields for schema"""
    include_deleted = request.args.get("include_deleted", "false").lower() == "true"
    fields = catalog.get_fields(schema_id, include_deleted=include_deleted)
    return jsonify(fields)
