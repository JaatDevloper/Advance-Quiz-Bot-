import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('app')

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "quiz_bot_secret_key_for_flask_sessions")

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    try:
        import models  # noqa: F401
        db.create_all()
        logger.debug("Database tables created")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

@app.errorhandler(404)
def page_not_found(e):
    return "404 Not Found", 404

@app.errorhandler(500)
def internal_server_error(e):
    return "500 Internal Server Error", 500

@app.route('/health')
def health_check():
    """Health check endpoint for Koyeb"""
    return "OK", 200

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

from routes import register_routes
register_routes(app)
