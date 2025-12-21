"""
ValidationEngine - Validates schema changes before applying them
Ensures data integrity and compatibility
"""
import re
from typing import List, Dict, Any, Optional
from ..models import SchemaField, FieldValue, MetadataRecord
from ..extensions import db


class ValidationEngine:
    """
    Validates schema modifications before they are applied
    """
    
    # Supported field types
    SUPPORTED_TYPES = [
        'string', 'integer', 'float', 'boolean', 'date', 'json', 'array', 'object'
    ]
    
    # Valid type conversions (old_type -> new_type)
    # More flexible for json/array/object since they can hold any data
    TYPE_COMPATIBILITY = {
        'string': ['string', 'json', 'array', 'object'],  # String can become JSON types
        'integer': ['integer', 'float', 'string', 'json', 'array', 'object'],  # Int can convert to anything
        'float': ['float', 'string', 'json', 'array', 'object'],  # Float to anything
        'boolean': ['boolean', 'string', 'json', 'array', 'object'],  # Bool to anything
        'date': ['date', 'string', 'json', 'array', 'object'],  # Date to anything
        'json': ['json', 'string', 'array', 'object'],  # JSON can convert to other JSON types or string
        'array': ['array', 'string', 'json', 'object'],  # Array similarly flexible
        'object': ['object', 'string', 'json', 'array']  # Object similarly flexible
    }
    
    def validate_fields(self, fields: List[Dict[str, Any]]) -> List[str]:
        """
        Validate a list of field definitions
        
        Args:
            fields: List of field definitions
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        field_names = set()
        
        for idx, field in enumerate(fields):
            # Check required keys
            if 'name' not in field:
                errors.append(f"Field {idx}: Missing 'name'")
                continue
            
            field_name = field['name']
            
            # Check duplicate names
            if field_name in field_names:
                errors.append(f"Field '{field_name}': Duplicate field name")
            field_names.add(field_name)
            
            # Validate field name
            if not self._is_valid_identifier(field_name):
                errors.append(
                    f"Field '{field_name}': Invalid name. Must be alphanumeric "
                    f"with underscores, starting with letter"
                )
            
            # Validate type
            field_type = field.get('type', 'string')
            if field_type not in self.SUPPORTED_TYPES:
                errors.append(
                    f"Field '{field_name}': Unsupported type '{field_type}'. "
                    f"Supported: {', '.join(self.SUPPORTED_TYPES)}"
                )
            
            # Validate constraints
            if 'constraints' in field and field['constraints']:
                constraint_errors = self._validate_constraints(
                    field_name, field_type, field['constraints']
                )
                errors.extend(constraint_errors)
            
            # Validate required + default
            if field.get('required', False) and 'default' not in field:
                errors.append(
                    f"Field '{field_name}': Required fields must have a default value "
                    f"for existing records"
                )
        
        return errors
    
    def validate_add_field(
        self,
        schema_id: int,
        field_def: Dict[str, Any],
        record_count: int
    ) -> List[str]:
        """
        Validate adding a field to existing schema
        
        Args:
            schema_id: Schema to add field to
            field_def: Field definition
            record_count: Number of existing records
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Basic field validation
        errors.extend(self.validate_fields([field_def]))
        
        # If there are existing records and field is required
        if record_count > 0 and field_def.get('required', False):
            if 'default' not in field_def or field_def['default'] is None:
                errors.append(
                    f"Cannot add required field '{field_def['name']}' without default "
                    f"value to schema with {record_count} existing records"
                )
        
        # Performance warning for large tables
        if record_count > 100000:
            errors.append(
                f"WARNING: Adding field to large schema ({record_count} records). "
                f"This may take time and impact performance."
            )
        
        return errors
    
    def validate_type_change(
        self,
        field_id: int,
        old_type: str,
        new_type: str
    ) -> List[str]:
        """
        Validate changing a field's data type
        
        Args:
            field_id: Field to modify
            old_type: Current type
            new_type: New type
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check if type change is allowed
        if new_type not in self.TYPE_COMPATIBILITY.get(old_type, []):
            errors.append(
                f"Cannot convert from '{old_type}' to '{new_type}'. "
                f"Allowed conversions: {', '.join(self.TYPE_COMPATIBILITY.get(old_type, []))}"
            )
            return errors
        
        # Check actual data compatibility
        field = SchemaField.query.get(field_id)
        if not field:
            errors.append(f"Field {field_id} not found")
            return errors
        
        # Sample check - test conversion on existing values
        sample_values = FieldValue.query.filter_by(schema_field_id=field_id).limit(100).all()
        
        incompatible_count = 0
        for value in sample_values:
            current_value = value.get_value()
            if current_value is not None:
                try:
                    self._test_conversion(current_value, old_type, new_type)
                except (ValueError, TypeError):
                    incompatible_count += 1
        
        if incompatible_count > 0:
            total_values = FieldValue.query.filter_by(schema_field_id=field_id).count()
            errors.append(
                f"Found {incompatible_count} incompatible values in sample of {len(sample_values)}. "
                f"Estimated {int(incompatible_count/len(sample_values) * total_values)} "
                f"incompatible values out of {total_values} total."
            )
        
        return errors
    
    def validate_constraints(
        self,
        field_id: int,
        constraints: Dict[str, Any]
    ) -> List[str]:
        """
        Validate adding/modifying constraints on a field
        
        Args:
            field_id: Field to add constraints to
            constraints: Constraint definitions
        
        Returns:
            List of validation errors
        """
        errors = []
        
        field = SchemaField.query.get(field_id)
        if not field:
            errors.append(f"Field {field_id} not found")
            return errors
        
        # Validate constraint format
        constraint_errors = self._validate_constraints(
            field.field_name, field.field_type, constraints
        )
        errors.extend(constraint_errors)
        
        if errors:
            return errors
        
        # Check existing data against constraints
        values = FieldValue.query.filter_by(schema_field_id=field_id).all()
        violations = []
        
        for value in values:
            current_value = value.get_value()
            if current_value is not None:
                violation = self._check_constraint_violation(
                    current_value, field.field_type, constraints
                )
                if violation:
                    violations.append(f"Record {value.record_id}: {violation}")
        
        if violations:
            errors.append(
                f"{len(violations)} records violate new constraints. "
                f"First violations: {', '.join(violations[:5])}"
            )
        
        return errors
    
    def validate_field_removal(
        self,
        schema_id: int,
        field_name: str
    ) -> Dict[str, Any]:
        """
        Analyze impact of removing a field
        
        Args:
            schema_id: Schema ID
            field_name: Field to remove
        
        Returns:
            Impact analysis dict
        """
        field = SchemaField.query.filter_by(
            schema_id=schema_id,
            field_name=field_name,
            is_deleted=False
        ).first()
        
        if not field:
            return {"error": f"Field '{field_name}' not found"}
        
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
            "field_name": field_name,
            "field_type": field.field_type,
            "is_required": field.is_required,
            "total_values": value_count,
            "non_null_values": non_null_count,
            "data_loss_warning": non_null_count > 0,
            "recommendation": "soft_delete" if non_null_count > 0 else "hard_delete"
        }
    
    # Private helper methods
    
    def _is_valid_identifier(self, name: str) -> bool:
        """Check if name is a valid identifier"""
        if not name:
            return False
        # Must start with letter or underscore, contain only alphanumeric and underscore
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name) is not None
    
    def _validate_constraints(
        self,
        field_name: str,
        field_type: str,
        constraints: Dict[str, Any]
    ) -> List[str]:
        """Validate constraint definitions"""
        errors = []
        
        if field_type in ('integer', 'float'):
            if 'min' in constraints and 'max' in constraints:
                if constraints['min'] > constraints['max']:
                    errors.append(f"Field '{field_name}': min > max")
        
        if field_type == 'string':
            if 'min_length' in constraints and 'max_length' in constraints:
                if constraints['min_length'] > constraints['max_length']:
                    errors.append(f"Field '{field_name}': min_length > max_length")
            
            if 'regex' in constraints:
                try:
                    re.compile(constraints['regex'])
                except re.error as e:
                    errors.append(f"Field '{field_name}': Invalid regex: {str(e)}")
        
        if 'enum' in constraints:
            if not isinstance(constraints['enum'], list):
                errors.append(f"Field '{field_name}': enum must be a list")
            elif len(constraints['enum']) == 0:
                errors.append(f"Field '{field_name}': enum cannot be empty")
        
        return errors
    
    def _test_conversion(self, value: Any, old_type: str, new_type: str):
        """Test if a value can be converted from old type to new type"""
        if new_type == 'string':
            str(value)  # Everything can become string
        elif new_type == 'integer':
            int(value)
        elif new_type == 'float':
            float(value)
        elif new_type == 'boolean':
            bool(value)
        # date, json, array, object conversions are more complex
        # For now, allow them if target is string
    
    def _check_constraint_violation(
        self,
        value: Any,
        field_type: str,
        constraints: Dict[str, Any]
    ) -> Optional[str]:
        """Check if a value violates constraints"""
        
        if field_type in ('integer', 'float'):
            if 'min' in constraints and value < constraints['min']:
                return f"Value {value} < min {constraints['min']}"
            if 'max' in constraints and value > constraints['max']:
                return f"Value {value} > max {constraints['max']}"
        
        if field_type == 'string':
            if 'min_length' in constraints and len(value) < constraints['min_length']:
                return f"Length {len(value)} < min_length {constraints['min_length']}"
            if 'max_length' in constraints and len(value) > constraints['max_length']:
                return f"Length {len(value)} > max_length {constraints['max_length']}"
            if 'regex' in constraints and not re.match(constraints['regex'], value):
                return f"Value doesn't match regex {constraints['regex']}"
        
        if 'enum' in constraints and value not in constraints['enum']:
            return f"Value {value} not in enum {constraints['enum']}"
        
        return None
    
    def validate_record_values(self, schema, values: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Validate metadata record values against schema
        
        Args:
            schema: SchemaModel instance
            values: Dict of field_name -> value
        
        Returns:
            List of error dicts with 'field' and 'message'
        """
        errors = []
        active_fields = [f for f in schema.fields if not f.is_deleted]
        
        # Check required fields
        for field in active_fields:
            if field.is_required and field.field_name not in values:
                errors.append({
                    "field": field.field_name,
                    "message": f"{field.field_name} is required"
                })
        
        # Validate each value
        for field_name, value in values.items():
            field = next((f for f in active_fields if f.field_name == field_name), None)
            
            if not field:
                if not schema.allow_additional_fields:
                    errors.append({
                        "field": field_name,
                        "message": f"{field_name} is not defined in schema"
                    })
                continue
            
            # Skip null/empty for non-required fields
            if not field.is_required and (value is None or value == ''):
                continue
            
            # Type validation
            error = self._validate_field_value(field, value)
            if error:
                errors.append({"field": field_name, "message": error})
        
        return errors
    
    def _validate_field_value(self, field: SchemaField, value: Any) -> Optional[str]:
        """Validate a single field value"""
        
        # Type checking and conversion
        try:
            if field.field_type == 'integer':
                int(value)
            elif field.field_type == 'float':
                float(value)
            elif field.field_type == 'boolean':
                if not isinstance(value, bool):
                    if isinstance(value, str) and value.lower() not in ('true', 'false', '0', '1', 'yes', 'no'):
                        return f"{field.field_name} must be a boolean"
        except (ValueError, TypeError):
            return f"{field.field_name} must be a valid {field.field_type}"
        
        # Constraint validation
        if field.constraints:
            error = self._check_constraint_violation(value, field.field_type, field.constraints)
            if error:
                return f"{field.field_name}: {error}"
        
        return None
