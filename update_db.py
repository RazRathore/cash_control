from app import app, db
from models import Transaction

def update_transaction_dates():
    with app.app_context():
        # Get all transactions and update their dates to include time
        transactions = Transaction.query.all()
        for tx in transactions:
            if tx.date and isinstance(tx.date, str):
                from datetime import datetime
                # If date is stored as string, convert it to datetime
                try:
                    tx.date = datetime.strptime(tx.date, '%Y-%m-%d')
                except (ValueError, TypeError):
                    # If conversion fails, use current time
                    tx.date = datetime.utcnow()
            elif tx.date and not hasattr(tx.date, 'time'):
                # If it's a date object without time, convert to datetime
                from datetime import datetime
                tx.date = datetime.combine(tx.date, datetime.utcnow().time())
        
        # Commit the changes
        db.session.commit()
        print(f"Updated {len(transactions)} transactions with datetime")

if __name__ == '__main__':
    update_transaction_dates()
