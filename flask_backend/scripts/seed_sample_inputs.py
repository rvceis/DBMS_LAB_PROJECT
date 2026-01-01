import os, sys
# Ensure project root is on path so `app` package can be imported when running from scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.extensions import db
from app.models import SchemaModel, MetadataRecord
from app.services.schema_manager import SchemaManager
import json

app = create_app()

samples = [
    # Raw Data Assets - CSV
    {
        "name": "training_tabular_1",
        "asset_type": None,
        "raw": "id,label,value\n1,cat,0.87\n2,dog,0.92\n",
        "format": "csv",
    },
    # Operational Inputs - user action log
    {
        "name": "user_action_upload",
        "asset_type": None,
        "raw": json.dumps({"user":"Akash","action":"upload","asset":"dataset_v1.csv","timestamp":"2025-12-31T01:12:00Z"}),
        "format": "json",
    },
    # Schema & Configuration Inputs - JSON Schema
    {
        "name": "schema_definition_sample",
        "asset_type": None,
        "raw": json.dumps({
            "type":"object",
            "properties":{
                "title":{"type":"string"},
                "author":{"type":"string"},
                "date_created":{"type":"string","format":"date-time"}
            }
        }),
        "format": "json",
    },
    # Model Experiment Input - experiment config
    {
        "name": "experiment_config_1",
        "asset_type": None,
        "raw": json.dumps({"epochs":20,"batch_size":32,"optimizer":"Adam","learning_rate":0.001}),
        "format": "json",
    },
    # External System Input - API response
    {
        "name": "weather_api_response",
        "asset_type": None,
        "raw": json.dumps({"weather":"sunny","temperature":28.5,"city":"Bengaluru"}),
        "format": "json",
    },
    # Governance input - retention policy
    {
        "name": "retention_policy_sample",
        "asset_type": None,
        "raw": json.dumps({"dataset":"Animal Images v1","retention_days":365}),
        "format": "json",
    }
]

with app.app_context():
    print("Seeding sample inputs into MetaDB...")
    manager = SchemaManager()
    # Ensure we have an asset_type to attach the schema to
    from app.models import AssetType
    at = AssetType.query.first()
    if not at:
        at = AssetType(name='Dataset')
        db.session.add(at)
        db.session.commit()

    # Create or reuse a RawData schema
    raw_schema = SchemaModel.query.filter_by(name="RawData").first()
    if not raw_schema:
        print("Creating RawData schema...")
        raw_schema = manager.create_schema(
            name="RawData",
            asset_type_id=at.id,
            fields=[],
            user_id=0,
            allow_additional_fields=True
        )
    else:
        print("Using existing RawData schema (id=%s)" % raw_schema.id)

    for s in samples:
        print(f"Inserting sample: {s['name']}")
        # Store raw string in raw_data and try to parse structured metadata_json if JSON
        metadata_json = None
        if s['format'] == 'json':
            try:
                metadata_json = json.loads(s['raw'])
            except Exception:
                metadata_json = None
        r = MetadataRecord(
            name=s['name'],
            schema_id=raw_schema.id,
            asset_type_id=s['asset_type'],
            metadata_json=metadata_json,
            raw_data=s['raw'],
            created_by=None
        )
        db.session.add(r)
    db.session.commit()
    print("Seeding completed.")
