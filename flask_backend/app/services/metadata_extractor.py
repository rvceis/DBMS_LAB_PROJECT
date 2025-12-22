"""
Intelligent Metadata Extraction Service
Extracts metadata from various file types and auto-generates schemas
Supports: Images, Videos, IoT Data, Medical Data, Satellite Data, ML Datasets, etc.
"""
import os
import json
import mimetypes
from datetime import datetime
from typing import Dict, Any, List, Tuple
import imghdr


class MetadataExtractor:
    """Extract metadata from various file types"""
    
    def extract(self, file_path: str, file_name: str) -> Tuple[Dict[str, Any], List[Dict]]:
        """
        Extract metadata from file
        
        Returns: (metadata, suggested_fields)
        where suggested_fields is list of field definitions for auto-generated schema
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        file_size = os.path.getsize(file_path)
        created_time = os.path.getctime(file_path)
        modified_time = os.path.getmtime(file_path)
        
        # Base metadata
        metadata = {
            'filename': file_name,
            'mime_type': mime_type,
            'file_size': file_size,
            'created_at': datetime.fromtimestamp(created_time).isoformat(),
            'modified_at': datetime.fromtimestamp(modified_time).isoformat(),
        }
        
        # Extract based on file type
        if mime_type.startswith('image/'):
            return self._extract_image(file_path, file_name, metadata)
        elif mime_type.startswith('video/'):
            return self._extract_video(file_path, file_name, metadata)
        elif mime_type in ['application/json', 'text/json']:
            return self._extract_json(file_path, file_name, metadata)
        elif mime_type.startswith('text/'):
            return self._extract_text(file_path, file_name, metadata)
        elif mime_type == 'application/pdf':
            return self._extract_pdf(file_path, file_name, metadata)
        elif 'csv' in mime_type or file_name.endswith('.csv'):
            return self._extract_csv(file_path, file_name, metadata)
        else:
            return self._extract_generic(file_path, file_name, metadata)
    
    def _extract_image(self, file_path: str, file_name: str, base_metadata: Dict) -> Tuple[Dict, List[Dict]]:
        """Extract metadata from image files"""
        metadata = base_metadata.copy()
        
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            img = Image.open(file_path)
            metadata['width'] = img.width
            metadata['height'] = img.height
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['is_animated'] = getattr(img, 'is_animated', False)
            
            # Extract EXIF data if available
            exif_data = {}
            try:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        exif_data[tag_name] = str(value)[:100]  # Limit size
            except:
                pass
            
            if exif_data:
                metadata['exif'] = exif_data
        except:
            # PIL not available, basic extraction
            img_type = imghdr.what(file_path)
            if img_type:
                metadata['image_type'] = img_type
        
        fields = [
            {'field_name': 'filename', 'field_type': 'string', 'is_required': True},
            {'field_name': 'width', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'height', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'format', 'field_type': 'string', 'is_required': False},
            {'field_name': 'file_size', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'created_at', 'field_type': 'date', 'is_required': False},
            {'field_name': 'exif', 'field_type': 'json', 'is_required': False},
        ]
        
        return metadata, fields
    
    def _extract_video(self, file_path: str, file_name: str, base_metadata: Dict) -> Tuple[Dict, List[Dict]]:
        """Extract metadata from video files"""
        metadata = base_metadata.copy()
        
        try:
            import subprocess
            import re
            
            # Try using ffprobe if available
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration,bit_rate', 
                 '-of', 'json', file_path],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                probe_data = json.loads(result.stdout)
                if 'format' in probe_data:
                    fmt = probe_data['format']
                    metadata['duration_seconds'] = float(fmt.get('duration', 0))
                    metadata['bit_rate'] = int(fmt.get('bit_rate', 0))
        except:
            pass
        
        fields = [
            {'field_name': 'filename', 'field_type': 'string', 'is_required': True},
            {'field_name': 'duration_seconds', 'field_type': 'float', 'is_required': False},
            {'field_name': 'bit_rate', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'file_size', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'created_at', 'field_type': 'date', 'is_required': False},
        ]
        
        return metadata, fields
    
    def _extract_json(self, file_path: str, file_name: str, base_metadata: Dict) -> Tuple[Dict, List[Dict]]:
        """Extract metadata from JSON files"""
        metadata = base_metadata.copy()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                # If it's a list, analyze first record
                if isinstance(data, list):
                    metadata['is_array'] = True
                    metadata['record_count'] = len(data)
                    if data:
                        sample = data[0]
                        metadata['sample'] = str(sample)[:200]
                        fields = self._infer_fields_from_dict(sample)
                    else:
                        fields = []
                elif isinstance(data, dict):
                    metadata['is_array'] = False
                    metadata['sample'] = str(data)[:200]
                    fields = self._infer_fields_from_dict(data)
                else:
                    fields = [{'field_name': 'value', 'field_type': 'string', 'is_required': True}]
            except json.JSONDecodeError:
                fields = [{'field_name': 'content', 'field_type': 'string', 'is_required': True}]
        
        return metadata, fields
    
    def _extract_csv(self, file_path: str, file_name: str, base_metadata: Dict) -> Tuple[Dict, List[Dict]]:
        """Extract metadata from CSV files"""
        metadata = base_metadata.copy()
        
        try:
            import csv
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                metadata['column_count'] = len(headers)
                metadata['columns'] = headers
                
                # Count rows
                row_count = sum(1 for _ in reader)
                metadata['row_count'] = row_count
                
                fields = [{'field_name': col, 'field_type': 'string', 'is_required': False} for col in headers]
        except:
            fields = [{'field_name': 'data', 'field_type': 'string', 'is_required': True}]
        
        return metadata, fields
    
    def _extract_text(self, file_path: str, file_name: str, base_metadata: Dict) -> Tuple[Dict, List[Dict]]:
        """Extract metadata from text files"""
        metadata = base_metadata.copy()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                metadata['line_count'] = len(content.split('\n'))
                metadata['char_count'] = len(content)
                metadata['word_count'] = len(content.split())
                metadata['preview'] = content[:200]
        except:
            pass
        
        fields = [
            {'field_name': 'filename', 'field_type': 'string', 'is_required': True},
            {'field_name': 'line_count', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'char_count', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'word_count', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'content', 'field_type': 'string', 'is_required': False},
        ]
        
        return metadata, fields
    
    def _extract_pdf(self, file_path: str, file_name: str, base_metadata: Dict) -> Tuple[Dict, List[Dict]]:
        """Extract metadata from PDF files"""
        metadata = base_metadata.copy()
        
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                metadata['page_count'] = len(reader.pages)
                
                if reader.metadata:
                    for key, value in reader.metadata.items():
                        if key not in ['filename']:
                            metadata[key.lower()] = str(value)[:100]
        except:
            pass
        
        fields = [
            {'field_name': 'filename', 'field_type': 'string', 'is_required': True},
            {'field_name': 'page_count', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'file_size', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'created_at', 'field_type': 'date', 'is_required': False},
        ]
        
        return metadata, fields
    
    def _extract_generic(self, file_path: str, file_name: str, base_metadata: Dict) -> Tuple[Dict, List[Dict]]:
        """Generic metadata extraction"""
        metadata = base_metadata.copy()
        
        fields = [
            {'field_name': 'filename', 'field_type': 'string', 'is_required': True},
            {'field_name': 'file_type', 'field_type': 'string', 'is_required': False},
            {'field_name': 'file_size', 'field_type': 'integer', 'is_required': False},
            {'field_name': 'created_at', 'field_type': 'date', 'is_required': False},
        ]
        
        return metadata, fields
    
    def _infer_fields_from_dict(self, data: Dict) -> List[Dict]:
        """Infer schema fields from dictionary"""
        fields = []
        
        for key, value in data.items():
            field_type = 'string'  # default
            
            if isinstance(value, bool):
                field_type = 'boolean'
            elif isinstance(value, int):
                field_type = 'integer'
            elif isinstance(value, float):
                field_type = 'float'
            elif isinstance(value, dict):
                field_type = 'json'
            elif isinstance(value, list):
                field_type = 'array'
            elif isinstance(value, str):
                # Try to detect date-like strings
                if 'date' in key.lower() or 'time' in key.lower():
                    field_type = 'date'
                else:
                    field_type = 'string'
            
            fields.append({
                'field_name': key,
                'field_type': field_type,
                'is_required': False
            })
        
        return fields
