from app import app, db
from models import User

def remove_user(username):
    with app.app_context():
        # Find the user
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Delete the user
            db.session.delete(user)
            db.session.commit()
            print(f"User '{username}' has been successfully removed.")
            return True
        else:
            print(f"User '{username}' not found.")
            return False

if __name__ == '__main__':
    # Remove the test user
    remove_user('testuser')
    print("User removal process completed.")
