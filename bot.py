import os
import logging
import threading
import signal
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackQueryHandler, ConversationHandler, CallbackContext
)
from sqlalchemy.exc import SQLAlchemyError
from models import User, Quiz, Question, QuizAttempt, ChatGroup, QuizSession, Analytics
from app import db
from config import TELEGRAM_BOT_TOKEN, OWNER_ID

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bot')

def initialize_bot():
    """Initialize and configure the Telegram bot"""
    # Check if token is available
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram Bot Token not set in environment variables!")
        raise ValueError("TELEGRAM_BOT_TOKEN is required")
    
    # Create the Updater and pass it the bot token
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    # Check for API ID and Hash
    telegram_api_id = os.environ.get('TELEGRAM_API_ID')
    telegram_api_hash = os.environ.get('TELEGRAM_API_HASH')
    owner_id = os.environ.get('OWNER_ID')
    
    if not telegram_api_id or not telegram_api_hash:
        logger.warning("Telegram API ID or API Hash is missing! Some advanced features may not be available.")
        logger.error("Telegram API ID or API Hash not set in environment variables!")
        logger.error("These credentials are required for advanced functionality.")
        logger.warning("Bot will be initialized with basic functionality only.")
    
    if not owner_id:
        logger.warning("Owner ID is not set! Admin features will not be available.")
    
    # Register command handlers
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("profile", user_profile))
    dp.add_handler(CommandHandler("quizzes", list_quizzes))
    dp.add_handler(CommandHandler("quiz", start_quiz))
    dp.add_handler(CommandHandler("marathon", lambda update, context: start_quiz(update, context, marathon=True)))
    dp.add_handler(CommandHandler("skip", skip_question))
    dp.add_handler(CommandHandler("pause", pause_quiz))
    dp.add_handler(CommandHandler("resume", resume_quiz))
    dp.add_handler(CommandHandler("end", end_quiz))
    dp.add_handler(CommandHandler("search", search_quizzes))
    dp.add_handler(CommandHandler("view", view_quiz_details))
    dp.add_handler(CommandHandler("report", generate_report))
    
    # Admin command handlers
    if owner_id:
        dp.add_handler(CommandHandler("admin", admin_dashboard))
        dp.add_handler(CommandHandler("ban", ban_user))
        dp.add_handler(CommandHandler("unban", unban_user))
        dp.add_handler(CommandHandler("setadmin", set_admin))
    
    # Quiz creation conversation handler
    create_quiz_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("create", create_quiz)],
        states={
            # ... conversation states would go here
        },
        fallbacks=[CommandHandler("cancel", cancel_operation)]
    )
    dp.add_handler(create_quiz_conv_handler)
    
    # Quiz editing conversation handler
    edit_quiz_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_quiz)],
        states={
            # ... conversation states would go here
        },
        fallbacks=[CommandHandler("cancel", cancel_operation)]
    )
    dp.add_handler(edit_quiz_conv_handler)
    
    # Poll conversion conversation handler
    poll_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("import", import_questions)],
        states={
            # ... conversation states would go here
        },
        fallbacks=[CommandHandler("cancel", cancel_operation)]
    )
    dp.add_handler(poll_conv_handler)
    
    # Handler for callback queries from inline keyboards
    dp.add_handler(CallbackQueryHandler(handle_button_press))
    
    # Handler for forwarded polls
    dp.add_handler(MessageHandler(Filters.poll, handle_poll))
    
    # Handler for PDF files
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_pdf_file))
    
    # Handler for text messages that aren't commands
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_message))
    
    # Register error handler
    dp.add_error_handler(error_handler)
    
    # Log bot configuration
    logger.info("Bot is running with the following configuration:")
    logger.info(f"- API ID: {'Set' if telegram_api_id else 'Not set'}")
    logger.info(f"- API Hash: {'Set' if telegram_api_hash else 'Not set'}")
    logger.info(f"- Owner ID: {'Set' if owner_id else 'Not set'}")
    
    return updater


def start_command(update: Update, context: CallbackContext):
    """Handle the /start command"""
    from app import app
    
    # Use Flask application context
    with app.app_context():
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        try:
            # Register user if not already registered
            db_user = User.query.filter_by(telegram_id=user.id).first()
            if not db_user:
                db_user = register_user(user)
            
            # Update last active time
            db_user.last_active = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            update.message.reply_text("Sorry, there was a database error. Please try again later.")
    
    # Send welcome message
    welcome_text = (
        f"Hello {user.first_name}! 👋\n\n"
        f"Welcome to the Advanced Quiz Bot! 🎯\n\n"
        f"Here's what you can do:\n"
        f"• Take quizzes from our library 📚\n"
        f"• Create your own quizzes 📝\n"
        f"• Challenge friends and groups 👥\n"
        f"• Track your progress and analytics 📊\n\n"
        f"Type /help to see all available commands."
    )
    
    keyboard = [
        [InlineKeyboardButton("Browse Quizzes", callback_data="quiz_list_1")],
        [InlineKeyboardButton("Create Quiz", callback_data="create_quiz")],
        [InlineKeyboardButton("My Profile", callback_data="profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    # Log analytics
    analytics = Analytics(
        date=datetime.utcnow(),
        user_id=db_user.id,
        chat_id=chat_id,
        event_type="bot_start",
        event_data={}
    )
    db.session.add(analytics)
    db.session.commit()

# ... Additional bot handlers would go here ...

def start_bot():
    """Start the Telegram bot"""
    try:
        # Initialize and start the bot
        updater = initialize_bot()
        
        # Start the Bot
        updater.start_polling()
        logger.info("Bot started successfully!")
        
        # Run the bot until you press Ctrl-C
        updater.idle()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

def run_bot_thread():
    """Run the bot in a separate thread"""
    try:
        start_bot()
    except Exception as e:
        logger.error(f"Bot thread error: {e}")
