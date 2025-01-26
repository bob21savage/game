from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    # Import models (after db initialization)
    from .models import User, Character
    
    # Register blueprints
    from .routes import main
    app.register_blueprint(main)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app