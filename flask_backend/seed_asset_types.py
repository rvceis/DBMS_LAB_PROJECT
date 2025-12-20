"""
Seed default asset types into the database.
Run this once to create common asset types.
"""
from app import create_app
from app.extensions import db
from app.models import AssetType

app = create_app()

default_types = [
    "Image",
    "Video",
    "Document",
    "Audio",
    "PDF",
    "Spreadsheet",
    "Presentation",
    "Archive",
    "Code",
    "Dataset",
]

with app.app_context():
    print("Seeding default asset types...")
    for type_name in default_types:
        existing = AssetType.query.filter_by(name=type_name).first()
        if not existing:
            asset_type = AssetType(name=type_name)
            db.session.add(asset_type)
            print(f"  ✓ Added: {type_name}")
        else:
            print(f"  - Already exists: {type_name}")
    
    db.session.commit()
    print("\n✓ Default asset types seeded successfully!")
    
    # Show count
    count = AssetType.query.count()
    print(f"Total asset types: {count}")
