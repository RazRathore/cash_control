from app import app, db
from models import User, Client, Transaction
from datetime import datetime, timedelta

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create a test user
        if not User.query.filter_by(username='testuser').first():
            user = User(
                username='testuser',
                name='Test User',
                department='test'
            )
            user.set_password('test123')
            db.session.add(user)
            
            # Create a test client
            client = Client(
                client_id='CLI1001',
                name='Test Client',
                client_type='Individual',
                email='client@example.com',
                phone='+1234567890',
                address='123 Test St',
                city='Test City',
                state='Test State',
                country='India',
                postal_code='123456',
                status='Active',
                balance=1000.00,
                notes='Test client'
            )
            db.session.add(client)
            
            # Create a test transaction
            transaction = Transaction(
                date=datetime.utcnow().date(),
                name='Initial Deposit',
                description='Test transaction',
                debit_amount=0.0,
                credit_amount=1000.00,
                balance=1000.00,
                client_id=1
            )
            db.session.add(transaction)
            
            db.session.commit()
            print("Test data created successfully!")
            print("Test user: Username: testuser, Password: test123")
            print(f"Test client: {client.name} (ID: {client.client_id})")
            print(f"Test transaction: {transaction.name} (Amount: ₹{transaction.credit_amount})")

if __name__ == '__main__':
    init_db()
