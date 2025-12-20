from jsonschema import validate, ValidationError
from ..models import MetadataRecord, SchemaModel
from ..extensions import db


def validate_metadata_against_schema(metadata: dict, schema_id: int):
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return False, "schema not found"
    try:
        validate(instance=metadata, schema=schema.schema_json)
    except ValidationError as exc:
        return False, str(exc)
    return True, None


def create_metadata_record(metadata_json: dict, schema_id: int = None, asset_type_id: int = None, tag: str = None):
    if schema_id:
        ok, err = validate_metadata_against_schema(metadata_json, schema_id)
        if not ok:
            return None, err
    r = MetadataRecord(metadata_json=metadata_json, schema_id=schema_id, asset_type_id=asset_type_id, tag=tag)
    db.session.add(r)
    db.session.commit()
    return r, None
