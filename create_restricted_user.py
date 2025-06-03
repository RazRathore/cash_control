from app import app, db
from models import User

def create_restricted_user():
    with app.app_context():
        # Check if the user already exists
        if User.query.filter_by(username='staff').first():
            print("User 'staff' already exists!")
            return False
            
        # Create new restricted user
        user = User(
            username='staff',
            name='Staff Member',
            department='Operations',
            role='user'  # Regular user role with no special access
        )
        user.set_password('staff123')
        
        try:
            db.session.add(user)
            db.session.commit()
            print("Restricted user created successfully!")
            print("Username: staff")
            print("Password: staff123")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {str(e)}")
            return False

if __name__ == '__main__':
    create_restricted_user()
