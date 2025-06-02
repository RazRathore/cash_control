from app import app, db
from models import Transaction, WorkingStage

def migrate_database():
    with app.app_context():
        # Create the working_stages table
        WorkingStage.__table__.create(db.engine, checkfirst=True)
        
        # Add new columns to transactions table if they don't exist
        # We'll use raw SQL since we can't use Flask-Migrate
        with db.engine.connect() as conn:
            # Check if columns exist
            result = conn.execute("""
                PRAGMA table_info(transactions);
            """).fetchall()
            
            columns = [row[1] for row in result]
            
            # Add columns if they don't exist
            if 'total_amount' not in columns:
                conn.execute("""
                    ALTER TABLE transactions ADD COLUMN total_amount INTEGER DEFAULT 0;
                """)
                
            if 'token_amount' not in columns:
                conn.execute("""
                    ALTER TABLE transactions ADD COLUMN token_amount INTEGER DEFAULT 0;
                """)
                
            if 'remaining_balance' not in columns:
                conn.execute("""
                    ALTER TABLE transactions ADD COLUMN remaining_balance INTEGER DEFAULT 0;
                """)
        
        db.session.commit()
        print("Database migration completed successfully!")

if __name__ == '__main__':
    migrate_database()
