import sqlite3
from datetime import datetime

def update_database():
    # Connect to the SQLite database
    conn = sqlite3.connect('mining_ledger.db')
    cursor = conn.cursor()
    
    try:
        # Create a new column for the datetime
        cursor.execute('''
            ALTER TABLE transactions 
            ADD COLUMN new_date DATETIME
        ''')
        
        # Get all transactions
        cursor.execute('SELECT id, date FROM transactions')
        transactions = cursor.fetchall()
        
        # Update each transaction with the new datetime
        for tx_id, tx_date in transactions:
            if tx_date:
                try:
                    # Parse the date and add current time
                    date_obj = datetime.strptime(tx_date, '%Y-%m-%d')
                    new_datetime = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute(
                        'UPDATE transactions SET new_date = ? WHERE id = ?',
                        (new_datetime, tx_id)
                    )
                except (ValueError, TypeError) as e:
                    print(f"Error processing transaction {tx_id}: {e}")
                    # Fallback to current time if parsing fails
                    cursor.execute(
                        'UPDATE transactions SET new_date = datetime("now") WHERE id = ?',
                        (tx_id,)
                    )
        
        # Drop the old date column
        cursor.execute('ALTER TABLE transactions DROP COLUMN date')
        
        # Rename new_date to date
        cursor.execute('ALTER TABLE transactions RENAME COLUMN new_date TO date')
        
        # Commit the changes
        conn.commit()
        print("Successfully updated database schema")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_database()
