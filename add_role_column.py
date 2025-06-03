import sqlite3
from app import app, db
from models import User

def add_role_column():
    # Connect to the SQLite database
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the role column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'role' not in columns:
            # Add the role column with a default value of 'user'
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL
            ''')
            conn.commit()
            print("Successfully added 'role' column to users table")
            
            # Update existing users to have appropriate roles
            # Default admin user will be 'admin', others will be 'user'
            cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")
            cursor.execute("UPDATE users SET role = 'user' WHERE username = 'staff'")
            conn.commit()
            print("Updated user roles")
        else:
            print("'role' column already exists in users table")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    with app.app_context():
        add_role_column()
