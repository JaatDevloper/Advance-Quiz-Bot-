"""
Health check script for Koyeb.
This script can be run to verify the health of the application components.
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if all required environment variables are set"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'DATABASE_URL',
        'SESSION_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("All required environment variables are set")
    return True

def check_telegram_bot():
    """Check if the Telegram bot token is valid"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set")
        return False
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                logger.info(f"Bot check successful: @{bot_info['result']['username']}")
                return True
            else:
                logger.error(f"Bot token is invalid: {bot_info.get('description')}")
                return False
        else:
            logger.error(f"Failed to connect to Telegram API: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error checking Telegram bot: {e}")
        return False

def check_database():
    """Check if the database connection is working"""
    try:
        from app import app, db
        with app.app_context():
            db.engine.connect()
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def check_web_server():
    """Check if the web server is running"""
    web_app_url = os.environ.get('WEB_APP_URL', 'http://localhost:5000')
    health_endpoint = f"{web_app_url}/health"
    
    try:
        response = requests.get(health_endpoint)
        if response.status_code == 200:
            logger.info("Web server is running")
            return True
        else:
            logger.error(f"Web server check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error checking web server: {e}")
        return False

def main():
    """Run all health checks"""
    logger.info("Starting application health check...")
    
    env_check = check_environment_variables()
    bot_check = check_telegram_bot()
    db_check = check_database()
    
    # Only check web server if we're not in standalone bot mode
    web_check = True
    if os.environ.get('WEB_APP_URL'):
        web_check = check_web_server()
    
    if env_check and bot_check and db_check and web_check:
        logger.info("All health checks passed!")
        return 0
    else:
        logger.error("One or more health checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
