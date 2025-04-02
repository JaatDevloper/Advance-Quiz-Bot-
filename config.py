import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_ID = os.environ.get('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.environ.get('TELEGRAM_API_HASH')
OWNER_ID = os.environ.get('OWNER_ID')

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

# Web App Configuration
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'http://localhost:5000')
PORT = int(os.environ.get('PORT', 5000))

# Session Configuration
SESSION_SECRET = os.environ.get('SESSION_SECRET', 'quiz_bot_secret_key_for_flask_sessions')

# Quiz Configuration
QUIZZES_PER_PAGE = 5
MAX_OPTIONS_PER_QUESTION = 10
DEFAULT_TIME_LIMIT = 30  # seconds per question
MAX_QUIZ_SESSIONS = 100  # maximum concurrent quiz sessions

# Feature Flags
ENABLE_PDF_IMPORT = True
ENABLE_POLL_CONVERSION = True
ENABLE_MARATHON_MODE = True
ENABLE_NEGATIVE_MARKING = True
