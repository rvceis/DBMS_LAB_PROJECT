"""
Quick Database Viewer - See all data in the database
Run: python view_db.py
"""
from app import create_app
from app.models import User, SchemaModel, MetadataRecord, AssetType, ChangeLog
import json

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("DATABASE CONTENTS")
    print("="*80)
    
    # Users
    print("\n>>> USERS")
    users = User.query.all()
    if users:
        for u in users:
            print(f"  ID: {u.id}, Username: {u.username}, Email: {u.email}, Role: {u.role}")
    else:
        print("  (No users)")
    
    # Asset Types
    print("\n>>> ASSET TYPES")
    types = AssetType.query.all()
    if types:
        for t in types:
            print(f"  ID: {t.id}, Name: {t.name}")
    else:
        print("  (No asset types)")
    
    # Schemas
    print("\n>>> SCHEMAS")
    schemas = SchemaModel.query.all()
    if schemas:
        for s in schemas:
            creator = User.query.get(s.created_by)
            creator_name = creator.username if creator else "Unknown"
            print(f"  ID: {s.id}, Version: {s.version}, Created by: {creator_name}")
            print(f"    Schema JSON: {json.dumps(s.schema_json, indent=6)}")
    else:
        print("  (No schemas)")
    
    # Metadata Records
    print("\n>>> METADATA RECORDS")
    records = MetadataRecord.query.all()
    if records:
        for r in records:
            creator = User.query.get(r.created_by)
            creator_name = creator.username if creator else "Unknown"
            asset_type = AssetType.query.get(r.asset_type_id)
            asset_type_name = asset_type.name if asset_type else "None"
            print(f"  ID: {r.id}, Name: {r.name}")
            print(f"    Created by: {creator_name}, Asset Type: {asset_type_name}")
            print(f"    Tag: {r.tag}, Schema ID: {r.schema_id}")
            print(f"    Metadata: {json.dumps(r.metadata_json, indent=6)}")
    else:
        print("  (No metadata records)")
    
    # Change Log
    print("\n>>> CHANGE LOG")
    logs = ChangeLog.query.all()
    if logs:
        for log in logs:
            print(f"  ID: {log.id}, Type: {log.change_type}, Schema ID: {log.schema_id}")
            print(f"    Description: {log.description}")
    else:
        print("  (No change logs)")
    
    print("\n" + "="*80)
    print(f"Total Records: Users={len(users)}, Schemas={len(schemas)}, Metadata={len(records)}, AssetTypes={len(types)}")
    print("="*80 + "\n")
