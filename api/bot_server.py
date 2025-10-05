import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import httpx
import json
import threading
from fastapi import FastAPI
import uvicorn

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create FastAPI app for health checks
app = FastAPI()

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "telegram-bot", "message": "Bot is running"}

@app.get("/health")
async def health():
    return {"status": "ok", "bot_running": True}

# Store user states
user_states = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.effective_chat.id
    user_states[chat_id] = "awaiting_location"

    # Delete existing location first
    await delete_user_location(chat_id, context)

    # Create inline keyboard with location sharing and manual entry options
    keyboard = [
        [
            InlineKeyboardButton("📍 Share Location", callback_data="share_location"),
            InlineKeyboardButton("✏️ Enter Manually", callback_data="enter_city")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Hello! 🌍 I can alert you about daily weather and air quality.\n"
        "Please share your location 📍 or type your city name.",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id

    if query.data == "share_location":
        user_states[chat_id] = "awaiting_location_share"
        await query.edit_message_text(
            "Getting your location automatically... 📍\n\n"
            "Please share your location using the button below:"
        )

        # Send a location request button
        location_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Share My Location", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text="Tap the button to automatically share your location:",
            reply_markup=location_keyboard
        )

    elif query.data == "enter_city":
        user_states[chat_id] = "awaiting_city"
        await query.edit_message_text(
            "Please type your city name:\n\n"
            "Example: London, New York, Tokyo, etc."
        )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle location messages"""
    chat_id = update.effective_chat.id
    user_states[chat_id] = None

    if update.message.location:
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude

        # Clear the keyboard
        await context.bot.send_message(
            chat_id=chat_id,
            text="📍 Location received! Processing your registration...",
            reply_markup=ReplyKeyboardRemove()
        )

        # Register location with coordinates
        await register_user_location(chat_id, latitude=latitude, longitude=longitude, context=context)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    # Check if user is waiting to enter city name
    if user_states.get(chat_id) == "awaiting_city":
        user_states[chat_id] = None

        # Register location with city name
        await register_user_location(chat_id, city=text, context=context)

    # Handle general messages
    elif text.startswith('/'):
        # Let command handlers process commands
        return
    else:
        # Handle other text messages
        await update.message.reply_text(
            "Please use /start to begin registration or type /help for available commands."
        )

async def delete_user_location(chat_id: int, context: ContextTypes.DEFAULT_TYPE = None):
    """Delete user's existing location from the database"""
    try:
        # Send delete request to API
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{API_BASE_URL}/delete_location/{chat_id}",
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully deleted location for chat_id {chat_id}: {result}")
                return True
            elif response.status_code == 404:
                # User doesn't exist, which is fine
                logger.info(f"No existing location found for chat_id {chat_id}")
                return True
            else:
                logger.error(f"Failed to delete location for chat_id {chat_id}: {response.text}")
                return False

    except Exception as e:
        logger.error(f"Error deleting location for chat_id {chat_id}: {str(e)}")
        return False

async def register_user_location(chat_id: int, city: str = None, latitude: float = None, longitude: float = None, context: ContextTypes.DEFAULT_TYPE = None):
    """Register user location in the database"""
    try:
        # Prepare registration data
        registration_data = {
            "chat_id": chat_id
        }

        if city:
            registration_data["city"] = city
        if latitude is not None and longitude is not None:
            registration_data["latitude"] = latitude
            registration_data["longitude"] = longitude

        # Send registration request to API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/register_location",
                json=registration_data,
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()

                # Create success message with dashboard button (pass chat_id as parameter)
                dashboard_url = f"https://nasa-hack-pi.vercel.app/?chat_id={chat_id}"
                keyboard = [
                    [InlineKeyboardButton("🌤️ Open Dashboard", url=dashboard_url)]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                if context:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="✅ Successfully registered! You'll now receive daily weather and air quality updates.\n"
                             "Tap 'Open Dashboard' below to view your data.\n\n"
                             "Use /start to reset your location or /changelocation to update it.",
                        reply_markup=reply_markup
                    )

                logger.info(f"Successfully registered location for chat_id {chat_id}: {result}")

            else:
                error_msg = f"Failed to register location: {response.text}"
                logger.error(error_msg)

                if context:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Sorry, I couldn't register your location. Please try again later."
                    )

    except Exception as e:
        error_msg = f"Error registering location for chat_id {chat_id}: {str(e)}"
        logger.error(error_msg)

        if context:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Sorry, I encountered an error. Please try again later."
            )

async def changelocation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /changelocation command"""
    chat_id = update.effective_chat.id
    user_states[chat_id] = "awaiting_location"

    # Create inline keyboard with location sharing and manual entry options
    keyboard = [
        [
            InlineKeyboardButton("📍 Share Location", callback_data="share_location"),
            InlineKeyboardButton("✏️ Enter Manually", callback_data="enter_city")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📍 Let's update your location for weather alerts!\n"
        "Please share your new location 📍 or type your new city name.",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🌤️ **WeatherSphere Bot Commands:**

/start - Begin registration for weather alerts
/changelocation - Update your location for weather alerts
/help - Show this help message

**Features:**
• Daily weather notifications
• Air quality alerts
• Location-based updates
• Personal weather dashboard

To get started, use /start and share your location!
Already registered? Use /changelocation to update your location.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the telegram bot"""
    logger.error(f"Update {update} caused error {context.error}")

def run_bot():
    """Run the telegram bot in a separate thread"""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error("Please set TELEGRAM_BOT_TOKEN in your .env file")
        return

    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("changelocation", changelocation_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    logger.info("Starting WeatherSphere Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Start Telegram bot in background
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Run FastAPI server
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)