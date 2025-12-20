"""
Analytics and statistics endpoints
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, SchemaModel, MetadataRecord, AssetType, ChangeLog
from ..extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics for the current user"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Admin sees all, others see their own
    if user.role == 'admin':
        total_records = MetadataRecord.query.count()
        total_schemas = SchemaModel.query.count()
        total_users = User.query.count()
        user_records = MetadataRecord.query.all()
    else:
        total_records = MetadataRecord.query.filter_by(created_by=user_id).count()
        total_schemas = SchemaModel.query.count()  # Can see all schemas
        total_users = 1  # Only themselves
        user_records = MetadataRecord.query.filter_by(created_by=user_id).all()
    
    total_asset_types = AssetType.query.count()
    
    # Records created in last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_records = MetadataRecord.query.filter(
        MetadataRecord.created_at >= seven_days_ago
    ).count()
    
    return jsonify({
        "total_metadata_records": total_records,
        "total_schemas": total_schemas,
        "total_users": total_users,
        "total_asset_types": total_asset_types,
        "recent_records_7days": recent_records
    })


@analytics_bp.route("/metadata-by-asset-type", methods=["GET"])
@jwt_required()
def get_metadata_by_asset_type():
    """Get metadata count grouped by asset type"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    query = db.session.query(
        AssetType.name,
        func.count(MetadataRecord.id).label('count')
    ).outerjoin(MetadataRecord, AssetType.id == MetadataRecord.asset_type_id)
    
    if user.role != 'admin':
        query = query.filter(MetadataRecord.created_by == user_id)
    
    query = query.group_by(AssetType.name)
    
    result = [{"name": name or "Unassigned", "value": count} 
              for name, count in query.all()]
    
    return jsonify(result)


@analytics_bp.route("/metadata-timeline", methods=["GET"])
@jwt_required()
def get_metadata_timeline():
    """Get metadata creation over last 30 days"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    query = db.session.query(
        func.date(MetadataRecord.created_at).label('date'),
        func.count(MetadataRecord.id).label('count')
    ).filter(MetadataRecord.created_at >= thirty_days_ago)
    
    if user.role != 'admin':
        query = query.filter(MetadataRecord.created_by == user_id)
    
    query = query.group_by(func.date(MetadataRecord.created_at)).order_by('date')
    
    result = [{"date": date.isoformat(), "records": count} 
              for date, count in query.all()]
    
    return jsonify(result)


@analytics_bp.route("/recent-activity", methods=["GET"])
@jwt_required()
def get_recent_activity():
    """Get recent schema changes and activity"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Get recent change logs
    logs = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).limit(20).all()
    
    result = []
    for log in logs:
        changed_by_user = User.query.get(log.changed_by) if log.changed_by else None
        schema = SchemaModel.query.get(log.schema_id) if log.schema_id else None
        
        result.append({
            "id": log.id,
            "schema_id": log.schema_id,
            "schema_version": schema.version if schema else None,
            "change_type": log.change_type,
            "description": log.description,
            "changed_by": log.changed_by,
            "changed_by_name": changed_by_user.username if changed_by_user else "Unknown",
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        })
    
    return jsonify(result)


@analytics_bp.route("/top-asset-types", methods=["GET"])
@jwt_required()
def get_top_asset_types():
    """Get top 5 most used asset types"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    query = db.session.query(
        AssetType.name,
        func.count(MetadataRecord.id).label('count')
    ).outerjoin(MetadataRecord, AssetType.id == MetadataRecord.asset_type_id)
    
    if user.role != 'admin':
        query = query.filter(MetadataRecord.created_by == user_id)
    
    query = query.group_by(AssetType.name).order_by(
        func.count(MetadataRecord.id).desc()
    ).limit(5)
    
    result = [{"name": name or "Unassigned", "count": count} 
              for name, count in query.all()]
    
    return jsonify(result)


@analytics_bp.route("/user-activity", methods=["GET"])
@jwt_required()
def get_user_activity():
    """Get metadata count per user (admin only)"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({"error": "admin only"}), 403
    
    query = db.session.query(
        User.username,
        func.count(MetadataRecord.id).label('count')
    ).outerjoin(MetadataRecord, User.id == MetadataRecord.created_by).group_by(User.username)
    
    result = [{"username": username or "Unknown", "count": count} 
              for username, count in query.all()]
    
    return jsonify(result)
