"""
Reports API Routes
"""
import os
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..models import ReportTemplate, ReportExecution, User, SchemaModel
from ..extensions import db
from ..services.report_generator import ReportGenerator

reports_bp = Blueprint('reports', __name__)

# Initialize report generator
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'reports')
report_gen = ReportGenerator(REPORTS_DIR)


@reports_bp.route('/templates', methods=['GET'])
@jwt_required()
def list_templates():
    """List available report templates"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Filter by access control
    if user.role == 'admin':
        templates = ReportTemplate.query.all()
    else:
        templates = ReportTemplate.query.filter(
            db.or_(
                ReportTemplate.created_by == user_id,
                ReportTemplate.is_public == True
            )
        ).all()
    
    return jsonify([t.to_dict() for t in templates])


@reports_bp.route('/templates/<int:template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """Get template details"""
    template = ReportTemplate.query.get_or_404(template_id)
    return jsonify(template.to_dict(include_config=True))


@reports_bp.route('/templates', methods=['POST'])
@jwt_required()
def create_template():
    """Create a new report template"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role', 'viewer')
    
    if role not in ('admin', 'editor'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    if not data.get('schema_id'):
        return jsonify({'error': 'schema_id is required'}), 400
    
    # Verify schema exists
    schema = SchemaModel.query.get(data['schema_id'])
    if not schema:
        return jsonify({'error': 'Schema not found'}), 404
    
    template = ReportTemplate(
        name=data['name'],
        description=data.get('description'),
        schema_id=data['schema_id'],
        asset_type_id=data.get('asset_type_id'),
        query_config=data.get('query_config', {}),
        display_config=data.get('display_config', {}),
        pdf_config=data.get('pdf_config', {}),
        created_by=user_id,
        is_public=data.get('is_public', False)
    )
    
    db.session.add(template)
    db.session.commit()
    
    return jsonify(template.to_dict(include_config=True)), 201


@reports_bp.route('/templates/<int:template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """Update report template"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role', 'viewer')
    
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Check permissions
    if template.created_by != user_id and role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update allowed fields
    for key in ['name', 'description', 'query_config', 'display_config', 'pdf_config', 'is_public']:
        if key in data:
            setattr(template, key, data[key])
    
    db.session.commit()
    return jsonify(template.to_dict(include_config=True))


@reports_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """Delete report template"""
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role', 'viewer')
    
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Check permissions
    if template.created_by != user_id and role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(template)
    db.session.commit()
    
    return jsonify({'message': 'Template deleted'}), 200


@reports_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_report():
    """Generate a report from template"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    template_id = data.get('template_id')
    format_type = data.get('format', 'csv')
    params = data.get('params', {})
    
    if not template_id:
        return jsonify({'error': 'template_id is required'}), 400
    
    if format_type not in ['csv', 'pdf']:
        return jsonify({'error': 'format must be csv or pdf'}), 400
    
    # Verify template access
    template = ReportTemplate.query.get(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    user = User.query.get(user_id)
    if not template.is_public and template.created_by != user_id and user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        execution = report_gen.generate_report(template_id, format_type, user_id, params)
        return jsonify(execution.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/generate/adhoc', methods=['POST'])
@jwt_required()
def generate_adhoc_report():
    """Generate an ad-hoc report without template"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    schema_id = data.get('schema_id')
    query_config = data.get('query_config', {})
    format_type = data.get('format', 'csv')
    report_name = data.get('name', 'Ad-hoc Report')
    
    if not schema_id:
        return jsonify({'error': 'schema_id is required'}), 400
    
    if format_type not in ['csv', 'pdf']:
        return jsonify({'error': 'format must be csv or pdf'}), 400
    
    try:
        execution = report_gen.generate_adhoc_report(
            schema_id, query_config, format_type, user_id, report_name
        )
        return jsonify(execution.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/executions', methods=['GET'])
@jwt_required()
def list_executions():
    """List report execution history"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    limit = request.args.get('limit', 100, type=int)
    
    if user.role == 'admin':
        executions = ReportExecution.query.order_by(
            ReportExecution.started_at.desc()
        ).limit(limit).all()
    else:
        executions = ReportExecution.query.filter_by(
            user_id=user_id
        ).order_by(ReportExecution.started_at.desc()).limit(limit).all()
    
    return jsonify([e.to_dict() for e in executions])


@reports_bp.route('/executions/<int:execution_id>', methods=['GET'])
@jwt_required()
def get_execution(execution_id):
    """Get report execution details"""
    user_id = int(get_jwt_identity())
    execution = ReportExecution.query.get_or_404(execution_id)
    
    # Check permissions
    user = User.query.get(user_id)
    if execution.user_id != user_id and user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(execution.to_dict())


@reports_bp.route('/executions/<int:execution_id>/download', methods=['GET'])
@jwt_required()
def download_report(execution_id):
    """Download generated report file"""
    user_id = int(get_jwt_identity())
    execution = ReportExecution.query.get_or_404(execution_id)
    
    # Check permissions
    user = User.query.get(user_id)
    if execution.user_id != user_id and user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if execution.status != 'completed':
        return jsonify({'error': 'Report not ready yet'}), 400
    
    if not execution.file_path or not os.path.exists(execution.file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Determine mimetype
    mimetype = 'text/csv' if execution.format == 'csv' else 'application/pdf'
    
    return send_file(
        execution.file_path,
        as_attachment=True,
        download_name=os.path.basename(execution.file_path),
        mimetype=mimetype
    )


@reports_bp.route('/executions/<int:execution_id>', methods=['DELETE'])
@jwt_required()
def delete_execution(execution_id):
    """Delete execution record and file"""
    user_id = int(get_jwt_identity())
    execution = ReportExecution.query.get_or_404(execution_id)
    
    # Check permissions
    user = User.query.get(user_id)
    if execution.user_id != user_id and user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Delete file if exists
    if execution.file_path and os.path.exists(execution.file_path):
        try:
            os.remove(execution.file_path)
        except:
            pass
    
    db.session.delete(execution)
    db.session.commit()
    
    return jsonify({'message': 'Execution deleted'}), 200
