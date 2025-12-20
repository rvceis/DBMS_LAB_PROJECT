"""
One-time database initialization script.
Run this ONCE to create all tables in your PostgreSQL database.

Usage:
    python init_db.py
"""
from app import create_app
from app.extensions import db
from app.models import User, AssetType, SchemaModel, MetadataRecord, ChangeLog

app = create_app()

with app.app_context():
    print("Dropping existing tables (if any)...")
    # Use raw SQL to drop with CASCADE
    from sqlalchemy import text
    try:
        db.session.execute(text("DROP TABLE IF EXISTS change_logs CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS metadata_records CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS schemas CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS asset_types CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        db.session.commit()
        print("✓ Existing tables dropped")
    except Exception as e:
        print(f"Note: {e}")
        db.session.rollback()
    
    print("Creating all database tables...")
    # Import all models to ensure they're registered
    # SQLAlchemy will handle the correct creation order based on foreign keys
    db.create_all()
    
    print("✓ Database tables created successfully!")
    print("\nTables created:")
    print("  - users")
    print("  - asset_types")
    print("  - schemas")
    print("  - metadata_records")
    print("  - change_logs")
    print("\nYou can now run: python main.py")
