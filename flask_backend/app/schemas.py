from .extensions import ma
from marshmallow import fields, validate


class UserSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    role = fields.Str()


class AssetTypeSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)


class SchemaModelSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    version = fields.Int()
    schema_json = fields.Dict()
    created_by = fields.Int()


class MetadataRecordSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    schema_id = fields.Int()
    asset_type_id = fields.Int()
    metadata_json = fields.Dict(required=True)
    tag = fields.Str()

class ChagneLog(ma.Schema):
    chagne_id=fields.Int(dump_only=True)
    change_type=fields.Str()


