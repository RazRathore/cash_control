from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def init_extensions(app):
    """Initialize Flask extensions with the app"""
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize LoginManager
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    
    # Configure session to expire when browser is closed
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configure SQLAlchemy to use SQLite with WAL mode
    with app.app_context():
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            from sqlalchemy import event
            from sqlalchemy.engine import Engine
            
            @event.listens_for(Engine, 'connect')
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.execute('PRAGMA synchronous=NORMAL')
                cursor.close()

    return app
