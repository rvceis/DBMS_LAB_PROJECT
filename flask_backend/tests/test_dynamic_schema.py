import os
import json
import pytest
from app import create_app
from app.extensions import db
from app.models import User, AssetType, SchemaModel, SchemaField, MetadataRecord, FieldValue
from app.services.schema_manager import SchemaManager


@pytest.fixture()
def app():
    # Configure test app with in-memory SQLite BEFORE app creation
    os.environ["FLASK_ENV"] = "development"
    os.environ["DATABASE_URL"] = "sqlite://"
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_dynamic_schema_crud(app):
    with app.app_context():
        # Seed a user and asset type
        user = User(username="tester", email="t@example.com", password_hash="x", role="admin")
        db.session.add(user)
        db.session.flush()
        asset = AssetType(name="Image")
        db.session.add(asset)
        db.session.commit()

        manager = SchemaManager()
        # Create schema
        schema = manager.create_schema(
            name="ImageMeta",
            asset_type_id=asset.id,
            fields=[
                {"name": "title", "type": "string", "required": True, "default": "Untitled"},
                {"name": "width", "type": "integer"},
                {"name": "height", "type": "integer"},
            ],
            user_id=user.id,
        )
        assert schema.id is not None
        assert len(schema.fields) == 3

        # Add field
        f = manager.add_field(schema.id, "author", "string", user.id, is_required=False)
        assert f.field_name == "author"

        # Create metadata record with values
        record = MetadataRecord(name="img1", schema_id=schema.id, asset_type_id=asset.id, created_by=user.id)
        db.session.add(record)
        db.session.flush()

        # Assign values
        fields = {sf.field_name: sf for sf in SchemaField.query.filter_by(schema_id=schema.id, is_deleted=False).all()}
        v_title = FieldValue(record_id=record.id, schema_field_id=fields["title"].id)
        v_title.schema_field = fields["title"]
        v_title.set_value("Sample")
        db.session.add(v_title)
        v_w = FieldValue(record_id=record.id, schema_field_id=fields["width"].id)
        v_w.schema_field = fields["width"]
        v_w.set_value(800)
        db.session.add(v_w)
        db.session.commit()

        # Verify values
        saved = MetadataRecord.query.get(record.id)
        out = saved.to_dict(include_values=True)
        assert out["values"]["title"] == "Sample"
        assert out["values"]["width"] == 800


def test_versioning_and_rollback(app):
    with app.app_context():
        user = User(username="tester2", email="t2@example.com", password_hash="x", role="admin")
        db.session.add(user)
        db.session.flush()
        asset = AssetType(name="Doc")
        db.session.add(asset)
        db.session.commit()

        manager = SchemaManager()
        schema = manager.create_schema(
            name="DocMeta",
            asset_type_id=asset.id,
            fields=[{"name": "title", "type": "string"}],
            user_id=user.id,
        )

        # Add and then remove field (soft)
        manager.add_field(schema.id, "pages", "integer", user.id)
        removed = manager.remove_field(schema.id, "pages", user.id, permanent=False)
        assert removed is True

        # Ensure field flagged deleted
        sf = SchemaField.query.filter_by(schema_id=schema.id, field_name="pages").first()
        assert sf.is_deleted is True
