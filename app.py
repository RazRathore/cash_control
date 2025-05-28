from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, Markup
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
import re
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from flask_migrate import Migrate
from extensions import db
from models import User, Client, Transaction
import pytz

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mining_ledger.db?check_same_thread=False&timeout=30'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
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
    from datetime import datetime, timedelta, timezone
    import pytz
    
    # Get filter parameters
    client_id = request.args.get('client_id', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Initialize query
    query = db.session.query(Transaction)
    
    # Apply client filter if selected
    if client_id:
        query = query.filter(Transaction.client_id == client_id)
    
    # Parse and apply date filters
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= start_date)
            
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() + timedelta(days=1)
            query = query.filter(Transaction.date < end_date)
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        # Continue with unfiltered query if there's a date parsing error
    
    # Get total count for pagination
    total_transactions = query.count()
    
    # Apply pagination
    transactions_pagination = query.order_by(Transaction.date.desc(), Transaction.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Get all transactions up to the current page to calculate running balance per client
    all_transactions_query = query.order_by(Transaction.client_id, Transaction.date.asc(), Transaction.id.asc())
    all_transactions = all_transactions_query.all()
    
    # Calculate running balance per client
    client_balances = {}
    transaction_balances = {}
    
    for transaction in all_transactions:
        client_id = transaction.client_id
        if client_id not in client_balances:
            client_balances[client_id] = 0
        
        # Update the balance for this client
        client_balances[client_id] += (transaction.credit_amount - transaction.debit_amount)
        transaction_balances[transaction.id] = client_balances[client_id]
    
    # Get the paginated transactions in the correct order (newest first)
    paginated_transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc())\
                                .paginate(page=page, per_page=per_page, error_out=False)
    
    # Add balances to the paginated transactions
    transactions = []
    for transaction in paginated_transactions.items:
        transaction.balance = transaction_balances.get(transaction.id, 0)
        transactions.append(transaction)
    
    # Get unique clients for the filter dropdown
    clients = Client.query.order_by(Client.name).all()
    
    # Debug: Print the generated SQL query
    print(f"SQL Query: {query.statement}")
    print(f"Found {len(transactions)} transactions")
    
    return render_template('transactions.html', 
                         transactions=transactions, 
                         transactions_pagination=transactions_pagination,
                         clients=clients,
                         selected_client_id=str(client_id) if client_id else None,
                         start_date=start_date_str if start_date_str else '',
                         end_date=end_date_str if end_date_str else '',
                         pytz=pytz)

@app.route('/transactions/new', methods=['GET', 'POST'])
@login_required
def new_transaction():
    clients = Client.query.order_by(Client.name).all()
    
    if request.method == 'POST':
        try:
            # Get form data
            date_str = request.form.get('date')
            client_id = request.form.get('client_id')
            
            # Validate required fields
            if not client_id:
                flash('Client is required', 'danger')
                return render_template('new_transaction.html', clients=clients, today=datetime.utcnow().date())
            
            # Get current time in IST
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist).replace(tzinfo=None)  # Store as naive datetime in IST
            
            # Get client for the transaction
            client = Client.query.get_or_404(client_id)
            
            # Convert amounts to integers (storing in paise)
            debit_amount = int(float(request.form.get('debit_amount', 0) or 0)) * 100
            credit_amount = int(float(request.form.get('credit_amount', 0) or 0)) * 100
            
            # Create transaction with current timestamp
            transaction = Transaction(
                date=current_time,  # Using current timestamp for the transaction
                name=f"Transaction for {client.name}",
                description=request.form.get('description', ''),
                debit_amount=debit_amount,
                credit_amount=credit_amount,
                client_id=client_id,
                created_at=current_time,
                updated_at=current_time
            )
            
            # Calculate balance for the client (in paise)
            client_balance = client.balance or 0
            transaction.balance = client_balance + credit_amount - debit_amount
            
            # Update client's balance
            client.balance = transaction.balance
            
            db.session.add(transaction)
            db.session.commit()
            
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('transactions'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding transaction: {str(e)}', 'danger')
    
    return render_template('new_transaction.html', clients=clients, today=datetime.utcnow().date())

@app.route('/transactions/report')
@login_required
def transactions_report():
    return render_template('transactions_report.html')

@app.route('/accounts')
@login_required
def accounts():
    return render_template('accounts_standalone.html')

# In-memory storage for expenses (replace with database in production)
expenses_db = []

@app.route('/expenses')
@login_required
def expenses():
    # Get the 10 most recent expenses
    recent_expenses = sorted(expenses_db, key=lambda x: x.get('date', ''), reverse=True)[:10]
    return render_template('expenses.html', recent_expenses=recent_expenses)

@app.route('/api/expenses', methods=['POST'])
@login_required
def add_expense():
    try:
        data = request.get_json()
        data['id'] = len(expenses_db) + 1
        data['date'] = datetime.now(timezone.utc).isoformat()
        expenses_db.append(data)
        return jsonify({"success": True, "message": "Expense added successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/expenses/client/<client_name>', methods=['GET'])
@login_required
def get_client_expenses(client_name):
    try:
        client_expenses = [exp for exp in expenses_db if exp.get('name') == client_name]
        return jsonify({"success": True, "data": client_expenses})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

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
        
        # Sorting - default to showing most recently added first
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
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
                (Client.client_id.ilike(search)) |
                (Client.address.ilike(search))
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

@app.route('/api/clients/search', methods=['GET'])
@login_required
def search_clients():
    """Search for clients by name"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    # Search for clients where the name contains the query (case-insensitive)
    clients = Client.query.filter(Client.name.ilike(f'%{query}%'))\
                         .order_by(Client.name)\
                         .limit(10)\
                         .all()
    
    return jsonify([{
        'id': client.id,
        'name': client.name,
        'phone': client.phone or '',
        'email': client.email or ''
    } for client in clients])

@app.route('/api/clients/<int:client_id>', methods=['GET'])
@login_required
def get_client(client_id):
    """Get a single client by ID"""
    client = Client.query.get_or_404(client_id)
    return jsonify({
        'success': True,
        'data': {
            'id': client.id,
            'client_id': client.client_id,
            'name': client.name,
            'phone': client.phone,
            'email': client.email,
            'address': client.address,
            'client_type': client.client_type or 'Individual',
            'status': client.status or 'Active',
            'balance': float(client.balance or 0),
            'created_at': client.created_at.isoformat() if client.created_at else None,
            'updated_at': client.updated_at.isoformat() if client.updated_at else None
        }
    }), 200

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
