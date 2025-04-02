"""
Standalone script for running the Telegram bot without the web interface.
This can be useful for debugging or when you only need the bot functionality.
"""

import os
import logging
from dotenv import load_dotenv
from bot import start_bot
from app import app

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize the database with all required tables"""
    with app.app_context():
        from models import db
        db.create_all()
        logger.info("Database tables created or verified")

def main():
    """Run the Telegram bot as a standalone application"""
    try:
        # Setup database
        setup_database()
        
        # Start the bot
        logger.info("Starting Telegram bot in standalone mode...")
        start_bot()
    except Exception as e:
        logger.error(f"Failed to start bot in standalone mode: {e}")
        raise

if __name__ == "__main__":
    main()
