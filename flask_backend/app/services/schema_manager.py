"""
SchemaManager - Core service for dynamic schema operations
Handles creation, modification, and deletion of schema fields at runtime
"""
import threading
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from ..models import SchemaModel, SchemaField, MetadataRecord, FieldValue, ChangeLog, SchemaVersion
from ..extensions import db
from .validation_engine import ValidationEngine
from .metadata_catalog import MetadataCatalog


class SchemaManager:
    """
    Manages dynamic schema operations with thread-safety
    """
    
    def __init__(self):
        self.lock = threading.RLock()  # Reentrant lock for nested calls
        self.schema_locks = {}  # Per-schema locking
        self.validation_engine = ValidationEngine()
        self.catalog = MetadataCatalog()
    
    def _get_lock(self, schema_id: int) -> threading.RLock:
        """Get or create a lock for a specific schema"""
        if schema_id not in self.schema_locks:
            with self.lock:
                if schema_id not in self.schema_locks:
                    self.schema_locks[schema_id] = threading.RLock()
        return self.schema_locks[schema_id]
    
    def create_schema(
        self,
        name: str,
        asset_type_id: int,
        fields: List[Dict[str, Any]],
        user_id: int,
        allow_additional_fields: bool = True,
        parent_schema_id: Optional[int] = None
    ) -> SchemaModel:
        """
        Create a new dynamic schema with fields
        
        Args:
            name: Schema name
            asset_type_id: Asset type ID
            fields: List of field definitions [{"name": "...", "type": "...", "required": bool, ...}]
            user_id: User creating the schema
            allow_additional_fields: Whether to allow fields not in schema
            parent_schema_id: Parent schema for inheritance
        
        Returns:
            Created SchemaModel
        """
        with self.lock:
            # Validate fields
            validation_errors = self.validation_engine.validate_fields(fields)
            if validation_errors:
                raise ValueError(f"Field validation failed: {validation_errors}")
            
            # Get next version
            latest = SchemaModel.query.filter_by(asset_type_id=asset_type_id).order_by(
                SchemaModel.version.desc()
            ).first()
            version = (latest.version + 1) if latest else 1
            
            # Create schema
            schema = SchemaModel(
                name=name,
                version=version,
                asset_type_id=asset_type_id,
                parent_schema_id=parent_schema_id,
                allow_additional_fields=allow_additional_fields,
                is_active=True,
                created_by=user_id
            )
            
            try:
                db.session.add(schema)
                db.session.flush()  # Get schema ID
                
                # Add fields
                for idx, field_def in enumerate(fields):
                    field = SchemaField(
                        schema_id=schema.id,
                        field_name=field_def['name'],
                        field_type=field_def.get('type', 'string'),
                        is_required=field_def.get('required', False),
                        default_value=field_def.get('default'),
                        constraints=field_def.get('constraints'),
                        description=field_def.get('description'),
                        order_index=idx
                    )
                    db.session.add(field)
                
                # Create change log
                log = ChangeLog(
                    schema_id=schema.id,
                    change_type='created',
                    description=f"Schema '{name}' v{version} created",
                    change_details={'fields_count': len(fields)},
                    schema_snapshot=self._get_schema_snapshot(schema),
                    changed_by=user_id
                )
                db.session.add(log)
                
                # Create version snapshot
                version_snapshot = SchemaVersion(
                    schema_id=schema.id,
                    version_number=1,
                    schema_snapshot=self._get_schema_snapshot(schema),
                    change_summary=f"Initial schema creation with {len(fields)} fields",
                    created_by=user_id
                )
                db.session.add(version_snapshot)
                
                db.session.commit()
                
                # Invalidate cache
                self.catalog.invalidate_schema(schema.id)
                
                return schema
                
            except Exception as e:
                db.session.rollback()
                raise Exception(f"Failed to create schema: {str(e)}")
    
    def add_field(
        self,
        schema_id: int,
        field_name: str,
        field_type: str,
        user_id: int,
        is_required: bool = False,
        default_value: Optional[str] = None,
        constraints: Optional[Dict] = None,
        description: Optional[str] = None
    ) -> SchemaField:
        """
        Add a field to an existing schema
        
        Args:
            schema_id: Schema to modify
            field_name: Name of the new field
            field_type: Data type (string, integer, float, boolean, date, json, array)
            user_id: User making the change
            is_required: Whether field is required
            default_value: Default value for existing records
            constraints: Field constraints
            description: Field description
        
        Returns:
            Created SchemaField
        """
        schema_lock = self._get_lock(schema_id)
        
        with schema_lock:
            schema = SchemaModel.query.get(schema_id)
            if not schema:
                raise ValueError(f"Schema {schema_id} not found")
            
            # Check if field already exists
            existing = SchemaField.query.filter_by(
                schema_id=schema_id,
                field_name=field_name,
                is_deleted=False
            ).first()
            
            if existing:
                raise ValueError(f"Field '{field_name}' already exists in schema")
            
            # Validate field addition
            field_def = {
                'name': field_name,
                'type': field_type,
                'required': is_required,
                'default': default_value,
                'constraints': constraints
            }
            
            record_count = MetadataRecord.query.filter_by(schema_id=schema_id).count()
            validation_errors = self.validation_engine.validate_add_field(
                schema_id, field_def, record_count
            )
            
            if validation_errors:
                raise ValueError(f"Validation failed: {validation_errors}")
            
            try:
                # Get next order index
                max_order = db.session.query(db.func.max(SchemaField.order_index)).filter_by(
                    schema_id=schema_id
                ).scalar() or 0
                
                # Create field
                field = SchemaField(
                    schema_id=schema_id,
                    field_name=field_name,
                    field_type=field_type,
                    is_required=is_required,
                    default_value=default_value,
                    constraints=constraints,
                    description=description,
                    order_index=max_order + 1
                )
                db.session.add(field)
                db.session.flush()
                
                # If required and has default, add default values to existing records
                if is_required and default_value and record_count > 0:
                    self._add_default_values_to_existing_records(field, default_value)
                
                # Create change log
                log = ChangeLog(
                    schema_id=schema_id,
                    change_type='field_added',
                    description=f"Added field '{field_name}' ({field_type})",
                    change_details={
                        'field_name': field_name,
                        'field_type': field_type,
                        'is_required': is_required,
                        'affected_records': record_count
                    },
                    schema_snapshot=self._get_schema_snapshot(schema),
                    changed_by=user_id
                )
                db.session.add(log)
                
                # Create new version
                self._create_version_snapshot(schema, f"Added field '{field_name}'", user_id)
                
                db.session.commit()
                
                # Invalidate cache
                self.catalog.invalidate_schema(schema_id)
                
                return field
                
            except Exception as e:
                db.session.rollback()
                raise Exception(f"Failed to add field: {str(e)}")
    
    def remove_field(
        self,
        schema_id: int,
        field_name: str,
        user_id: int,
        permanent: bool = False
    ) -> bool:
        """
        Remove a field from schema (soft delete by default for rollback safety)
        
        Args:
            schema_id: Schema to modify
            field_name: Field to remove
            user_id: User making the change
            permanent: If True, hard delete (loses data). If False, soft delete
        
        Returns:
            True if successful
        """
        schema_lock = self._get_lock(schema_id)
        
        with schema_lock:
            schema = SchemaModel.query.get(schema_id)
            if not schema:
                raise ValueError(f"Schema {schema_id} not found")
            
            field = SchemaField.query.filter_by(
                schema_id=schema_id,
                field_name=field_name,
                is_deleted=False
            ).first()
            
            if not field:
                raise ValueError(f"Field '{field_name}' not found")
            
            # Check impact
            value_count = FieldValue.query.filter_by(schema_field_id=field.id).count()
            
            try:
                if permanent:
                    # Hard delete - removes all data
                    FieldValue.query.filter_by(schema_field_id=field.id).delete()
                    db.session.delete(field)
                    action = "permanently deleted"
                else:
                    # Soft delete - mark as deleted
                    field.is_deleted = True
                    action = "soft deleted"
                
                # Create change log
                log = ChangeLog(
                    schema_id=schema_id,
                    change_type='field_removed',
                    description=f"Field '{field_name}' {action}",
                    change_details={
                        'field_name': field_name,
                        'field_type': field.field_type,
                        'permanent': permanent,
                        'affected_values': value_count
                    },
                    schema_snapshot=self._get_schema_snapshot(schema),
                    changed_by=user_id
                )
                db.session.add(log)
                
                # Create new version
                self._create_version_snapshot(schema, f"Removed field '{field_name}'", user_id)
                
                db.session.commit()
                
                # Invalidate cache
                self.catalog.invalidate_schema(schema_id)
                
                return True
                
            except Exception as e:
                db.session.rollback()
                raise Exception(f"Failed to remove field: {str(e)}")
    
    def modify_field(
        self,
        schema_id: int,
        field_name: str,
        user_id: int,
        new_type: Optional[str] = None,
        new_required: Optional[bool] = None,
        new_constraints: Optional[Dict] = None,
        new_description: Optional[str] = None
    ) -> SchemaField:
        """
        Modify an existing field's properties
        
        Args:
            schema_id: Schema to modify
            field_name: Field to modify
            user_id: User making the change
            new_type: New data type (requires data migration)
            new_required: New required status
            new_constraints: New constraints
            new_description: New description
        
        Returns:
            Modified SchemaField
        """
        schema_lock = self._get_lock(schema_id)
        
        with schema_lock:
            schema = SchemaModel.query.get(schema_id)
            if not schema:
                raise ValueError(f"Schema {schema_id} not found")
            
            field = SchemaField.query.filter_by(
                schema_id=schema_id,
                field_name=field_name,
                is_deleted=False
            ).first()
            
            if not field:
                raise ValueError(f"Field '{field_name}' not found")
            
            old_type = field.field_type
            changes = []
            
            try:
                # Type change requires data migration
                if new_type and new_type != old_type:
                    validation_errors = self.validation_engine.validate_type_change(
                        field.id, old_type, new_type
                    )
                    if validation_errors:
                        raise ValueError(f"Type change validation failed: {validation_errors}")
                    
                    # Migrate data
                    self._migrate_field_type(field, old_type, new_type)
                    field.field_type = new_type
                    changes.append(f"type: {old_type} → {new_type}")
                
                # Update other properties
                if new_required is not None and new_required != field.is_required:
                    field.is_required = new_required
                    changes.append(f"required: {field.is_required} → {new_required}")
                
                if new_constraints is not None:
                    field.constraints = new_constraints
                    changes.append("constraints updated")
                
                if new_description is not None:
                    field.description = new_description
                    changes.append("description updated")
                
                if not changes:
                    return field
                
                # Create change log
                log = ChangeLog(
                    schema_id=schema_id,
                    change_type='field_modified',
                    description=f"Modified field '{field_name}': {', '.join(changes)}",
                    change_details={
                        'field_name': field_name,
                        'changes': changes,
                        'old_type': old_type if new_type else None,
                        'new_type': new_type if new_type else None
                    },
                    schema_snapshot=self._get_schema_snapshot(schema),
                    changed_by=user_id
                )
                db.session.add(log)
                
                # Create new version
                self._create_version_snapshot(
                    schema,
                    f"Modified field '{field_name}'",
                    user_id
                )
                
                db.session.commit()
                
                # Invalidate cache
                self.catalog.invalidate_schema(schema_id)
                
                return field
                
            except Exception as e:
                db.session.rollback()
                raise Exception(f"Failed to modify field: {str(e)}")
    
    def fork_schema(
        self,
        schema_id: int,
        new_name: str,
        user_id: int,
        modifications: Optional[Dict] = None
    ) -> SchemaModel:
        """
        Create a new schema based on an existing one (schema inheritance)
        
        Args:
            schema_id: Parent schema ID
            new_name: Name for new schema
            user_id: User creating the fork
            modifications: Optional changes to make {"add_fields": [...], "remove_fields": [...]}
        
        Returns:
            New SchemaModel
        """
        parent = SchemaModel.query.get(schema_id)
        if not parent:
            raise ValueError(f"Parent schema {schema_id} not found")
        
        # Get parent fields
        parent_fields = SchemaField.query.filter_by(
            schema_id=schema_id,
            is_deleted=False
        ).all()
        
        fields_data = [{
            'name': f.field_name,
            'type': f.field_type,
            'required': f.is_required,
            'default': f.default_value,
            'constraints': f.constraints,
            'description': f.description
        } for f in parent_fields]
        
        # Apply modifications
        if modifications:
            if 'add_fields' in modifications:
                fields_data.extend(modifications['add_fields'])
            if 'remove_fields' in modifications:
                remove_names = set(modifications['remove_fields'])
                fields_data = [f for f in fields_data if f['name'] not in remove_names]
        
        # Create new schema
        return self.create_schema(
            name=new_name,
            asset_type_id=parent.asset_type_id,
            fields=fields_data,
            user_id=user_id,
            allow_additional_fields=parent.allow_additional_fields,
            parent_schema_id=parent.id
        )
    
    # Helper methods
    
    def _get_schema_snapshot(self, schema: SchemaModel) -> Dict:
        """Get complete schema snapshot for versioning"""
        return {
            'schema_id': schema.id,
            'name': schema.name,
            'version': schema.version,
            'asset_type_id': schema.asset_type_id,
            'allow_additional_fields': schema.allow_additional_fields,
            'fields': [
                {
                    'id': f.id,
                    'name': f.field_name,
                    'type': f.field_type,
                    'required': f.is_required,
                    'default': f.default_value,
                    'constraints': f.constraints,
                    'description': f.description,
                    'order': f.order_index,
                    'deleted': f.is_deleted
                }
                for f in schema.fields
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _create_version_snapshot(
        self,
        schema: SchemaModel,
        change_summary: str,
        user_id: int
    ):
        """Create a version snapshot"""
        latest_version = SchemaVersion.query.filter_by(schema_id=schema.id).order_by(
            SchemaVersion.version_number.desc()
        ).first()
        
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
        version = SchemaVersion(
            schema_id=schema.id,
            version_number=version_number,
            schema_snapshot=self._get_schema_snapshot(schema),
            change_summary=change_summary,
            created_by=user_id
        )
        db.session.add(version)
    
    def _add_default_values_to_existing_records(
        self,
        field: SchemaField,
        default_value: str
    ):
        """Add default value to all existing records for a new required field"""
        records = MetadataRecord.query.filter_by(schema_id=field.schema_id).all()
        
        for record in records:
            field_value = FieldValue(
                record_id=record.id,
                schema_field_id=field.id
            )
            field_value.set_value(default_value)
            db.session.add(field_value)
    
    def _migrate_field_type(
        self,
        field: SchemaField,
        old_type: str,
        new_type: str
    ):
        """Migrate field values to new type"""
        values = FieldValue.query.filter_by(schema_field_id=field.id).all()
        
        for value in values:
            old_value = value.get_value()
            if old_value is not None:
                try:
                    # Temporarily change field type for set_value
                    field.field_type = new_type
                    value.set_value(old_value)
                except (ValueError, TypeError) as e:
                    # Rollback field type
                    field.field_type = old_type
                    raise ValueError(
                        f"Cannot convert value '{old_value}' from {old_type} to {new_type}: {str(e)}"
                    )
