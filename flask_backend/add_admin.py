"""
Add admin user to the database
"""
from app import create_app
from app.models import User
from app.extensions import db
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Check existing admins
    admins = User.query.filter_by(role='admin').all()
    print("=" * 50)
    print("EXISTING ADMIN USERS:")
    print("=" * 50)
    if admins:
        for admin in admins:
            print(f"  • {admin.username} ({admin.email}) - Role: {admin.role}")
    else:
        print("  No admin users found")
    
    print("\n" + "=" * 50)
    print("ADDING NEW ADMIN USER")
    print("=" * 50)
    
    # Check if user already exists
    existing = User.query.filter_by(email='agoundi720@gmail.com').first()
    if existing:
        print(f"❌ User with email {existing.email} already exists!")
        print(f"   Username: {existing.username}, Role: {existing.role}")
    else:
        # Create new admin user
        # Using a default password - user should change on first login
        default_password = "Akash@123456"
        
        new_admin = User(
            username='Akash',
            email='agoundi720@gmail.com',
            password_hash=generate_password_hash(default_password),
            role='admin'
        )
        db.session.add(new_admin)
        db.session.commit()
        print(f"✓ Admin user created successfully!")
        print(f"\n  Username: Akash")
        print(f"  Email: agoundi720@gmail.com")
        print(f"  Role: admin")
        print(f"  Temporary Password: {default_password}")
        print(f"\n⚠️  IMPORTANT: User should change password after first login!")
    
    print("=" * 50)
