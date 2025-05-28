from app import app, db
from models import Client

def normalize_client_types():
    with app.app_context():
        clients = Client.query.all()
        updated = 0
        
        for client in clients:
            # The @client_type.setter will handle the normalization
            if client._client_type != client.client_type:
                client.client_type = client._client_type
                updated += 1
        
        if updated > 0:
            db.session.commit()
            print(f"Updated {updated} client records with normalized client types.")
        else:
            print("No client records needed updating.")

if __name__ == '__main__':
    normalize_client_types()
