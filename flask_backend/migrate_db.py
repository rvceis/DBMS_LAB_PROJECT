"""
Drop existing tables and recreate with new schema including created_by and name fields.
Run this ONCE to update the database with the new columns.
"""
from app import create_app
from app.extensions import db
from app.models import User, AssetType, SchemaModel, MetadataRecord, ChangeLog

app = create_app()

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    
    print("Creating all tables with new schema...")
    db.create_all()
    
    print("✓ Database recreated successfully with new schema!")
    print("\nNew fields added:")
    print("  - MetadataRecord.name: Meaningful name for each record")
    print("  - MetadataRecord.created_by: Track who created each record")
    print("\nYou can now run: python main.py")
