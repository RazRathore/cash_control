from wave import WAVE_FORMAT_PCM
from app import app, db
from models import User, Client, Transaction, WorkingStage
from flask_migrate import Migrate, upgrade
from sqlalchemy import inspect

def run_migrations():
    """Run database migrations and ensure all tables exist"""
    with app.app_context():
        # Check if migrations table exists
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # If no tables exist, create them all
        if not tables:
            print("No database tables found. Creating all tables...")
            db.create_all()
            
            # Create admin user
            admin = User(
                username='admin',
                name='Administrator',
                department='Administration'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Created admin user')
        else:
            # Check if we need to add new columns
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('clients')]
            
            # Add missing columns
            if 'near_village' not in columns or 'district' not in columns:
                print("Adding missing columns to clients table...")
                with db.engine.connect() as conn:
                    if 'near_village' not in columns:
                        conn.execute('ALTER TABLE clients ADD COLUMN near_village VARCHAR(50)')
                    if 'district' not in columns:
                        conn.execute('ALTER TABLE clients ADD COLUMN district VARCHAR(50)')
                print("Database schema updated successfully")
        print("Database has been reset and initialized with admin user!")
        print("Username: admin")
        print("Password: admin123")

if __name__ == '__main__':
    run_migrations()