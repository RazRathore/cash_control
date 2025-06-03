from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, Markup
from flask_login import login_user, login_required, logout_user, current_user
from functools import wraps
from flask_migrate import Migrate
import os
import re
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from extensions import db, login_manager, init_extensions
from models import User, Client, Transaction, WorkingStage
import pytz

def role_required(*roles):
    """Decorator to check if user has required role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles and 'admin' not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
# Use absolute path for database to ensure it's created in the correct location
import os
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "mining_ledger.db")}?check_same_thread=False&timeout=30'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
app = init_extensions(app)

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['REMEMBER_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(hours=1)

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

@app.route('/vendor-transactions')
@login_required
def vendor_transactions():
    from datetime import datetime, timedelta, timezone
    import pytz
    
    # Get filter parameters
    client_id = request.args.get('client_id', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Set transaction type to filter only vendor transactions
    transaction_type = 'vendor'
    
    # Initialize query with vendor filter
    query = Transaction.query.filter(Transaction.transaction_type == transaction_type)
    
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
    
    # Add balances and working stages to the paginated transactions
    transactions = []
    for transaction in paginated_transactions.items:
        transaction.balance = transaction_balances.get(transaction.id, 0)
        # Calculate total credits (token_amount + sum of working stages)
        total_credits = transaction.token_amount
        working_stages = WorkingStage.query.filter_by(transaction_id=transaction.id).all()
        for stage in working_stages:
            total_credits += stage.amount
        transaction.total_credits = total_credits
        transaction.working_stages = working_stages
        transactions.append(transaction)
    
    # Get unique clients for the filter dropdown
    clients = Client.query.order_by(Client.name).all()
    
    # Debug: Print the generated SQL query
    print(f"Vendor Transactions SQL Query: {query.statement}")
    print(f"Found {len(transactions)} vendor transactions")
    
    return render_template('vendor_transactions.html', 
                         transactions=transactions, 
                         transactions_pagination=transactions_pagination,
                         clients=clients,
                         selected_client_id=str(client_id) if client_id else None,
                         start_date=start_date_str if start_date_str else '',
                         end_date=end_date_str if end_date_str else '',
                         pytz=pytz)

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
    
    # Set transaction type to filter only client transactions
    transaction_type = 'client'
    
    # Initialize query with client filter
    query = Transaction.query.filter(Transaction.transaction_type == transaction_type)
    
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
    
    # Add balances and working stages to the paginated transactions
    transactions = []
    for transaction in paginated_transactions.items:
        transaction.balance = transaction_balances.get(transaction.id, 0)
        # Calculate total credits (token_amount + sum of working stages)
        total_credits = transaction.token_amount
        working_stages = WorkingStage.query.filter_by(transaction_id=transaction.id).all()
        for stage in working_stages:
            total_credits += stage.amount
        transaction.total_credits = total_credits
        transaction.working_stages = working_stages
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

@app.route('/transactions/<int:transaction_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    clients = Client.query.order_by(Client.name).all()
    
    if request.method == 'POST':
        try:
            # Get form data
            client_id = request.form.get('client_id')
            
            # Validate required fields
            if not client_id:
                flash('Client is required', 'danger')
                return render_template('edit_transaction.html', 
                                    transaction=transaction, 
                                    clients=clients,
                                    today=datetime.utcnow().date())
            
            # Get client for the transaction
            client = Client.query.get_or_404(client_id)
            
            # Process amounts (convert to paise)
            total_amount = int(float(request.form.get('total_amount', 0) or 0) * 100)
            token_amount = int(float(request.form.get('token_amount', 0) or 0) * 100)
            
            # Get working stages data
            stage_descriptions = request.form.getlist('stage_descriptions[]')
            stage_amounts = request.form.getlist('stage_amounts[]')
            
            # Calculate total stages amount
            stages_total = sum(int(float(amt) * 100) for amt in stage_amounts if amt)
            
            # Calculate remaining balance
            remaining_balance = total_amount - token_amount - stages_total
            
            # Update transaction
            transaction.client_id = client_id
            transaction.name = f"Transaction for {client.name}"
            transaction.description = request.form.get('description', '')
            transaction.total_amount = total_amount
            transaction.token_amount = token_amount
            transaction.remaining_balance = remaining_balance
            
            # Delete existing working stages
            WorkingStage.query.filter_by(transaction_id=transaction.id).delete()
            
            # Add new working stages
            for desc, amt in zip(stage_descriptions, stage_amounts):
                if desc and amt:
                    stage = WorkingStage(
                        description=desc.strip(),
                        amount=int(float(amt) * 100),
                        transaction_id=transaction.id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(stage)
            
            # Update client balance (if client changed)
            if transaction.client_id != int(client_id):
                # Remove token amount from old client's balance
                old_client = Client.query.get(transaction.client_id)
                if old_client:
                    old_client.balance = (old_client.balance or 0) - transaction.token_amount
                
                # Add token amount to new client's balance
                client.balance = (client.balance or 0) + token_amount
            
            db.session.commit()
            flash('Transaction updated successfully!', 'success')
            return redirect(url_for('transactions'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating transaction: {str(e)}', 'danger')
            import traceback
            traceback.print_exc()
    
    # Convert working stages to a list of dicts for the template
    working_stages = [{'description': ws.description, 'amount': ws.amount} 
                     for ws in transaction.working_stages]
    
    return render_template('edit_transaction.html', 
                         transaction=transaction, 
                         clients=clients,
                         working_stages=working_stages,
                         today=datetime.utcnow().date())

@app.route('/transactions/new', methods=['GET', 'POST'])
@login_required
def new_transaction():
    transaction_type = request.args.get('transaction_type', 'client')  # Default to client if not specified
    clients = Client.query.order_by(Client.name).all()
    
    if request.method == 'POST':
        try:
            # Get form data
            client_id = request.form.get('client_id')
            
            # Validate required fields
            if not client_id:
                flash('Client is required', 'danger')
                return render_template('new_transaction.html', 
                                    clients=clients, 
                                    today=datetime.utcnow().date(),
                                    transaction_type=transaction_type)
            
            # Get current time in IST
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist).replace(tzinfo=None)  # Store as naive datetime in IST
            
            # Get client for the transaction
            client = Client.query.get_or_404(client_id)
            
            # Process amounts (convert to paise)
            total_amount = int(float(request.form.get('total_amount', 0) or 0) * 100)
            token_amount = int(float(request.form.get('token_amount', 0) or 0) * 100)
            
            # Get working stages data
            stage_descriptions = request.form.getlist('stage_descriptions[]')
            stage_amounts = request.form.getlist('stage_amounts[]')
            
            # Calculate total stages amount
            stages_total = sum(int(float(amt) * 100) for amt in stage_amounts if amt)
            
            # Calculate remaining balance
            remaining_balance = total_amount - token_amount - stages_total
            
            # Create transaction
            transaction = Transaction(
                date=current_time,
                name=f"Transaction for {client.name}",
                description=request.form.get('description', ''),
                total_amount=total_amount,
                token_amount=token_amount,
                remaining_balance=remaining_balance,
                client_id=client_id,
                transaction_type=transaction_type,  # Set transaction type
                created_at=current_time,
                updated_at=current_time
            )
            
            # Add working stages
            for desc, amt in zip(stage_descriptions, stage_amounts):
                if desc and amt:  # Only add if both description and amount are provided
                    stage = WorkingStage(
                        description=desc.strip(),
                        amount=int(float(amt) * 100),
                        transaction=transaction,
                        created_at=current_time,
                        updated_at=current_time
                    )
                    db.session.add(stage)
            
            # Update client's balance (add the token amount to their balance)
            client.balance = (client.balance or 0) + token_amount
            
            db.session.add(transaction)
            db.session.commit()
            
            flash('Transaction added successfully!', 'success')
            # Redirect to the appropriate transactions page based on type
            if transaction_type == 'vendor':
                return redirect(url_for('vendor_transactions'))
            return redirect(url_for('transactions'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding transaction: {str(e)}', 'danger')
            import traceback
            traceback.print_exc()
    
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
@role_required('admin', 'accountant')
def expenses():
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
                (Client.address.ilike(search)) |
                (Client.near_village.ilike(search)) |
                (Client.district.ilike(search)) |
                (Client.client_type.ilike(search)) |
                (Client.mining_lease_no.ilike(search)) |
                (Client.city.ilike(search)) |
                (Client.state.ilike(search)) |
                (Client.country.ilike(search)) |
                (Client.postal_code.ilike(search))
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
        print(clients)
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
        'email': client.email or '',
        'query_license': client.query_license,
        'near_village': client.near_village,
        'district': client.district,
        'mining_lease_no': client.mining_lease_no,
        'city': client.city,
        'state': client.state,
        'country': client.country,
        'postal_code': client.postal_code,
        'status': client.status or 'Active',
        'balance': float(client.balance or 0),
        'created_at': client.created_at.isoformat() if client.created_at else None,
        'updated_at': client.updated_at.isoformat() if client.updated_at else None
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
            'query_license': client.query_license,
            'mining_lease_no': client.mining_lease_no,
            'near_village': client.near_village,
            'district': client.district,
            'city': client.city,
            'state': client.state,
            'country': client.country or 'India',
            'postal_code': client.postal_code,
            'balance': float(client.balance or 0) if client.balance is not None else 0.0,
            'notes': client.notes,
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
        print('adding new client.')
        print(data)
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
        client.query_license = data.get('query_license')
        client.mining_lease_no = data.get('mining_lease_no')
        client.near_village = data.get('near_village')
        client.city = data.get('city')
        client.district = data.get('district')
        client.state = data.get('state')
        client.country = data.get('country')
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
        if 'query_license' in data:
            client.query_license = data['query_license']
        if 'mining_lease_no' in data:
            client.mining_lease_no = data['mining_lease_no']
        if 'near_village' in data:
            client.near_village = data['near_village']
        if 'city' in data:
            client.city = data['city']
        if 'district' in data:
            client.district = data['district']
        if 'state' in data:
            client.state = data['state']
        if 'country' in data:
            client.country = data['country']
            
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

from models import User

# Create database tables
def init_db():
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='Administrator',
                department='Administration',
                role='admin'  # Add admin role
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Created admin user")
        
        # Create staff user if not exists
        staff = User.query.filter_by(username='staff').first()
        if not staff:
            staff = User(
                username='staff',
                name='Staff Member',
                department='Operations',
                role='user'  # Regular user role with restricted access
            )
            staff.set_password('staff123')
            db.session.add(staff)
            print("Created staff user")
        
        # Commit changes
        db.session.commit()
        print("Database initialization complete")

# Add this at the bottom of app.py
if __name__ == '__main__':
    # Initialize the database
    with app.app_context():
        init_db()
    # Run the app
    print("Starting Flask development server...")
    app.run(debug=True, host='0.0.0.0', port=5000)