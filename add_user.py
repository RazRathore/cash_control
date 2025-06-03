from app import app, db
from models import User

def create_user(username, password, name, department, role='user'):
    """Create a new user with the specified role"""
    with app.app_context():
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print(f"User '{username}' already exists!")
            return False
            
        # Create new user
        user = User(
            username=username,
            name=name,
            department=department,
            role=role
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            print(f"User '{username}' created successfully with role '{role}'")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {str(e)}")
            return False

if __name__ == '__main__':
    # Create a regular user without access to expenses
    create_user(
        username='staff',
        password='staff123',
        name='Staff Member',
        department='Operations',
        role='user'  # Regular user role
    )
