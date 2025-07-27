from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import json
from database import db
from messages import get_message
from utils import generate_referral_code, create_referral_link, is_admin, log_user_action

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id

    log_user_action(user_id, "start_command")

    # Check for referral code in start parameter
    referral_code = None
    if context.args:
        referral_code = context.args[0]
        log_user_action(user_id, "referral_visit", referral_code)
     # Check if user is admin
    from config import ADMIN_IDS
    if user_id in ADMIN_IDS:
        # Admin: show admin panel, skip registration
        from handlers.admin_handler import handle_admin_panel
        await handle_admin_panel(update, context)
        return

    # Check if user exists
    existing_user = db.get_user(user_id)

    # Try to get language from user profile or fallback to English
    user_language = existing_user.get('language', 'en') if existing_user else 'en'

    if existing_user:
        # Existing user - show main menu
        await show_main_menu(update, context, existing_user)
    else:
        # New user - show welcome and registration option
        welcome_text = get_message(user_language, 'welcome')

        keyboard = [
            [InlineKeyboardButton("🔐 Register Now", callback_data="register_start")],
            [InlineKeyboardButton("🌐 Change Language", callback_data="change_language")]
        ]

        # Store referral code in session if provided
        if referral_code:
            db.update_user_session(user_id, "start_with_referral", json.dumps({"referral_code": referral_code}))

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user=None):
    """Show main menu for registered users"""
    user_id = update.effective_user.id

    if not user:
        user = db.get_user(user_id)

    if not user:
        if update.message:
            await update.message.reply_text("Please register first using /start")
        else:
            await update.callback_query.edit_message_text("Please register first using /start")
        return

    # Check for active subscription
    active_sub = db.get_active_subscription(user_id)

    keyboard = [
        [InlineKeyboardButton("📚 Browse Services", callback_data="browse_services")],
        [InlineKeyboardButton("📊 My Dashboard", callback_data="show_dashboard")],
        [InlineKeyboardButton("🤝 Referral Program", callback_data="show_referrals")],
    ]

    if not active_sub:
        keyboard.insert(1, [InlineKeyboardButton("💳 Subscribe Now", callback_data="browse_services")])

    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👨‍💼 Admin Panel", callback_data="admin_panel")])

    keyboard.append([InlineKeyboardButton("🌐 Language", callback_data="change_language")])

    user_language = user.get('language', 'en')

    # Use personalized main menu message
    greeting = f"🏠 **Main Menu**\n\nWelcome back, {user['name']}! What would you like to do today?\n\nChoose an option below:"

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Always show the custom keyboard (persistent menu)
    custom_keyboard = [
        [KeyboardButton("📚 Browse Services"), KeyboardButton("📊 Dashboard")],
        [KeyboardButton("🤝 Referrals"), KeyboardButton("❓ Help")],
        [KeyboardButton("🌐 Language")]
    ]
    if is_admin(user_id):
        custom_keyboard.append([KeyboardButton("👨‍💼 Admin Panel")])

    reply_markup_custom = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

    if update.message:
        await update.message.reply_text(
            greeting,
            parse_mode='Markdown',
            reply_markup=reply_markup_custom  # Send custom keyboard first
        )
        await update.message.reply_text(
            "👇 Use the menu below for quick access to main features.",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            greeting,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )