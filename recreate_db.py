from app import app, db
from models import User
import os

def recreate_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all tables")
        
        # Create all tables
        db.create_all()
        print("Created all tables")
        
        # Create admin user
        admin = User(
            username='admin',
            name='Administrator',
            department='Administration',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("Created admin user")
        
        # Create staff user
        staff = User(
            username='staff',
            name='Staff Member',
            department='Operations',
            role='user'
        )
        staff.set_password('staff123')
        db.session.add(staff)
        print("Created staff user")
        
        # Commit changes
        db.session.commit()
        print("Database recreation complete")

if __name__ == '__main__':
    # Delete the database file if it exists
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'mining_ledger.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")
    
    # Recreate the database
    recreate_database()
