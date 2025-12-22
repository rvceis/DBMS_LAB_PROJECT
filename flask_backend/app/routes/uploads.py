"""
Data Upload/Import Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import SchemaModel, MetadataRecord
from ..extensions import db
from ..services.data_import_service import DataImportService
from ..services.metadata_service import MetadataService

uploads_bp = Blueprint('uploads', __name__)
import_service = DataImportService()
metadata_service = MetadataService()


@uploads_bp.route('/parse', methods=['POST'])
@jwt_required()
def parse_data():
    """
    Parse raw data and return preview
    
    Body: {
        "content": "raw data string",
        "schema_id": 1,
        "format": "auto" (or "json", "csv", "tsv", etc.)
    }
    """
    data = request.get_json()
    content = data.get('content')
    schema_id = data.get('schema_id')
    format_hint = data.get('format', 'auto')
    
    if not content:
        return jsonify({'error': 'content is required'}), 400
    if not schema_id:
        return jsonify({'error': 'schema_id is required'}), 400
    
    # Get schema
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({'error': 'Schema not found'}), 404
    
    schema_fields = [f.field_name for f in schema.fields if not f.is_deleted]
    
    try:
        # Parse data
        if format_hint == 'auto':
            detected_format, parsed_data = import_service.auto_parse(content, schema_fields)
        elif format_hint == 'json':
            parsed_data = import_service.parse_json(content)
            detected_format = 'json'
        elif format_hint in ['csv', 'tsv', 'pipe', 'semicolon']:
            delimiter = ',' if format_hint == 'csv' else format_hint
            parsed_data = import_service.parse_csv(content, delimiter)
            detected_format = format_hint
        elif format_hint == 'keyvalue':
            parsed_data = import_service.parse_keyvalue(content)
            detected_format = 'keyvalue'
        else:
            parsed_data = import_service.parse_plain_text(content, schema_fields)
            detected_format = 'plain'
        
        # Suggest field mapping
        schema_field_defs = [
            {'field_name': f.field_name, 'field_type': f.field_type, 'is_required': f.is_required}
            for f in schema.fields if not f.is_deleted
        ]
        mapping = import_service.suggest_field_mapping(parsed_data, schema_field_defs)
        
        return jsonify({
            'format_detected': detected_format,
            'record_count': len(parsed_data),
            'preview': parsed_data[:10],  # First 10 records
            'suggested_mapping': mapping,
            'data_fields': list(parsed_data[0].keys()) if parsed_data else [],
            'schema_fields': schema_fields,
        })
    except Exception as e:
        return jsonify({'error': f'Parse error: {str(e)}'}), 400


@uploads_bp.route('/import', methods=['POST'])
@jwt_required()
def import_data():
    """
    Import parsed data into metadata records
    
    Body: {
        "content": "raw data",
        "schema_id": 1,
        "format": "auto",
        "field_mapping": {"data_field": "schema_field", ...},
        "skip_validation": false
    }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    content = data.get('content')
    schema_id = data.get('schema_id')
    format_hint = data.get('format', 'auto')
    field_mapping = data.get('field_mapping', {})
    skip_validation = data.get('skip_validation', False)
    
    if not content:
        return jsonify({'error': 'content is required'}), 400
    if not schema_id:
        return jsonify({'error': 'schema_id is required'}), 400
    
    # Get schema
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({'error': 'Schema not found'}), 404
    
    schema_fields = [f.field_name for f in schema.fields if not f.is_deleted]
    
    try:
        # Parse data
        if format_hint == 'auto':
            detected_format, parsed_data = import_service.auto_parse(content, schema_fields)
        elif format_hint == 'json':
            parsed_data = import_service.parse_json(content)
            detected_format = 'json'
        elif format_hint in ['csv', 'tsv', 'pipe', 'semicolon']:
            delimiter = ',' if format_hint == 'csv' else format_hint
            parsed_data = import_service.parse_csv(content, delimiter)
            detected_format = format_hint
        elif format_hint == 'keyvalue':
            parsed_data = import_service.parse_keyvalue(content)
            detected_format = 'keyvalue'
        else:
            parsed_data = import_service.parse_plain_text(content, schema_fields)
            detected_format = 'plain'
        
        # Apply field mapping
        if field_mapping:
            mapped_data = []
            for record in parsed_data:
                mapped_record = {}
                for data_field, value in record.items():
                    schema_field = field_mapping.get(data_field, data_field)
                    mapped_record[schema_field] = value
                mapped_data.append(mapped_record)
            parsed_data = mapped_data
        
        # Validate against schema
        schema_field_defs = [
            {'field_name': f.field_name, 'field_type': f.field_type, 'is_required': f.is_required}
            for f in schema.fields if not f.is_deleted
        ]
        
        if not skip_validation:
            valid_records, errors = import_service.validate_against_schema(parsed_data, schema_field_defs)
            if errors:
                return jsonify({
                    'error': 'Validation failed',
                    'validation_errors': errors,
                    'valid_count': len(valid_records),
                    'invalid_count': len(errors),
                }), 400
        else:
            valid_records = parsed_data
        
        # Create metadata records
        created_records = []
        failed_records = []
        
        for idx, record_data in enumerate(valid_records):
            try:
                # Create metadata record
                record = metadata_service.create_record(
                    schema_id=schema_id,
                    name=record_data.get('name', f'Imported Record {idx + 1}'),
                    field_values=record_data,
                    created_by=user_id
                )
                created_records.append(record.id)
            except Exception as e:
                failed_records.append({'index': idx, 'error': str(e)})
        
        return jsonify({
            'success': True,
            'format_detected': detected_format,
            'total_records': len(parsed_data),
            'created_count': len(created_records),
            'failed_count': len(failed_records),
            'created_ids': created_records,
            'failures': failed_records,
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Import error: {str(e)}'}), 500


@uploads_bp.route('/file', methods=['POST'])
@jwt_required()
def upload_file():
    """
    Upload a file (CSV, JSON, TXT) and parse
    
    Form data:
        - file: uploaded file
        - schema_id: target schema
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    schema_id = request.form.get('schema_id')
    
    if not schema_id:
        return jsonify({'error': 'schema_id is required'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get schema
    schema = SchemaModel.query.get(int(schema_id))
    if not schema:
        return jsonify({'error': 'Schema not found'}), 404
    
    try:
        # Read file content
        content = file.read().decode('utf-8-sig')  # Handle BOM
        
        # Detect format from extension
        filename = file.filename.lower()
        if filename.endswith('.json'):
            format_hint = 'json'
        elif filename.endswith('.csv'):
            format_hint = 'csv'
        elif filename.endswith('.tsv') or filename.endswith('.txt'):
            format_hint = 'tsv'
        else:
            format_hint = 'auto'
        
        schema_fields = [f.field_name for f in schema.fields if not f.is_deleted]
        
        # Parse
        if format_hint == 'auto':
            detected_format, parsed_data = import_service.auto_parse(content, schema_fields)
        elif format_hint == 'json':
            parsed_data = import_service.parse_json(content)
            detected_format = 'json'
        elif format_hint in ['csv', 'tsv']:
            delimiter = ',' if format_hint == 'csv' else '\t'
            parsed_data = import_service.parse_csv(content, delimiter)
            detected_format = format_hint
        else:
            parsed_data = import_service.parse_plain_text(content, schema_fields)
            detected_format = 'plain'
        
        # Suggest mapping
        schema_field_defs = [
            {'field_name': f.field_name, 'field_type': f.field_type, 'is_required': f.is_required}
            for f in schema.fields if not f.is_deleted
        ]
        mapping = import_service.suggest_field_mapping(parsed_data, schema_field_defs)
        
        return jsonify({
            'filename': file.filename,
            'format_detected': detected_format,
            'record_count': len(parsed_data),
            'preview': parsed_data[:10],
            'suggested_mapping': mapping,
            'data_fields': list(parsed_data[0].keys()) if parsed_data else [],
            'schema_fields': schema_fields,
        })
        
    except Exception as e:
        return jsonify({'error': f'File processing error: {str(e)}'}), 500

