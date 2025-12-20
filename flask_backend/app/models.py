from datetime import datetime
from .extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="viewer")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "email": self.email, "role": self.role}


class AssetType(db.Model):
    __tablename__ = "asset_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    schemas = db.relationship('SchemaModel', backref='asset_type', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SchemaModel(db.Model):
    """Enhanced schema model with dynamic schema support"""
    __tablename__ = "schemas"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    asset_type_id = db.Column(db.Integer, db.ForeignKey("asset_types.id"), nullable=False)
    parent_schema_id = db.Column(db.Integer, db.ForeignKey("schemas.id"), nullable=True)
    allow_additional_fields = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    schema_json = db.Column(db.JSON, nullable=True)  # Kept for backward compatibility
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fields = db.relationship('SchemaField', backref='schema', lazy=True, cascade="all, delete-orphan")
    metadata_records = db.relationship('MetadataRecord', backref='schema', lazy=True)
    change_logs = db.relationship('ChangeLog', backref='schema', lazy=True)
    parent = db.relationship('SchemaModel', remote_side=[id], backref='children')
    
    def to_dict(self, include_fields=True):
        result = {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "asset_type_id": self.asset_type_id,
            "parent_schema_id": self.parent_schema_id,
            "allow_additional_fields": self.allow_additional_fields,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_fields:
            result["fields"] = [field.to_dict() for field in self.fields]
        return result


class SchemaField(db.Model):
    """Individual field definitions for dynamic schemas"""
    __tablename__ = "schema_fields"
    id = db.Column(db.Integer, primary_key=True)
    schema_id = db.Column(db.Integer, db.ForeignKey("schemas.id"), nullable=False)
    field_name = db.Column(db.String(128), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)  # string, integer, float, boolean, date, json, array
    is_required = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.String(255), nullable=True)
    constraints = db.Column(db.JSON, nullable=True)  # {"min": 0, "max": 100, "regex": "...", "enum": [...]}
    description = db.Column(db.Text, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)  # Soft delete for rollback safety
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    field_values = db.relationship('FieldValue', backref='schema_field', lazy=True)
    
    __table_args__ = (
        db.UniqueConstraint('schema_id', 'field_name', name='uq_schema_field'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "schema_id": self.schema_id,
            "field_name": self.field_name,
            "field_type": self.field_type,
            "is_required": self.is_required,
            "default_value": self.default_value,
            "constraints": self.constraints,
            "description": self.description,
            "is_deleted": self.is_deleted,
            "order_index": self.order_index
        }


class MetadataRecord(db.Model):
    """Metadata records using dynamic schema"""
    __tablename__ = "metadata_records"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, default="Unnamed Record")
    schema_id = db.Column(db.Integer, db.ForeignKey("schemas.id"), nullable=False)  # Now required!
    asset_type_id = db.Column(db.Integer, db.ForeignKey("asset_types.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    tag = db.Column(db.String(128), nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)  # Kept for backward compatibility
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    field_values = db.relationship('FieldValue', backref='metadata_record', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self, include_values=True):
        result = {
            "id": self.id,
            "name": self.name,
            "schema_id": self.schema_id,
            "asset_type_id": self.asset_type_id,
            "created_by": self.created_by,
            "tag": self.tag,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        if include_values:
            result["values"] = {fv.schema_field.field_name: fv.get_value() for fv in self.field_values}
        return result


class FieldValue(db.Model):
    """EAV (Entity-Attribute-Value) pattern for dynamic field storage"""
    __tablename__ = "field_values"
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("metadata_records.id"), nullable=False)
    schema_field_id = db.Column(db.Integer, db.ForeignKey("schema_fields.id"), nullable=False)
    
    # Type-specific columns for performance
    value_text = db.Column(db.Text, nullable=True)
    value_int = db.Column(db.Integer, nullable=True)
    value_float = db.Column(db.Float, nullable=True)
    value_bool = db.Column(db.Boolean, nullable=True)
    value_date = db.Column(db.DateTime, nullable=True)
    value_json = db.Column(db.JSON, nullable=True)  # For arrays and objects
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('record_id', 'schema_field_id', name='uq_record_field'),
    )
    
    def get_value(self):
        """Get the value based on field type"""
        field_type = self.schema_field.field_type
        if field_type == 'string':
            return self.value_text
        elif field_type == 'integer':
            return self.value_int
        elif field_type == 'float':
            return self.value_float
        elif field_type == 'boolean':
            return self.value_bool
        elif field_type == 'date':
            return self.value_date.isoformat() if self.value_date else None
        elif field_type in ('json', 'array', 'object'):
            return self.value_json
        return None
    
    def set_value(self, value):
        """Set the value based on field type"""
        field_type = self.schema_field.field_type
        # Clear all values first
        self.value_text = None
        self.value_int = None
        self.value_float = None
        self.value_bool = None
        self.value_date = None
        self.value_json = None
        
        # Set the appropriate value
        if value is None:
            return
        
        if field_type == 'string':
            self.value_text = str(value)
        elif field_type == 'integer':
            self.value_int = int(value)
        elif field_type == 'float':
            self.value_float = float(value)
        elif field_type == 'boolean':
            self.value_bool = bool(value)
        elif field_type == 'date':
            if isinstance(value, str):
                from dateutil import parser
                self.value_date = parser.parse(value)
            else:
                self.value_date = value
        elif field_type in ('json', 'array', 'object'):
            self.value_json = value


class ChangeLog(db.Model):
    """Enhanced change log for schema versioning"""
    __tablename__ = "change_logs"
    id = db.Column(db.Integer, primary_key=True)
    schema_id = db.Column(db.Integer, db.ForeignKey("schemas.id"), nullable=True)
    change_type = db.Column(db.String(64), nullable=False)  # created, updated, deleted, field_added, field_removed, etc.
    description = db.Column(db.Text, nullable=True)
    change_details = db.Column(db.JSON, nullable=True)  # Store detailed change information
    schema_snapshot = db.Column(db.JSON, nullable=True)  # Complete schema state at this point
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "schema_id": self.schema_id,
            "change_type": self.change_type,
            "description": self.description,
            "change_details": self.change_details,
            "changed_by": self.changed_by,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class SchemaVersion(db.Model):
    """Track complete schema versions for rollback"""
    __tablename__ = "schema_versions"
    id = db.Column(db.Integer, primary_key=True)
    schema_id = db.Column(db.Integer, db.ForeignKey("schemas.id"), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    schema_snapshot = db.Column(db.JSON, nullable=False)  # Complete schema with all fields
    change_summary = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('schema_id', 'version_number', name='uq_schema_version'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "schema_id": self.schema_id,
            "version_number": self.version_number,
            "schema_snapshot": self.schema_snapshot,
            "change_summary": self.change_summary,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
