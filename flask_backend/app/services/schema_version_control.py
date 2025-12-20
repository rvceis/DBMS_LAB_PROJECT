"""
SchemaVersionControl - Manage schema versions and rollbacks
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from ..models import SchemaModel, SchemaField, SchemaVersion, ChangeLog, FieldValue
from ..extensions import db
from .metadata_catalog import MetadataCatalog


class SchemaVersionControl:
    """
    Handles schema versioning and rollback operations
    """
    
    def __init__(self):
        self.catalog = MetadataCatalog()
    
    def get_version(self, schema_id: int, version_number: int) -> Optional[Dict]:
        """
        Get a specific schema version
        
        Args:
            schema_id: Schema ID
            version_number: Version number
        
        Returns:
            Version snapshot or None
        """
        version = SchemaVersion.query.filter_by(
            schema_id=schema_id,
            version_number=version_number
        ).first()
        
        if not version:
            return None
        
        return version.to_dict()
    
    def get_latest_version(self, schema_id: int) -> Optional[Dict]:
        """Get the latest version of a schema"""
        version = SchemaVersion.query.filter_by(
            schema_id=schema_id
        ).order_by(SchemaVersion.version_number.desc()).first()
        
        if not version:
            return None
        
        return version.to_dict()
    
    def list_versions(
        self,
        schema_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """
        List all versions of a schema
        
        Args:
            schema_id: Schema ID
            limit: Maximum number of versions to return
        
        Returns:
            List of version dicts
        """
        versions = SchemaVersion.query.filter_by(
            schema_id=schema_id
        ).order_by(SchemaVersion.version_number.desc()).limit(limit).all()
        
        return [v.to_dict() for v in versions]
    
    def compare_versions(
        self,
        schema_id: int,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """
        Compare two schema versions
        
        Args:
            schema_id: Schema ID
            version1: First version number
            version2: Second version number
        
        Returns:
            Diff dict with changes
        """
        v1 = SchemaVersion.query.filter_by(
            schema_id=schema_id,
            version_number=version1
        ).first()
        
        v2 = SchemaVersion.query.filter_by(
            schema_id=schema_id,
            version_number=version2
        ).first()
        
        if not v1 or not v2:
            raise ValueError("Version not found")
        
        return self._calculate_diff(v1.schema_snapshot, v2.schema_snapshot)
    
    def rollback(
        self,
        schema_id: int,
        target_version: int,
        user_id: int,
        preserve_data: bool = True
    ) -> Dict[str, Any]:
        """
        Rollback schema to a previous version
        
        Args:
            schema_id: Schema to rollback
            target_version: Target version number
            user_id: User performing rollback
            preserve_data: If True, soft delete fields. If False, hard delete
        
        Returns:
            Rollback result dict
        """
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")
        
        target = SchemaVersion.query.filter_by(
            schema_id=schema_id,
            version_number=target_version
        ).first()
        
        if not target:
            raise ValueError(f"Version {target_version} not found")
        
        current_version = SchemaVersion.query.filter_by(
            schema_id=schema_id
        ).order_by(SchemaVersion.version_number.desc()).first()
        
        if current_version.version_number == target_version:
            return {
                'success': True,
                'message': 'Already at target version',
                'changes': []
            }
        
        # Calculate what needs to be done
        diff = self._calculate_diff(
            current_version.schema_snapshot,
            target.schema_snapshot
        )
        
        try:
            # Start transaction
            changes_made = []
            
            # Handle removed fields (fields in target but not in current)
            for field_name in diff['added_fields']:
                # These were removed, need to restore or create
                field_def = next(
                    (f for f in target.schema_snapshot['fields'] if f['name'] == field_name),
                    None
                )
                if field_def:
                    # Check if soft deleted
                    existing = SchemaField.query.filter_by(
                        schema_id=schema_id,
                        field_name=field_name,
                        is_deleted=True
                    ).first()
                    
                    if existing:
                        # Restore soft deleted field
                        existing.is_deleted = False
                        changes_made.append(f"Restored field '{field_name}'")
                    else:
                        # Create new field
                        new_field = SchemaField(
                            schema_id=schema_id,
                            field_name=field_def['name'],
                            field_type=field_def['type'],
                            is_required=field_def['required'],
                            default_value=field_def.get('default'),
                            constraints=field_def.get('constraints'),
                            description=field_def.get('description'),
                            order_index=field_def.get('order', 0)
                        )
                        db.session.add(new_field)
                        changes_made.append(f"Recreated field '{field_name}'")
            
            # Handle added fields (fields in current but not in target)
            for field_name in diff['removed_fields']:
                # These need to be removed
                field = SchemaField.query.filter_by(
                    schema_id=schema_id,
                    field_name=field_name,
                    is_deleted=False
                ).first()
                
                if field:
                    if preserve_data:
                        # Soft delete
                        field.is_deleted = True
                        changes_made.append(f"Soft deleted field '{field_name}'")
                    else:
                        # Hard delete
                        FieldValue.query.filter_by(schema_field_id=field.id).delete()
                        db.session.delete(field)
                        changes_made.append(f"Deleted field '{field_name}' and all data")
            
            # Handle modified fields
            for field_name, changes in diff['modified_fields'].items():
                field = SchemaField.query.filter_by(
                    schema_id=schema_id,
                    field_name=field_name,
                    is_deleted=False
                ).first()
                
                if field:
                    target_field = next(
                        (f for f in target.schema_snapshot['fields'] if f['name'] == field_name),
                        None
                    )
                    
                    if target_field:
                        field.field_type = target_field['type']
                        field.is_required = target_field['required']
                        field.default_value = target_field.get('default')
                        field.constraints = target_field.get('constraints')
                        field.description = target_field.get('description')
                        field.order_index = target_field.get('order', 0)
                        changes_made.append(f"Reverted field '{field_name}': {', '.join(changes)}")
            
            # Create change log
            log = ChangeLog(
                schema_id=schema_id,
                change_type='rollback',
                description=f"Rolled back from v{current_version.version_number} to v{target_version}",
                change_details={
                    'from_version': current_version.version_number,
                    'to_version': target_version,
                    'changes': changes_made,
                    'preserve_data': preserve_data
                },
                schema_snapshot=target.schema_snapshot,
                changed_by=user_id
            )
            db.session.add(log)
            
            db.session.commit()
            
            # Invalidate cache
            self.catalog.invalidate_schema(schema_id)
            
            return {
                'success': True,
                'message': f'Successfully rolled back to version {target_version}',
                'from_version': current_version.version_number,
                'to_version': target_version,
                'changes': changes_made
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'changes': changes_made
            }
    
    def get_change_history(
        self,
        schema_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get change history for a schema
        
        Args:
            schema_id: Schema ID
            limit: Maximum number of changes to return
        
        Returns:
            List of change log entries
        """
        logs = ChangeLog.query.filter_by(
            schema_id=schema_id
        ).order_by(ChangeLog.timestamp.desc()).limit(limit).all()
        
        return [log.to_dict() for log in logs]
    
    def get_field_history(
        self,
        schema_id: int,
        field_name: str
    ) -> List[Dict]:
        """
        Get history of changes to a specific field
        
        Args:
            schema_id: Schema ID
            field_name: Field name
        
        Returns:
            List of changes affecting this field
        """
        logs = ChangeLog.query.filter_by(schema_id=schema_id).order_by(
            ChangeLog.timestamp.desc()
        ).all()
        
        field_logs = []
        for log in logs:
            if log.change_details:
                if 'field_name' in log.change_details:
                    if log.change_details['field_name'] == field_name:
                        field_logs.append(log.to_dict())
        
        return field_logs
    
    def create_snapshot(
        self,
        schema_id: int,
        user_id: int,
        change_summary: Optional[str] = None
    ) -> SchemaVersion:
        """
        Create a manual snapshot of current schema state
        
        Args:
            schema_id: Schema to snapshot
            user_id: User creating snapshot
            change_summary: Optional description
        
        Returns:
            Created SchemaVersion
        """
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")
        
        latest = SchemaVersion.query.filter_by(
            schema_id=schema_id
        ).order_by(SchemaVersion.version_number.desc()).first()
        
        version_number = (latest.version_number + 1) if latest else 1
        
        snapshot = self._build_snapshot(schema)
        
        version = SchemaVersion(
            schema_id=schema_id,
            version_number=version_number,
            schema_snapshot=snapshot,
            change_summary=change_summary or f"Manual snapshot v{version_number}",
            created_by=user_id
        )
        
        db.session.add(version)
        db.session.commit()
        
        return version
    
    # Private methods
    
    def _calculate_diff(
        self,
        snapshot1: Dict,
        snapshot2: Dict
    ) -> Dict[str, Any]:
        """Calculate differences between two schema snapshots"""
        fields1 = {f['name']: f for f in snapshot1.get('fields', [])}
        fields2 = {f['name']: f for f in snapshot2.get('fields', [])}
        
        # Fields in snapshot2 but not in snapshot1 (added)
        added_fields = [name for name in fields2 if name not in fields1]
        
        # Fields in snapshot1 but not in snapshot2 (removed)
        removed_fields = [name for name in fields1 if name not in fields2]
        
        # Fields in both but modified
        modified_fields = {}
        for name in fields1:
            if name in fields2:
                changes = []
                if fields1[name]['type'] != fields2[name]['type']:
                    changes.append(f"type: {fields1[name]['type']} → {fields2[name]['type']}")
                if fields1[name]['required'] != fields2[name]['required']:
                    changes.append(f"required: {fields1[name]['required']} → {fields2[name]['required']}")
                if fields1[name].get('constraints') != fields2[name].get('constraints'):
                    changes.append("constraints changed")
                
                if changes:
                    modified_fields[name] = changes
        
        return {
            'added_fields': added_fields,
            'removed_fields': removed_fields,
            'modified_fields': modified_fields,
            'summary': {
                'total_changes': len(added_fields) + len(removed_fields) + len(modified_fields),
                'additions': len(added_fields),
                'removals': len(removed_fields),
                'modifications': len(modified_fields)
            }
        }
    
    def _build_snapshot(self, schema: SchemaModel) -> Dict:
        """Build complete schema snapshot"""
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
