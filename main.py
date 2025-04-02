import os
import threading
from dotenv import load_dotenv
from app import app
from bot import run_bot_thread
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_telegram_credentials():
    """Validate that all required Telegram credentials are set"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")
    
    logger.info("Telegram credentials validated successfully")

if __name__ == "__main__":
    try:
        validate_telegram_credentials()
        
        # Start bot in a separate thread
        logger.info("Starting Telegram bot thread...")
        bot_thread = threading.Thread(target=run_bot_thread)
        bot_thread.daemon = True
        bot_thread.start()
        
        # Start Flask app
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting Flask app on port {port}...")
        app.run(host="0.0.0.0", port=port, debug=False)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
