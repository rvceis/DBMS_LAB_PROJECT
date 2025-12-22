"""
Data Import Service
Handles parsing and importing data from multiple formats
"""
import csv
import json
import io
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re


class DataImportService:
    """Parse and import data from various formats"""
    
    def detect_format(self, content: str) -> str:
        """
        Auto-detect data format
        
        Returns: 'json', 'csv', 'tsv', 'plain', or 'unknown'
        """
        content = content.strip()
        
        # Try JSON first
        if (content.startswith('{') or content.startswith('[')) and (content.endswith('}') or content.endswith(']')):
            try:
                json.loads(content)
                return 'json'
            except:
                pass
        
        # Check for CSV/TSV patterns
        lines = content.split('\n')
        if len(lines) > 1:
            first_line = lines[0]
            
            # Count delimiters
            comma_count = first_line.count(',')
            tab_count = first_line.count('\t')
            pipe_count = first_line.count('|')
            semicolon_count = first_line.count(';')
            
            # Determine delimiter
            if tab_count > comma_count and tab_count > 0:
                return 'tsv'
            elif comma_count > 0:
                return 'csv'
            elif pipe_count > comma_count:
                return 'pipe'
            elif semicolon_count > comma_count:
                return 'semicolon'
        
        # Check for key-value pairs
        if re.search(r'\w+\s*[:=]\s*.+', content):
            return 'keyvalue'
        
        return 'unknown'
    
    def parse_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON data"""
        data = json.loads(content)
        
        # If single object, wrap in array
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("JSON must be object or array")
    
    def parse_csv(self, content: str, delimiter: str = ',') -> List[Dict[str, Any]]:
        """Parse CSV/TSV/delimited data"""
        if delimiter == 'tab':
            delimiter = '\t'
        elif delimiter == 'pipe':
            delimiter = '|'
        elif delimiter == 'semicolon':
            delimiter = ';'
        
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        return list(reader)
    
    def parse_keyvalue(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse key-value format like:
        name: John
        age: 30
        email: john@example.com
        ---
        name: Jane
        age: 25
        """
        records = []
        current_record = {}
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Empty line or separator - save current record
            if not line or line == '---':
                if current_record:
                    records.append(current_record)
                    current_record = {}
                continue
            
            # Parse key: value or key = value
            match = re.match(r'([^:=]+)\s*[:=]\s*(.+)', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                current_record[key] = value
        
        # Add last record
        if current_record:
            records.append(current_record)
        
        return records
    
    def parse_plain_text(self, content: str, schema_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Parse plain text by splitting on newlines and mapping to schema fields
        Useful for simple lists
        """
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not schema_fields:
            # Create generic field
            return [{'value': line} for line in lines]
        
        # Map to first field
        primary_field = schema_fields[0]
        return [{primary_field: line} for line in lines]
    
    def auto_parse(self, content: str, schema_fields: List[str] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Automatically detect format and parse data
        
        Returns: (format_detected, parsed_data)
        """
        format_type = self.detect_format(content)
        
        if format_type == 'json':
            data = self.parse_json(content)
        elif format_type == 'csv':
            data = self.parse_csv(content, ',')
        elif format_type == 'tsv':
            data = self.parse_csv(content, '\t')
        elif format_type == 'pipe':
            data = self.parse_csv(content, '|')
        elif format_type == 'semicolon':
            data = self.parse_csv(content, ';')
        elif format_type == 'keyvalue':
            data = self.parse_keyvalue(content)
        else:
            # Fall back to plain text
            data = self.parse_plain_text(content, schema_fields or [])
        
        return format_type, data
    
    def validate_against_schema(self, data: List[Dict[str, Any]], schema_fields: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Validate and type-cast data against schema
        
        Returns: (valid_records, errors)
        """
        valid_records = []
        errors = []
        
        for idx, record in enumerate(data):
            validated_record = {}
            record_errors = []
            
            for field in schema_fields:
                field_name = field['field_name']
                field_type = field['field_type']
                is_required = field.get('is_required', False)
                
                # Get value from record
                value = record.get(field_name)
                
                # Check required
                if is_required and (value is None or value == ''):
                    record_errors.append(f"Record {idx + 1}: '{field_name}' is required")
                    continue
                
                # Skip if empty and not required
                if value is None or value == '':
                    validated_record[field_name] = None
                    continue
                
                # Type casting
                try:
                    if field_type == 'integer':
                        validated_record[field_name] = int(value)
                    elif field_type == 'float':
                        validated_record[field_name] = float(value)
                    elif field_type == 'boolean':
                        if isinstance(value, bool):
                            validated_record[field_name] = value
                        else:
                            lower_val = str(value).lower()
                            validated_record[field_name] = lower_val in ('true', '1', 'yes', 'y')
                    elif field_type == 'date':
                        # Try parsing date
                        if isinstance(value, str):
                            validated_record[field_name] = value  # Let backend handle date parsing
                        else:
                            validated_record[field_name] = str(value)
                    elif field_type in ('json', 'array', 'object'):
                        if isinstance(value, str):
                            validated_record[field_name] = json.loads(value)
                        else:
                            validated_record[field_name] = value
                    else:  # string
                        validated_record[field_name] = str(value)
                except Exception as e:
                    record_errors.append(f"Record {idx + 1}: '{field_name}' - {str(e)}")
            
            if record_errors:
                errors.extend(record_errors)
            else:
                valid_records.append(validated_record)
        
        return valid_records, errors
    
    def suggest_field_mapping(self, data: List[Dict[str, Any]], schema_fields: List[Dict]) -> Dict[str, str]:
        """
        Suggest mapping from data fields to schema fields
        
        Returns: {data_field: schema_field}
        """
        if not data:
            return {}
        
        data_fields = list(data[0].keys())
        schema_field_names = [f['field_name'] for f in schema_fields]
        
        mapping = {}
        
        for data_field in data_fields:
            # Exact match
            if data_field in schema_field_names:
                mapping[data_field] = data_field
                continue
            
            # Case-insensitive match
            lower_data = data_field.lower()
            for schema_field in schema_field_names:
                if schema_field.lower() == lower_data:
                    mapping[data_field] = schema_field
                    break
            
            # Fuzzy match (contains)
            if data_field not in mapping:
                for schema_field in schema_field_names:
                    if lower_data in schema_field.lower() or schema_field.lower() in lower_data:
                        mapping[data_field] = schema_field
                        break
        
        return mapping
