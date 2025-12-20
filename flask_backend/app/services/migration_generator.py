"""
MigrationGenerator - Generate SQL migration scripts for schema changes
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models import SchemaModel, SchemaField, SchemaVersion
from .schema_version_control import SchemaVersionControl


class MigrationGenerator:
    """
    Generates SQL migration scripts for schema changes
    """
    
    def __init__(self):
        self.version_control = SchemaVersionControl()
    
    def generate_migration(
        self,
        schema_id: int,
        from_version: int,
        to_version: int,
        dialect: str = 'postgresql'
    ) -> str:
        """
        Generate migration script between two versions
        
        Args:
            schema_id: Schema ID
            from_version: Starting version
            to_version: Target version
            dialect: SQL dialect ('postgresql', 'mysql', 'sqlite')
        
        Returns:
            SQL migration script
        """
        if from_version == to_version:
            return "-- No migration needed (same version)"
        
        # Get version snapshots
        from_snap = self.version_control.get_version(schema_id, from_version)
        to_snap = self.version_control.get_version(schema_id, to_version)
        
        if not from_snap or not to_snap:
            raise ValueError("Version not found")
        
        # Calculate diff
        diff = self.version_control._calculate_diff(
            from_snap['schema_snapshot'],
            to_snap['schema_snapshot']
        )
        
        # Generate script
        script = self._generate_script_header(
            schema_id, from_version, to_version, diff
        )
        
        script += "\nBEGIN TRANSACTION;\n\n"
        
        # Generate statements for each change
        table_name = f"metadata_record_{schema_id}"  # Virtual table name
        
        # Add new fields
        for field_name in diff['added_fields']:
            field_def = next(
                (f for f in to_snap['schema_snapshot']['fields'] if f['name'] == field_name),
                None
            )
            if field_def:
                script += self._generate_add_field_sql(
                    table_name, field_def, dialect
                )
        
        # Modify existing fields
        for field_name, changes in diff['modified_fields'].items():
            from_field = next(
                (f for f in from_snap['schema_snapshot']['fields'] if f['name'] == field_name),
                None
            )
            to_field = next(
                (f for f in to_snap['schema_snapshot']['fields'] if f['name'] == field_name),
                None
            )
            if from_field and to_field:
                script += self._generate_modify_field_sql(
                    table_name, from_field, to_field, dialect
                )
        
        # Remove fields
        for field_name in diff['removed_fields']:
            script += self._generate_remove_field_sql(
                table_name, field_name, dialect
            )
        
        script += "\nCOMMIT;\n"
        
        return script
    
    def generate_rollback_script(
        self,
        schema_id: int,
        target_version: int,
        dialect: str = 'postgresql'
    ) -> str:
        """
        Generate rollback script to a specific version
        
        Args:
            schema_id: Schema ID
            target_version: Target version to rollback to
            dialect: SQL dialect
        
        Returns:
            SQL rollback script
        """
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")
        
        current = self.version_control.get_latest_version(schema_id)
        if not current:
            raise ValueError("No version history found")
        
        current_version = current['version_number']
        
        return self.generate_migration(
            schema_id,
            current_version,
            target_version,
            dialect
        )
    
    def generate_full_schema_ddl(
        self,
        schema_id: int,
        dialect: str = 'postgresql'
    ) -> str:
        """
        Generate complete DDL for current schema state
        
        Args:
            schema_id: Schema ID
            dialect: SQL dialect
        
        Returns:
            Complete CREATE TABLE statement
        """
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")
        
        fields = SchemaField.query.filter_by(
            schema_id=schema_id,
            is_deleted=False
        ).order_by(SchemaField.order_index).all()
        
        table_name = f"metadata_record_{schema_id}"
        
        script = f"-- Full schema DDL for {schema.name} (v{schema.version})\n"
        script += f"-- Generated on {datetime.utcnow().isoformat()}\n\n"
        
        script += f"CREATE TABLE {table_name} (\n"
        script += "    id SERIAL PRIMARY KEY,\n"
        script += "    record_id INTEGER NOT NULL,\n"
        
        for field in fields:
            sql_type = self._get_sql_type(field.field_type, dialect)
            nullable = "NOT NULL" if field.is_required else "NULL"
            default = f" DEFAULT {self._format_default(field.default_value, field.field_type)}" if field.default_value else ""
            
            script += f"    {field.field_name} {sql_type} {nullable}{default},\n"
        
        script += "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
        script += "    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
        script += ");\n\n"
        
        # Add indexes
        script += f"CREATE INDEX idx_{table_name}_record_id ON {table_name}(record_id);\n"
        
        return script
    
    def generate_data_migration(
        self,
        schema_id: int,
        from_version: int,
        to_version: int
    ) -> str:
        """
        Generate data migration script (for type conversions, etc.)
        
        Args:
            schema_id: Schema ID
            from_version: Starting version
            to_version: Target version
        
        Returns:
            Data migration script
        """
        diff_result = self.version_control.compare_versions(
            schema_id, from_version, to_version
        )
        
        script = f"-- Data migration from v{from_version} to v{to_version}\n\n"
        script += "BEGIN TRANSACTION;\n\n"
        
        # Handle type changes that need data conversion
        for field_name, changes in diff_result.get('modified_fields', {}).items():
            if any('type:' in change for change in changes):
                script += f"-- Convert {field_name} data type\n"
                script += f"-- Review and adjust conversion logic as needed\n"
                script += f"UPDATE field_values\n"
                script += f"SET value_text = CAST(value_int AS TEXT)\n"
                script += f"WHERE schema_field_id IN (\n"
                script += f"    SELECT id FROM schema_fields\n"
                script += f"    WHERE schema_id = {schema_id} AND field_name = '{field_name}'\n"
                script += f");\n\n"
        
        script += "COMMIT;\n"
        
        return script
    
    # Private helper methods
    
    def _generate_script_header(
        self,
        schema_id: int,
        from_version: int,
        to_version: int,
        diff: Dict
    ) -> str:
        """Generate migration script header"""
        direction = "↑" if to_version > from_version else "↓"
        
        header = f"""-- ============================================
-- Migration Script
-- Schema ID: {schema_id}
-- From Version: {from_version} {direction} To Version: {to_version}
-- Generated: {datetime.utcnow().isoformat()}
-- ============================================
-- Changes Summary:
--   Fields Added: {len(diff['added_fields'])}
--   Fields Removed: {len(diff['removed_fields'])}
--   Fields Modified: {len(diff['modified_fields'])}
-- ============================================
"""
        return header
    
    def _generate_add_field_sql(
        self,
        table_name: str,
        field_def: Dict,
        dialect: str
    ) -> str:
        """Generate SQL for adding a field"""
        sql_type = self._get_sql_type(field_def['type'], dialect)
        nullable = "NOT NULL" if field_def['required'] else "NULL"
        default = f" DEFAULT {self._format_default(field_def.get('default'), field_def['type'])}" if field_def.get('default') else ""
        
        sql = f"-- Add field: {field_def['name']}\n"
        sql += f"ALTER TABLE {table_name} ADD COLUMN {field_def['name']} {sql_type} {nullable}{default};\n\n"
        
        return sql
    
    def _generate_modify_field_sql(
        self,
        table_name: str,
        from_field: Dict,
        to_field: Dict,
        dialect: str
    ) -> str:
        """Generate SQL for modifying a field"""
        sql = f"-- Modify field: {from_field['name']}\n"
        
        # Type change
        if from_field['type'] != to_field['type']:
            if dialect == 'postgresql':
                new_type = self._get_sql_type(to_field['type'], dialect)
                sql += f"ALTER TABLE {table_name} ALTER COLUMN {from_field['name']} TYPE {new_type} USING {from_field['name']}::{new_type};\n"
            elif dialect == 'mysql':
                new_type = self._get_sql_type(to_field['type'], dialect)
                nullable = "NOT NULL" if to_field['required'] else "NULL"
                sql += f"ALTER TABLE {table_name} MODIFY COLUMN {from_field['name']} {new_type} {nullable};\n"
        
        # Nullability change
        if from_field['required'] != to_field['required']:
            if dialect == 'postgresql':
                if to_field['required']:
                    sql += f"ALTER TABLE {table_name} ALTER COLUMN {from_field['name']} SET NOT NULL;\n"
                else:
                    sql += f"ALTER TABLE {table_name} ALTER COLUMN {from_field['name']} DROP NOT NULL;\n"
        
        sql += "\n"
        return sql
    
    def _generate_remove_field_sql(
        self,
        table_name: str,
        field_name: str,
        dialect: str
    ) -> str:
        """Generate SQL for removing a field"""
        sql = f"-- Remove field: {field_name}\n"
        sql += f"ALTER TABLE {table_name} DROP COLUMN {field_name};\n\n"
        return sql
    
    def _get_sql_type(self, field_type: str, dialect: str) -> str:
        """Map field type to SQL type"""
        type_map = {
            'postgresql': {
                'string': 'TEXT',
                'integer': 'INTEGER',
                'float': 'DOUBLE PRECISION',
                'boolean': 'BOOLEAN',
                'date': 'TIMESTAMP',
                'json': 'JSONB',
                'array': 'JSONB',
                'object': 'JSONB'
            },
            'mysql': {
                'string': 'TEXT',
                'integer': 'INT',
                'float': 'DOUBLE',
                'boolean': 'BOOLEAN',
                'date': 'DATETIME',
                'json': 'JSON',
                'array': 'JSON',
                'object': 'JSON'
            },
            'sqlite': {
                'string': 'TEXT',
                'integer': 'INTEGER',
                'float': 'REAL',
                'boolean': 'INTEGER',
                'date': 'TEXT',
                'json': 'TEXT',
                'array': 'TEXT',
                'object': 'TEXT'
            }
        }
        
        return type_map.get(dialect, type_map['postgresql']).get(field_type, 'TEXT')
    
    def _format_default(self, value: Any, field_type: str) -> str:
        """Format default value for SQL"""
        if value is None:
            return 'NULL'
        
        if field_type == 'string':
            return f"'{value}'"
        elif field_type == 'boolean':
            return 'TRUE' if value else 'FALSE'
        elif field_type in ('json', 'array', 'object'):
            import json
            return f"'{json.dumps(value)}'"
        else:
            return str(value)


class ImpactAnalyzer:
    """
    Analyzes impact of schema changes before applying them
    """
    
    def analyze_field_addition(
        self,
        schema_id: int,
        field_def: Dict
    ) -> Dict[str, Any]:
        """Analyze impact of adding a field"""
        from ..models import MetadataRecord
        
        record_count = MetadataRecord.query.filter_by(schema_id=schema_id).count()
        
        return {
            'operation': 'add_field',
            'field_name': field_def['name'],
            'field_type': field_def['type'],
            'affected_records': record_count,
            'estimated_time_seconds': record_count * 0.001,  # Rough estimate
            'storage_impact_mb': record_count * 0.0001,  # Rough estimate
            'risk_level': 'low' if not field_def.get('required') else 'medium',
            'requires_default': field_def.get('required', False) and record_count > 0,
            'recommendations': [
                "Add during low-traffic period" if record_count > 10000 else None,
                "Provide default value for required field" if field_def.get('required') else None
            ]
        }
    
    def analyze_field_removal(
        self,
        schema_id: int,
        field_name: str
    ) -> Dict[str, Any]:
        """Analyze impact of removing a field"""
        field = SchemaField.query.filter_by(
            schema_id=schema_id,
            field_name=field_name,
            is_deleted=False
        ).first()
        
        if not field:
            return {'error': 'Field not found'}
        
        from ..models import FieldValue
        
        value_count = FieldValue.query.filter_by(schema_field_id=field.id).count()
        non_null_count = db.session.query(db.func.count(FieldValue.id)).filter(
            FieldValue.schema_field_id == field.id,
            db.or_(
                FieldValue.value_text.isnot(None),
                FieldValue.value_int.isnot(None),
                FieldValue.value_float.isnot(None),
                FieldValue.value_bool.isnot(None),
                FieldValue.value_date.isnot(None),
                FieldValue.value_json.isnot(None)
            )
        ).scalar()
        
        return {
            'operation': 'remove_field',
            'field_name': field_name,
            'field_type': field.field_type,
            'affected_values': value_count,
            'non_null_values': non_null_count,
            'data_loss': non_null_count > 0,
            'risk_level': 'critical' if non_null_count > 100 else 'high' if non_null_count > 0 else 'low',
            'recommendations': [
                '⚠️  CRITICAL: Will lose data!' if non_null_count > 0 else None,
                'Use soft delete instead of hard delete' if non_null_count > 0 else None,
                'Export data before deletion' if non_null_count > 100 else None
            ]
        }
    
    def analyze_type_change(
        self,
        schema_id: int,
        field_name: str,
        new_type: str
    ) -> Dict[str, Any]:
        """Analyze impact of changing field type"""
        field = SchemaField.query.filter_by(
            schema_id=schema_id,
            field_name=field_name,
            is_deleted=False
        ).first()
        
        if not field:
            return {'error': 'Field not found'}
        
        from ..models import FieldValue
        from .validation_engine import ValidationEngine
        
        validator = ValidationEngine()
        validation_errors = validator.validate_type_change(
            field.id, field.field_type, new_type
        )
        
        value_count = FieldValue.query.filter_by(schema_field_id=field.id).count()
        
        return {
            'operation': 'change_type',
            'field_name': field_name,
            'old_type': field.field_type,
            'new_type': new_type,
            'affected_values': value_count,
            'validation_errors': validation_errors,
            'risk_level': 'high' if validation_errors else 'medium',
            'requires_migration': True,
            'reversible': new_type == 'string',  # String conversion is usually reversible
            'recommendations': [
                'Test conversion on sample data first',
                'Backup data before conversion' if value_count > 1000 else None,
                'Consider creating new field instead' if validation_errors else None
            ]
        }
