from flask_sqlalchemy import SQLAlchemy

# Create a global instance of SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    # Initialize the app with the db instance
    db.init_app(app)
    
    with app.app_context():
        db.create_all()  # Create database tables