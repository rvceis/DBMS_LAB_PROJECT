"""
Report Query Builder Service
Builds queries from report configurations
"""
from typing import List, Dict, Any
from sqlalchemy import and_, or_
from ..models import MetadataRecord, SchemaField, FieldValue, SchemaModel
from ..extensions import db


class ReportQueryBuilder:
    """Build queries from report configuration"""
    
    def build_query(self, query_config: dict, schema: SchemaModel):
        """
        Build SQLAlchemy query from config
        
        Args:
            query_config: {
                "fields": ["field1", "field2"],
                "filters": [...],
                "sort": [...],
                "limit": 1000
            }
            schema: SchemaModel instance
        
        Returns:
            SQLAlchemy query
        """
        # Base query
        query = db.session.query(MetadataRecord).filter_by(schema_id=schema.id)
        
        # Apply filters
        for filter_def in query_config.get('filters', []):
            query = self._apply_filter(query, filter_def, schema)
        
        # Apply sorting
        for sort_def in query_config.get('sort', []):
            query = self._apply_sort(query, sort_def, schema)
        
        # Limit
        limit = query_config.get('limit', 10000)
        if limit:
            query = query.limit(limit)
        
        return query
    
    def _apply_filter(self, query, filter_def: dict, schema: SchemaModel):
        """
        Apply filter to query
        
        filter_def: {
            "field": "status",
            "operator": "eq|ne|gt|lt|gte|lte|in|contains|between",
            "value": "active"
        }
        """
        field_name = filter_def.get('field')
        operator = filter_def.get('operator', 'eq')
        value = filter_def.get('value')
        
        # Special case: filter on metadata record fields
        if field_name in ['id', 'name', 'created_at', 'updated_at']:
            return self._apply_record_field_filter(query, field_name, operator, value)
        
        # Filter on dynamic fields
        field = next((f for f in schema.fields if f.field_name == field_name and not f.is_deleted), None)
        if not field:
            return query
        
        # Join FieldValue table
        field_alias = db.aliased(FieldValue)
        query = query.join(field_alias, MetadataRecord.id == field_alias.record_id)
        query = query.filter(field_alias.schema_field_id == field.id)
        
        # Apply operator-specific conditions
        if operator == 'eq':
            query = query.filter(self._get_value_column(field_alias, field.field_type) == value)
        elif operator == 'ne':
            query = query.filter(self._get_value_column(field_alias, field.field_type) != value)
        elif operator == 'gt':
            query = query.filter(self._get_value_column(field_alias, field.field_type) > value)
        elif operator == 'lt':
            query = query.filter(self._get_value_column(field_alias, field.field_type) < value)
        elif operator == 'gte':
            query = query.filter(self._get_value_column(field_alias, field.field_type) >= value)
        elif operator == 'lte':
            query = query.filter(self._get_value_column(field_alias, field.field_type) <= value)
        elif operator == 'in':
            query = query.filter(self._get_value_column(field_alias, field.field_type).in_(value))
        elif operator == 'contains':
            query = query.filter(self._get_value_column(field_alias, field.field_type).ilike(f'%{value}%'))
        elif operator == 'between':
            if isinstance(value, list) and len(value) == 2:
                query = query.filter(
                    self._get_value_column(field_alias, field.field_type).between(value[0], value[1])
                )
        
        return query
    
    def _apply_record_field_filter(self, query, field_name: str, operator: str, value):
        """Apply filter on MetadataRecord fields"""
        field_col = getattr(MetadataRecord, field_name, None)
        if not field_col:
            return query
        
        if operator == 'eq':
            return query.filter(field_col == value)
        elif operator == 'ne':
            return query.filter(field_col != value)
        elif operator == 'gt':
            return query.filter(field_col > value)
        elif operator == 'lt':
            return query.filter(field_col < value)
        elif operator == 'gte':
            return query.filter(field_col >= value)
        elif operator == 'lte':
            return query.filter(field_col <= value)
        elif operator == 'in':
            return query.filter(field_col.in_(value))
        elif operator == 'contains':
            return query.filter(field_col.ilike(f'%{value}%'))
        
        return query
    
    def _apply_sort(self, query, sort_def: dict, schema: SchemaModel):
        """
        Apply sorting
        
        sort_def: {
            "field": "created_at",
            "direction": "asc|desc"
        }
        """
        field_name = sort_def.get('field')
        direction = sort_def.get('direction', 'asc')
        
        # Sort on record fields
        if field_name in ['id', 'name', 'created_at', 'updated_at']:
            field_col = getattr(MetadataRecord, field_name)
            return query.order_by(field_col.desc() if direction == 'desc' else field_col.asc())
        
        # For dynamic fields, sorting is more complex - skip for now
        return query
    
    def _get_value_column(self, field_value_alias, field_type: str):
        """Get the appropriate value column based on field type"""
        if field_type in ['integer']:
            return field_value_alias.value_int
        elif field_type in ['float']:
            return field_value_alias.value_float
        elif field_type in ['boolean']:
            return field_value_alias.value_bool
        elif field_type in ['date']:
            return field_value_alias.value_date
        elif field_type in ['json', 'array', 'object']:
            return field_value_alias.value_json
        else:  # string, default
            return field_value_alias.value_text
    
    def execute_and_format(self, query, query_config: dict, schema: SchemaModel) -> List[Dict]:
        """Execute query and return formatted results"""
        records = query.all()
        
        # Extract requested fields
        fields = query_config.get('fields', [])
        if not fields:
            # If no fields specified, include all non-deleted fields
            fields = [f.field_name for f in schema.fields if not f.is_deleted]
        
        results = []
        for record in records:
            row = {
                'id': record.id,
                'name': record.name,
                'created_at': record.created_at.isoformat() if record.created_at else None,
            }
            
            # Get field values
            for field_name in fields:
                if field_name in ['id', 'name', 'created_at']:
                    continue  # Already included
                
                field = next((f for f in schema.fields if f.field_name == field_name and not f.is_deleted), None)
                if field:
                    value_obj = next((v for v in record.field_values if v.schema_field_id == field.id), None)
                    if value_obj:
                        row[field_name] = value_obj.get_value()
                    else:
                        row[field_name] = None
            
            results.append(row)
        
        return results
