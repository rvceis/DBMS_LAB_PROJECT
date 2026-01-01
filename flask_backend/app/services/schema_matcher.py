from typing import Optional, Tuple, List, Dict
from ..models import SchemaModel, SchemaField
from ..extensions import db


def _schema_score_from_fields(schema: SchemaModel, incoming_keys: List[str]) -> float:
    """Compute overlap score between incoming metadata keys and defined schema fields."""
    if not incoming_keys:
        return 0.0
    field_names = {f.field_name for f in schema.fields if not f.is_deleted}
    if not field_names:
        return 0.0
    keys_set = set(incoming_keys)
    common = keys_set.intersection(field_names)
    return len(common) / len(keys_set) if keys_set else 0.0


def _schema_score(schema_json: dict, metadata_json: dict) -> float:
    """Backward-compat: score using schema_json.properties vs metadata_json keys."""
    props = schema_json.get("properties", {}) if isinstance(schema_json, dict) else {}
    if not props:
        return 0.0
    meta_keys = set(metadata_json.keys()) if isinstance(metadata_json, dict) else set()
    if not meta_keys:
        return 0.0
    common = meta_keys.intersection(props.keys())
    return len(common) / len(meta_keys)


def find_best_schema_from_keys(
    incoming_keys: List[str],
    asset_type_id: Optional[int] = None,
    min_score: float = 0.6,
) -> Tuple[Optional[SchemaModel], float]:
    """Return best matching schema (field-based) optionally filtered by asset type."""
    q = SchemaModel.query
    if asset_type_id:
        q = q.filter(SchemaModel.asset_type_id == asset_type_id)
    schemas = q.all()
    best_schema = None
    best_score = 0.0
    for schema in schemas:
        score = _schema_score_from_fields(schema, incoming_keys)
        if score > best_score:
            best_schema = schema
            best_score = score
    if best_score >= min_score:
        return best_schema, best_score
    return None, 0.0


def create_schema_from_metadata(
    name: str,
    metadata: Dict,
    asset_type_id: int,
    user_id: Optional[int],
    allow_additional_fields: bool = True,
) -> SchemaModel:
    """Create a dynamic schema using SchemaManager based on metadata keys and inferred types."""
    from .schema_manager import SchemaManager


    def merge_types(existing_type, new_type):
        # Promote types according to hierarchy
        type_order = ['integer', 'float', 'string', 'object']
        if isinstance(existing_type, list):
            types = set(existing_type)
        else:
            types = {existing_type}
        types.add(new_type)
        # Promote to the most general type if needed
        for t in reversed(type_order):
            if t in types:
                return t if len(types) == 1 else list(types)
        return list(types)

    def infer_type(v):
        if isinstance(v, bool):
            return "boolean"
        if isinstance(v, int) and not isinstance(v, bool):
            return "integer"
        if isinstance(v, float):
            return "float"
        if isinstance(v, list):
            # Infer type of items
            if v:
                item_types = set(infer_type(item) for item in v)
                if len(item_types) == 1:
                    return f"array<{item_types.pop()}>"
                else:
                    return f"array<{','.join(sorted(item_types))}>"
            else:
                return "array<any>"
        if isinstance(v, dict):
            # Nested object: recursively infer subfields
            return {
                "type": "object",
                "fields": {k: infer_type(val) for k, val in v.items()}
            }
        return "string"

    # Build fields with type promotion/union
    fields = []
    observed_types = {}
    if isinstance(metadata, dict):
        for k, v in metadata.items():
            inferred = infer_type(v)
            if k in observed_types:
                inferred = merge_types(observed_types[k], inferred)
            observed_types[k] = inferred
            fields.append({
                "name": k,
                "type": inferred,
                "required": False
            })

    manager = SchemaManager()
    schema = manager.create_schema(
        name=name,
        asset_type_id=asset_type_id,
        fields=fields,
        user_id=user_id or 0,
        allow_additional_fields=allow_additional_fields,
    )
    return schema
