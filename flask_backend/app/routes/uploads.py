"""
Data Upload/Import Routes
"""
import os
import tempfile
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import SchemaModel, SchemaField, MetadataRecord, FieldValue
from ..extensions import db
from ..services.data_import_service import DataImportService
from ..services.metadata_extractor import MetadataExtractor

uploads_bp = Blueprint('uploads', __name__)
import_service = DataImportService()
extractor_service = MetadataExtractor()


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
                # Create metadata record (store data in metadata_json)
                record = MetadataRecord(
                    name=record_data.get('name', f'Imported Record {idx + 1}'),
                    schema_id=schema_id,
                    asset_type_id=schema.asset_type_id,
                    created_by=user_id,
                    metadata_json=record_data
                )
                db.session.add(record)
                db.session.commit()
                created_records.append(record.id)
            except Exception as e:
                db.session.rollback()
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


@uploads_bp.route('/extract-metadata', methods=['POST'])
@jwt_required()
def extract_metadata():
    """
    Extract metadata from any file type and auto-generate schema
    
    Form data:
        - file: uploaded file (image, video, JSON, CSV, PDF, etc.)
        - asset_type_id: asset type for the schema
    
    Returns:
        - metadata: extracted metadata
        - suggested_schema: auto-generated schema with fields
    """
    user_id = int(get_jwt_identity())
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    asset_type_id = request.form.get('asset_type_id')
    
    if not asset_type_id:
        return jsonify({'error': 'asset_type_id is required'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Save temp file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        # Extract metadata
        metadata, fields = extractor_service.extract(temp_path, file.filename)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'metadata': metadata,
            'suggested_fields': fields,
            'schema_name': file.filename.split('.')[0].title(),
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Metadata extraction error: {str(e)}'}), 500


@uploads_bp.route('/create-schema-from-metadata', methods=['POST'])
@jwt_required()
def create_schema_from_metadata():
    """
    Create schema from extracted metadata and optionally create metadata record
    
    Body: {
        "asset_type_id": 1,
        "schema_name": "Image Metadata",
        "fields": [...],
        "metadata": {...},
        "create_record": true
    }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    asset_type_id = data.get('asset_type_id')
    schema_name = data.get('schema_name')
    fields = data.get('fields', [])
    metadata = data.get('metadata', {})
    create_record = data.get('create_record', False)
    
    if not asset_type_id or not schema_name or not fields:
        return jsonify({'error': 'asset_type_id, schema_name, and fields are required'}), 400
    
    try:
        # Create schema
        schema = SchemaModel(
            name=schema_name,
            version=1,
            asset_type_id=int(asset_type_id),
            schema_json={},
            created_by=user_id
        )
        db.session.add(schema)
        db.session.flush()  # Flush to get schema ID
        
        # Create fields
        for idx, field_def in enumerate(fields):
            field = SchemaField(
                schema_id=schema.id,
                field_name=field_def.get('field_name'),
                field_type=field_def.get('field_type', 'string'),
                is_required=field_def.get('is_required', False),
                description='Auto-extracted from file',
                order_index=idx
            )
            db.session.add(field)

        db.session.commit()
        
        # Optionally create metadata record
        record_id = None
        if create_record and metadata:
            try:
                record = MetadataRecord(
                    name=metadata.get('filename', 'Imported File'),
                    schema_id=schema.id,
                    asset_type_id=int(asset_type_id),
                    created_by=user_id,
                    metadata_json=metadata
                )
                db.session.add(record)
                db.session.commit()
                record_id = record.id
            except Exception as e:
                db.session.rollback()
                print(f"Record creation error: {e}")
        
        return jsonify({
            'success': True,
            'schema_id': schema.id,
            'schema_name': schema.name,
            'field_count': len(fields),
            'record_id': record_id,
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Schema creation error: {str(e)}'}), 500


@uploads_bp.route('/smart-upload', methods=['POST'])
@jwt_required()
def smart_upload():
    """
    Single endpoint: upload a file, auto-extract metadata, auto-create schema if needed,
    and create the metadata record.

    Form data:
      - file: uploaded file (required)
      - asset_type_id: target asset type (required)
      - record_name: optional display name for the record
    """
    user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    asset_type_id = request.form.get('asset_type_id')
    record_name = request.form.get('record_name') or file.filename

    if not asset_type_id:
        return jsonify({'error': 'asset_type_id is required'}), 400
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        # Save temp file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)

        # Extract metadata and suggested fields
        metadata, fields = extractor_service.extract(temp_path, file.filename)

        # Compute candidate existing schemas by field overlap
        def _score_schema(s: SchemaModel) -> float:
            s_field_names = {f.field_name for f in s.fields if not f.is_deleted}
            incoming = {f.get('field_name') for f in fields}
            common = s_field_names.intersection(incoming)
            return round((len(common) / max(1, len(incoming))) * 100, 1)

        candidates_q = SchemaModel.query.filter(SchemaModel.asset_type_id == int(asset_type_id))
        candidates = [
            {
                'id': s.id,
                'name': s.name,
                'version': s.version,
                'match_score': _score_schema(s),
                'fields': [f.field_name for f in s.fields if not f.is_deleted]
            }
            for s in candidates_q.all()
        ]
        candidates.sort(key=lambda x: x['match_score'], reverse=True)

        # If no action specified, return suggestions without creating anything
        action = request.form.get('action')  # 'use_existing' | 'create_new'
        if not action:
            # Clean up temp file
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return jsonify({
                'success': True,
                'metadata': metadata,
                'suggested_fields': fields,
                'candidates': candidates,
            }), 200

        # Decide: use existing schema or create new, then persist file and record
        if action == 'use_existing':
            schema_id_str = request.form.get('schema_id')
            if not schema_id_str:
                return jsonify({'error': 'schema_id required for use_existing'}), 400
            schema = SchemaModel.query.get(int(schema_id_str))
            if not schema:
                return jsonify({'error': 'schema not found'}), 404
        elif action == 'create_new':
            base_name = os.path.splitext(file.filename)[0].replace('_', ' ').title()
            schema_name = request.form.get('schema_name') or f"{base_name} Metadata"
            schema = SchemaModel(
                name=schema_name,
                version=1,
                asset_type_id=int(asset_type_id),
                schema_json={},
                created_by=user_id
            )
            db.session.add(schema)
            db.session.flush()
            for idx, field_def in enumerate(fields):
                field = SchemaField(
                    schema_id=schema.id,
                    field_name=field_def.get('field_name'),
                    field_type=field_def.get('field_type', 'string'),
                    is_required=field_def.get('is_required', False),
                    description='Auto-generated from file upload',
                    order_index=idx
                )
                db.session.add(field)
            db.session.commit()
        else:
            return jsonify({'error': 'invalid action'}), 400

        # Persist uploaded file to instance/uploads and include path in metadata
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        uploads_dir = os.path.join(base_dir, 'instance', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        # Unique filename
        from datetime import datetime
        safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        final_path = os.path.join(uploads_dir, safe_name)
        # Copy temp to final
        try:
            import shutil
            shutil.copyfile(temp_path, final_path)
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass

        # Augment metadata with file info
        rel_path = f"instance/uploads/{safe_name}"
        metadata['file_path'] = rel_path
        metadata['original_filename'] = file.filename

        # Create metadata record
        record = MetadataRecord(
            name=record_name,
            schema_id=schema.id,
            asset_type_id=int(asset_type_id),
            created_by=user_id,
            metadata_json=metadata
        )
        db.session.add(record)
        db.session.flush()  # Flush to get record ID

        # Create FieldValue entries for extracted metadata
        schema_fields = {f.field_name: f for f in schema.fields if not f.is_deleted}
        for field_name, field_value in metadata.items():
            if field_name in schema_fields:
                schema_field = schema_fields[field_name]
                fv = FieldValue(record_id=record.id, schema_field_id=schema_field.id)
                fv.schema_field = schema_field
                try:
                    fv.set_value(field_value)
                except Exception as e:
                    print(f"Error setting field {field_name}: {e}")
                db.session.add(fv)

        db.session.commit()

        return jsonify({
            'success': True,
            'schema_id': schema.id,
            'schema_name': schema.name,
            'field_count': len(fields),
            'record_id': record.id,
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Smart upload error: {str(e)}'}), 500
