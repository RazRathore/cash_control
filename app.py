from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, Markup
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import re
from dotenv import load_dotenv
from models import Client
from extensions import db

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mining_ledger.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Custom template filter
@app.template_filter('cascade_css')
def cascade_css(value):
    """A dummy filter that returns the input as-is.
    This is a workaround for templates that expect this filter.
    """
    return value

# User model
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Client(db.Model):
    __tablename__ = 'clients'
    __table_args__ = {'extend_existing': True}  # Allow table redefinition
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    company = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    credit_limit = db.Column(db.Float, default=0.0, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'company': self.company,
            'status': self.status,
            'balance': self.balance,
            'credit_limit': self.credit_limit,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@app.route('/dashboard')
def home():
    if current_user.is_authenticated:
        return render_template('dashboard_new.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/transactions')
@login_required
def transactions():
    return render_template('transactions_standalone.html')

@app.route('/transactions/report')
@login_required
def transactions_report():
    return render_template('transactions_report.html')

@app.route('/accounts')
@login_required
def accounts():
    try:
        # Get the current user's department
        department = current_user.department if hasattr(current_user, 'department') else 'Administration'
        
        # Render the template with the department information
        return render_template('accounts_standalone.html', department=department)
    except Exception as e:
        app.logger.error(f"Error in accounts route: {str(e)}")
        return render_template('error.html', error="An error occurred while loading the accounts page"), 500

# API Routes for Clients
@app.route('/api/clients', methods=['GET'])
@login_required
def get_clients():
    """Get paginated list of clients with optional filtering and sorting"""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filtering
        status = request.args.get('status')
        client_type = request.args.get('type')
        search = request.args.get('search', '').strip()
        
        # Sorting
        sort_by = request.args.get('sort_by', 'id')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Build query
        query = Client.query
        
        # Apply filters
        if status and status in ['active', 'inactive']:
            query = query.filter(Client.status == status)
            
        if search:
            search = f"%{search}%"
            query = query.filter(
                (Client.name.ilike(search)) | 
                (Client.email.ilike(search)) |
                (Client.phone.ilike(search)) |
                (Client.company.ilike(search))
            )
        
        # Apply sorting
        if hasattr(Client, sort_by):
            sort_column = getattr(Client, sort_by)
            if sort_order.lower() == 'desc':
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
        
        # Execute paginated query
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        clients = [client.to_dict() for client in pagination.items]
        
        # Prepare response
        response = {
            'success': True,
            'data': clients,
            'pagination': {
                'total': pagination.total,
                'pages': pagination.pages,
                'page': page,
                'per_page': per_page,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Error fetching clients: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch clients'}), 500

@app.route('/api/clients/<int:client_id>', methods=['GET'])
@login_required
def get_client(client_id):
    """Get a single client by ID"""
    try:
        client = Client.query.get_or_404(client_id)
        return jsonify({'success': True, 'data': client.to_dict()}), 200
    except Exception as e:
        app.logger.error(f"Error fetching client {client_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Client not found'}), 404

@app.route('/api/clients', methods=['POST'])
@login_required
def create_client():
    """Create a new client"""
    try:
        data = request.get_json()
        
        # Basic validation
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Name is required'}), 400
            
        # Create new client
        client = Client()
        client.client_id = Client.generate_client_id(data.get('client_type', 'Individual'))
        client.name = data['name']
        client.client_type = data.get('client_type', 'Individual')
        client.email = data.get('email')
        client.phone = data.get('phone')
        client.address = data.get('address')
        client.city = data.get('city')
        client.state = data.get('state')
        client.country = data.get('country', 'India')
        client.postal_code = data.get('postal_code')
        client.status = data.get('status', 'Active')
        client.balance = float(data.get('balance', 0.00))
        client.notes = data.get('notes')
        
        db.session.add(client)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Client created successfully',
            'data': client.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating client: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create client'}), 500

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
@login_required
def update_client(client_id):
    """Update an existing client"""
    try:
        client = Client.query.get_or_404(client_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            client.name = data['name']
        if 'email' in data:
            client.email = data['email']
        if 'phone' in data:
            client.phone = data['phone']
        if 'address' in data:
            client.address = data['address']
        if 'city' in data:
            client.city = data['city']
        if 'state' in data:
            client.state = data['state']
        if 'country' in data:
            client.country = data['country']
        if 'postal_code' in data:
            client.postal_code = data['postal_code']
        if 'status' in data and data['status'] in ['Active', 'Pending', 'Inactive']:
            client.status = data['status']
        if 'balance' in data:
            try:
                client.balance = float(data['balance'])
            except (ValueError, TypeError):
                pass  # Keep existing balance if invalid
        if 'notes' in data:
            client.notes = data['notes']
            
        client.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Client updated successfully',
            'data': client.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating client {client_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update client'}), 500

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
@login_required
def delete_client(client_id):
    """Delete a client"""
    try:
        client = Client.query.get_or_404(client_id)
        db.session.delete(client)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Client deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting client {client_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete client'}), 500

# Initialize database
def init_db():
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if admin user exists, if not create one
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='Administrator',
                department='Administration'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Add sample clients
            clients = [
                {
                    'name': 'Jodhpur Mining Corp',
                    'email': 'contact@jodhpurnining.com',
                    'phone': '+911234567890',
                    'address': '123 Mining Street, Jodhpur, Rajasthan',
                    'company': 'Jodhpur Mining Corp',
                    'status': 'active',
                    'balance': 50000.00,
                    'credit_limit': 100000.00,
                    'notes': 'Premium client with high credit limit'
                },
                {
                    'name': 'Rajesh Sharma',
                    'email': 'rajesh.sharma@example.com',
                    'phone': '+919876543210',
                    'address': '456 Gem Colony, Jodhpur, Rajasthan',
                    'company': 'Sharma Gems',
                    'status': 'active',
                    'balance': 25000.50,
                    'credit_limit': 50000.00,
                    'notes': 'Regular customer'
                },
                {
                    'name': 'Meera Devi',
                    'email': 'meera.devi@example.com',
                    'phone': '+919988776655',
                    'address': '789 Silver Street, Jodhpur, Rajasthan',
                    'company': 'Meera Jewelers',
                    'status': 'inactive',
                    'balance': 0.00,
                    'credit_limit': 25000.00,
                    'notes': 'Inactive account - follow up required'
                }
            ]
            
            for client_data in clients:
                client = Client(**client_data)
                db.session.add(client)
            
            db.session.commit()
            print('Database initialized with admin user and sample data.')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
