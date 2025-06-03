from app import app, db
from models import User

def update_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='Administrator',
                department='Administration',
                role='admin'  # Add admin role
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Created admin user")
        
        # Create staff user if not exists
        staff = User.query.filter_by(username='staff').first()
        if not staff:
            staff = User(
                username='staff',
                name='Staff Member',
                department='Operations',
                role='user'  # Regular user role with restricted access
            )
            staff.set_password('staff123')
            db.session.add(staff)
            print("Created staff user")
        
        # Commit changes
        db.session.commit()
        print("Database updated successfully!")

if __name__ == '__main__':
    update_database()
