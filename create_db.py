from app import create_app
from app.extensions import db
from app import models

# Create Flask application
app = create_app()

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")