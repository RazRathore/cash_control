from app import app, db
from models import User

def create_user(username, password, name, department):
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists!")
        return
    
    # Create new user
    new_user = User(
        username=username,
        name=name,
        department=department
    )
    new_user.set_password(password)
    
    # Add to database
    db.session.add(new_user)
    db.session.commit()
    print(f"User '{username}' created successfully!")

if __name__ == '__main__':
    with app.app_context():
        # Create first user - Manager
        create_user(
            username='manager',
            password='manager123',
            name='Operations Manager',
            department='Management'
        )
        
        # Create second user - Accountant
        create_user(
            username='accountant',
            password='account123',
            name='Finance Accountant',
            department='Finance'
        )
        
        print("User creation completed.")
