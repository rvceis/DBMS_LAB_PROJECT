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


class SchemaModel(db.Model):
    __tablename__ = "schemas"
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    schema_json = db.Column(db.JSON, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MetadataRecord(db.Model):
    __tablename__ = "metadata_records"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, default="Unnamed Record")
    schema_id = db.Column(db.Integer, db.ForeignKey("schemas.id"), nullable=True)
    asset_type_id = db.Column(db.Integer, db.ForeignKey("asset_types.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    metadata_json = db.Column(db.JSON, nullable=False)
    tag = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChangeLog(db.Model):
    __tablename__ = "change_logs"
    id = db.Column(db.Integer, primary_key=True)
    schema_id = db.Column(db.Integer, db.ForeignKey("schemas.id"), nullable=True)
    change_type = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=True)
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
