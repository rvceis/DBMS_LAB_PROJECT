from app.models import User

u = User(username='alice', email='a@example.com', password_hash='x', role='viewer')
print('User created:', u.username, u.email, u.password_hash, u.role)
print('Has attrs:', hasattr(u,'username'), hasattr(u,'email'))
