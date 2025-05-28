from app import app, db

def normalize_client_types():
    with app.app_context():
        # Update all client types to title case
        result = db.session.execute(
            """
            UPDATE clients 
            SET client_type = 
                CASE 
                    WHEN LOWER(client_type) = 'individual' THEN 'Individual'
                    WHEN LOWER(client_type) = 'corporate' THEN 'Corporate'
                    ELSE 'Individual'
                END
            WHERE LOWER(client_type) IN ('individual', 'corporate')
            """
        )
        
        db.session.commit()
        print(f"Updated {result.rowcount} client records with normalized client types.")

if __name__ == '__main__':
    normalize_client_types()
