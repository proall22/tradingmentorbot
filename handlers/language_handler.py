from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from database import db
from config import LANGUAGES
from messages import get_message
from utils import log_user_action

logger = logging.getLogger(__name__)

async def handle_change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection"""
    user_id = update.effective_user.id

    log_user_action(user_id, "change_language_request")

    # Always use Markdown for formatting
    message = (
        "🌐 *Choose Your Language*\n\n"
        "Please select your preferred language:"
    )

    keyboard = []
    for lang_code, lang_name in LANGUAGES.items():
        keyboard.append([InlineKeyboardButton(
            lang_name,
            callback_data=f"set_language_{lang_code}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user language"""
    user_id = update.effective_user.id

    # Extract language code from callback data
    language_code = update.callback_query.data.split('_')[2]

    if language_code not in LANGUAGES:
        await update.callback_query.answer("Invalid language!")
        return

    # Update user language in database
    success = db.update_user_language(user_id, language_code)

    if success:
        log_user_action(user_id, "language_changed", language_code)

        # Get localized message
        message = get_message(language_code, 'language_updated')

        await update.callback_query.answer("✅ Language updated!")

        # Always show main menu in the new language
        from handlers.start_handler import show_main_menu
        await show_main_menu(update, context)
    else:
        await update.callback_query.answer("❌ Failed to update language!")