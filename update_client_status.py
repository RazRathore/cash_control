from app import app, db

def normalize_client_status():
    with app.app_context():
        # Update all status values to title case
        result = db.session.execute(
            """
            UPDATE clients 
            SET status = 
                CASE 
                    WHEN LOWER(status) = 'active' THEN 'Active'
                    WHEN LOWER(status) = 'pending' THEN 'Pending'
                    WHEN LOWER(status) = 'inactive' THEN 'Inactive'
                    ELSE 'Active'
                END
            WHERE LOWER(status) IN ('active', 'pending', 'inactive')
            """
        )
        
        db.session.commit()
        print(f"Updated {result.rowcount} client records with normalized status values.")

if __name__ == '__main__':
    normalize_client_status()
