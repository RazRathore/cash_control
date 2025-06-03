from app import app, db
from models import User, Client, Transaction, WorkingStage
from flask_migrate import Migrate, upgrade, migrate as flask_migrate, init as flask_migrate_init
from sqlalchemy import inspect, text
import os

def run_migrations():
    """Run database migrations and ensure all tables exist"""
    with app.app_context():
        # Initialize Flask-Migrate
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.exists(migrations_dir):
            print("Initializing migrations directory...")
            flask_migrate_init()
        
        # Create Migrate instance
        migrate = Migrate(app, db)
        
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
            print("Database initialized with admin user")
        else:
            print("Database tables already exist")
            
            # Check if transaction_type column exists in transactions table
            try:
                # This is a SQLite-specific check, adjust if using a different database
                result = db.session.execute(
                    text("PRAGMA table_info(transactions)")
                ).fetchall()
                columns = [row[1] for row in result]
                
                if 'transaction_type' not in columns:
                    print("Adding transaction_type column to transactions table...")
                    db.session.execute(
                        text("ALTER TABLE transactions ADD COLUMN transaction_type VARCHAR(20) DEFAULT 'client' NOT NULL")
                    )
                    db.session.commit()
                    print("Added transaction_type column to transactions table")
            except Exception as e:
                print(f"Error checking/adding transaction_type column: {str(e)}")
            
            # Try to run any pending migrations
            try:
                print("Running any pending migrations...")
                # Generate a new migration for the transaction_type field
                print("Generating migration for transaction_type field...")
                flask_migrate(message="Add transaction_type to Transaction model")
                # Apply the migration
                upgrade()
                print("Migrations completed successfully")
            except Exception as e:
                print(f"Error running migrations: {str(e)}")
                print("Continuing with existing database schema...")
        print("Database has been reset and initialized with admin user!")
        print("Username: admin")
        print("Password: admin123")

if __name__ == '__main__':
    run_migrations()