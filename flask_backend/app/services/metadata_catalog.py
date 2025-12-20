"""
MetadataCatalog - Centralized schema metadata management with caching
"""
import threading
from typing import Dict, List, Optional, Any
from functools import lru_cache
from datetime import datetime, timedelta
from ..models import SchemaModel, SchemaField, AssetType
from ..extensions import db


class MetadataCatalog:
    """
    Centralized catalog for schema metadata with intelligent caching
    """
    
    def __init__(self, cache_ttl: int = 300):
        """
        Args:
            cache_ttl: Cache time-to-live in seconds (default 5 minutes)
        """
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = cache_ttl
        self.lock = threading.RLock()
    
    def get_schema(self, schema_id: int, use_cache: bool = True) -> Optional[Dict]:
        """
        Get complete schema information
        
        Args:
            schema_id: Schema ID
            use_cache: Whether to use cache
        
        Returns:
            Schema dict with fields or None
        """
        cache_key = f"schema:{schema_id}"
        
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        # Load from database
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            return None
        
        schema_data = self._build_schema_dict(schema)
        
        # Cache it
        if use_cache:
            self._put_in_cache(cache_key, schema_data)
        
        return schema_data
    
    def get_schemas_by_asset_type(
        self,
        asset_type_id: int,
        active_only: bool = True,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Get all schemas for an asset type
        
        Args:
            asset_type_id: Asset type ID
            active_only: Return only active schemas
            use_cache: Whether to use cache
        
        Returns:
            List of schema dicts
        """
        cache_key = f"schemas:asset_type:{asset_type_id}:active:{active_only}"
        
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        # Load from database
        query = SchemaModel.query.filter_by(asset_type_id=asset_type_id)
        if active_only:
            query = query.filter_by(is_active=True)
        
        schemas = query.order_by(SchemaModel.version.desc()).all()
        schemas_data = [self._build_schema_dict(s) for s in schemas]
        
        # Cache it
        if use_cache:
            self._put_in_cache(cache_key, schemas_data)
        
        return schemas_data
    
    def get_field(self, schema_id: int, field_name: str) -> Optional[Dict]:
        """
        Get specific field information
        
        Args:
            schema_id: Schema ID
            field_name: Field name
        
        Returns:
            Field dict or None
        """
        field = SchemaField.query.filter_by(
            schema_id=schema_id,
            field_name=field_name,
            is_deleted=False
        ).first()
        
        if not field:
            return None
        
        return {
            'id': field.id,
            'name': field.field_name,
            'type': field.field_type,
            'required': field.is_required,
            'default': field.default_value,
            'constraints': field.constraints,
            'description': field.description,
            'order': field.order_index
        }
    
    def get_fields(
        self,
        schema_id: int,
        include_deleted: bool = False
    ) -> List[Dict]:
        """
        Get all fields for a schema
        
        Args:
            schema_id: Schema ID
            include_deleted: Include soft-deleted fields
        
        Returns:
            List of field dicts
        """
        cache_key = f"fields:{schema_id}:deleted:{include_deleted}"
        
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        query = SchemaField.query.filter_by(schema_id=schema_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        
        fields = query.order_by(SchemaField.order_index).all()
        fields_data = [self._build_field_dict(f) for f in fields]
        
        self._put_in_cache(cache_key, fields_data)
        
        return fields_data
    
    def field_exists(self, schema_id: int, field_name: str) -> bool:
        """Check if field exists in schema"""
        return SchemaField.query.filter_by(
            schema_id=schema_id,
            field_name=field_name,
            is_deleted=False
        ).count() > 0
    
    def get_asset_type(self, asset_type_id: int) -> Optional[Dict]:
        """Get asset type information"""
        cache_key = f"asset_type:{asset_type_id}"
        
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        asset_type = AssetType.query.get(asset_type_id)
        if not asset_type:
            return None
        
        data = asset_type.to_dict()
        self._put_in_cache(cache_key, data)
        
        return data
    
    def get_all_asset_types(self) -> List[Dict]:
        """Get all asset types"""
        cache_key = "asset_types:all"
        
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        asset_types = AssetType.query.all()
        data = [at.to_dict() for at in asset_types]
        
        self._put_in_cache(cache_key, data)
        
        return data
    
    def get_schema_statistics(self, schema_id: int) -> Dict:
        """
        Get usage statistics for a schema
        
        Args:
            schema_id: Schema ID
        
        Returns:
            Statistics dict
        """
        from ..models import MetadataRecord
        
        cache_key = f"stats:{schema_id}"
        
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        record_count = MetadataRecord.query.filter_by(schema_id=schema_id).count()
        field_count = SchemaField.query.filter_by(
            schema_id=schema_id,
            is_deleted=False
        ).count()
        
        stats = {
            'schema_id': schema_id,
            'record_count': record_count,
            'field_count': field_count,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        self._put_in_cache(cache_key, stats, ttl=60)  # Shorter TTL for stats
        
        return stats
    
    def invalidate_schema(self, schema_id: int):
        """Invalidate all cache entries for a schema"""
        with self.lock:
            keys_to_remove = []
            for key in self.cache.keys():
                if f":{schema_id}" in key or key.startswith(f"schema:{schema_id}"):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
    
    def invalidate_asset_type(self, asset_type_id: int):
        """Invalidate all cache entries for an asset type"""
        with self.lock:
            keys_to_remove = []
            for key in self.cache.keys():
                if f"asset_type:{asset_type_id}" in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
    
    def clear_cache(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.cache_timestamps.clear()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            return {
                'size': len(self.cache),
                'keys': list(self.cache.keys()),
                'ttl': self.cache_ttl
            }
    
    # Private methods
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check expiry
            timestamp = self.cache_timestamps.get(key)
            if timestamp:
                age = (datetime.utcnow() - timestamp).total_seconds()
                if age > self.cache_ttl:
                    # Expired
                    del self.cache[key]
                    del self.cache_timestamps[key]
                    return None
            
            return self.cache[key]
    
    def _put_in_cache(self, key: str, value: Any, ttl: Optional[int] = None):
        """Put value in cache"""
        with self.lock:
            self.cache[key] = value
            self.cache_timestamps[key] = datetime.utcnow()
    
    def _build_schema_dict(self, schema: SchemaModel) -> Dict:
        """Build complete schema dict"""
        return {
            'id': schema.id,
            'name': schema.name,
            'version': schema.version,
            'asset_type_id': schema.asset_type_id,
            'parent_schema_id': schema.parent_schema_id,
            'allow_additional_fields': schema.allow_additional_fields,
            'is_active': schema.is_active,
            'created_by': schema.created_by,
            'created_at': schema.created_at.isoformat() if schema.created_at else None,
            'fields': [self._build_field_dict(f) for f in schema.fields if not f.is_deleted],
            'field_count': len([f for f in schema.fields if not f.is_deleted])
        }
    
    def _build_field_dict(self, field: SchemaField) -> Dict:
        """Build field dict"""
        return {
            'id': field.id,
            'name': field.field_name,
            'type': field.field_type,
            'required': field.is_required,
            'default': field.default_value,
            'constraints': field.constraints,
            'description': field.description,
            'order': field.order_index,
            'deleted': field.is_deleted
        }


# Global instance
catalog = MetadataCatalog()
