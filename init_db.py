from app import app, db, User

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
            db.session.commit()
            print("Test user created! Username: testuser, Password: test123")

if __name__ == '__main__':
    init_db()
