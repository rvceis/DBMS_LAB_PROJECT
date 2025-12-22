"""
Migration to add report tables

Run with: python migrate_db.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask_backend.app import create_app
from flask_backend.app.extensions import db

app = create_app()

with app.app_context():
    # Import models to ensure they're registered
    from flask_backend.app.models import ReportTemplate, ReportExecution
    
    print("Creating report tables...")
    db.create_all()
    print("✅ Report tables created successfully!")
    
    # Create reports directory
    reports_dir = os.path.join(os.path.dirname(__file__), 'instance', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    print(f"✅ Reports directory created: {reports_dir}")
