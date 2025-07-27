#!/usr/bin/env python3

import logging
import json
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

# Import handlers
from handlers.start_handler import start_command, show_main_menu
from handlers.registration_handler import (
    handle_registration_start, handle_registration_steps, 
    handle_cancel_registration, handle_email_option,
    handle_telegram_option, handle_privacy_option
)
from handlers.service_handler import (
    handle_browse_services, handle_select_service, handle_select_duration
)
from handlers.payment_handler import (
    handle_binance_method, handle_payment_method, handle_submit_tx_hash, handle_tx_hash_input,
    handle_upload_receipt_request, handle_receipt_upload, handle_cancel_payment,
    handle_submit_order_id, handle_order_id_input  # <-- Add these
)
from handlers.admin_handler import (
    handle_admin_panel, handle_pending_payments, handle_approve_payment,
    handle_reject_payment, handle_all_users, handle_broadcast_setup,
    handle_broadcast_message
)
from handlers.dashboard_handler import (
    handle_show_dashboard, handle_show_referrals, handle_copy_referral_link,
    handle_update_profile, handle_main_menu
)
from handlers.language_handler import handle_change_language, handle_set_language

# Import other modules
from config import BOT_TOKEN, ADMIN_IDS
from database import db
from scheduler import start_scheduler
from utils import is_admin, log_user_action
from messages import get_message

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def handle_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help menu with contact info"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    user_language = user.get('language', 'en') if user else 'en'

    # Escaped MarkdownV2 message
    message = (
        "❓ *Help & Support*\n\n"
        "If you need assistance or encounter any errors, please contact our support team:\n\n"
        "• 📞 Phone: \\+1234567890\n"
        "• 📧 Email: support\\@tradingmentor\\.com\n"
        "• 💬 Telegram: \\@support\\_username\n\n"
        "You can also contact the admin for urgent issues\\.\n"
        "We\\'re here to help you\\!"
    )

    keyboard = [
        [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

def escape_markdown_v2(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\@])', r'\\\1', text)

async def handle_contact_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show contact support info"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    user_language = user.get('language', 'en') if user else 'en'
    
    message_raw = get_message(user_language, 'contact_support')
    message = escape_markdown_v2(message_raw)
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Help", callback_data="help_menu")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_user:
        try:
            await update.message.reply_text(
                "❌ An error occurred. Please try again or contact support."
            )
        except:
            pass

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    try:
        await query.answer()
        
        # Registration handlers
        if data == "register_start":
            await handle_registration_start(update, context)
        elif data == "resume_registration":
         from handlers.registration_handler import handle_resume_registration
         await handle_resume_registration(update, context)
        elif data == "cancel_registration":
            await handle_cancel_registration(update, context)
        elif data in ["add_email_yes", "add_email_no"]:
            await handle_email_option(update, context)
        elif data in ["add_telegram_yes", "add_telegram_no"]:
            await handle_telegram_option(update, context)
        elif data in ["privacy_allow", "privacy_deny"]:
            await handle_privacy_option(update, context)
        
        # Service handlers
        elif data == "browse_services":
            await handle_browse_services(update, context)
        elif data.startswith("select_service_"):
            await handle_select_service(update, context)
        elif data.startswith("duration_"):
            await handle_select_duration(update, context)
        
        # Payment handlers
        elif data.startswith("payment_"):
            await handle_payment_method(update, context)
        elif data == "submit_tx_hash":
            await handle_submit_tx_hash(update, context)
        elif data == "submit_order_id":  # <-- Add this
            await handle_submit_order_id(update, context)
        elif data == "upload_receipt":
            await handle_upload_receipt_request(update, context)
        elif data == "cancel_payment":
            await handle_cancel_payment(update, context)
        
        # ADD THIS BLOCK for binance method selection
        elif data in ["binance_payid", "binance_wallet"]:
            await handle_binance_method(update, context)

        # Admin handlers
        elif data == "admin_panel" and is_admin(update.effective_user.id):
            await handle_admin_panel(update, context)
        elif data == "admin_pending_payments" and is_admin(update.effective_user.id):
            await handle_pending_payments(update, context)
        elif data.startswith("approve_payment_") and is_admin(update.effective_user.id):
            await handle_approve_payment(update, context)
        elif data.startswith("reject_payment_") and is_admin(update.effective_user.id):
            await handle_reject_payment(update, context)
        elif data == "admin_all_users" and is_admin(update.effective_user.id):
            await handle_all_users(update, context)
        elif data == "admin_broadcast" and is_admin(update.effective_user.id):
            await handle_broadcast_setup(update, context)
        elif data == "admin_broadcast_user" and is_admin(update.effective_user.id):
            from handlers.admin_handler import handle_broadcast_user_setup
            await handle_broadcast_user_setup(update, context)
        elif data.startswith("admin_broadcast_user_select_") and is_admin(update.effective_user.id):
            from handlers.admin_handler import handle_broadcast_user_select
            await handle_broadcast_user_select(update, context)
        
        # Dashboard handlers
        elif data == "show_dashboard":
            await handle_show_dashboard(update, context)
        elif data == "show_referrals":
            await handle_show_referrals(update, context)
        elif data == "copy_referral_link":
            await handle_copy_referral_link(update, context)
        elif data == "update_profile":
            await handle_update_profile(update, context)
        elif data == "main_menu":
            await handle_main_menu(update, context)
        
        # Menu handlers
        elif data == "help_menu":
            await handle_help_menu(update, context)
        elif data == "contact_support":
            await handle_contact_support(update, context)
        
        # Language handlers
        elif data == "change_language":
            await handle_change_language(update, context)
        elif data.startswith("set_language_"):
            await handle_set_language(update, context)
        
        # Profile update handlers
        elif data == "update_phone":
            await update.callback_query.edit_message_text(
                "📱 **Update Phone Number**\n\nPlease type your new phone number:",
                parse_mode='Markdown'
            )
            db.update_user_session(update.effective_user.id, "updating_phone", "{}")
        elif data == "update_country":
            await update.callback_query.edit_message_text(
                "🌍 **Update Country**\n\nPlease type your country:",
                parse_mode='Markdown'
            )
            db.update_user_session(update.effective_user.id, "updating_country", "{}")
        
        else:
            await query.edit_message_text("❌ Unknown action. Please try again.")
    
    except Exception as e:
        logger.error(f"Callback query error: {e}")
        try:
            await query.edit_message_text("❌ An error occurred. Please try again.")
        except:
            pass

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # Custom admin menu triggers
    if is_admin(user_id):
        if text == "👨‍💼 Admin Panel":
            from handlers.admin_handler import handle_admin_panel
            await handle_admin_panel(update, context)
            return
        elif text == "👥 All Users":
            from handlers.admin_handler import handle_all_users
            await handle_all_users(update, context)
            return
        elif text == "💳 Pending Payments":
            from handlers.admin_handler import handle_pending_payments
            await handle_pending_payments(update, context)
            return
        elif text == "📢 Broadcast":
            from handlers.admin_handler import handle_broadcast_setup
            await handle_broadcast_setup(update, context)
            return
        elif text == "👤 Broadcast User":
            from handlers.admin_handler import handle_broadcast_user_setup
            await handle_broadcast_user_setup(update, context)
            return
        elif text == "📊 Service Stats":
            # You may need to implement handle_service_stats
            await update.message.reply_text("Service stats feature coming soon.")
            return
        elif text == "🏠 Main Menu":
            from handlers.start_handler import show_main_menu
            await show_main_menu(update, context)
            return

    # Existing code for normal user menu
    if text == "📚 Browse Services":
        await handle_browse_services(update, context)
        return
    elif text == "📊 Dashboard":
        await handle_show_dashboard(update, context)
        return
    elif text == "🤝 Referrals":
        await handle_show_referrals(update, context)
        return
    elif text == "❓ Help":
        await handle_help_menu(update, context)
        return
    elif text == "🌐 Language":
        await handle_change_language(update, context)
        return
    
    user_id = update.effective_user.id
    
    log_user_action(user_id, "text_message", update.message.text[:50])
    
    # Get user session
    session = db.get_user_session(user_id)
    
    if not session:
        # No active session, show menu options
        user = db.get_user(user_id)
        if user:
            # User is registered, show main menu
            keyboard = [
                [InlineKeyboardButton("📚 Browse Services", callback_data="browse_services")],
                [InlineKeyboardButton("📊 My Dashboard", callback_data="show_dashboard")],
                [InlineKeyboardButton("🤝 Referrals", callback_data="show_referrals")],
                [InlineKeyboardButton("❓ Help", callback_data="help_menu")],
                [InlineKeyboardButton("🌐 Language", callback_data="change_language")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Hi! I don't understand that message. Please use the menu below:",
                reply_markup=reply_markup
            )
        else:
            # User not registered, suggest starting
            await update.message.reply_text(
                "Hi! I don't understand. Please use /start to begin registration."
            )
        return
    
    current_step = session['current_step']
    
    try:
        # Registration steps
        if current_step in ['registration_name', 'registration_email', 'registration_phone', 'registration_country', 'registration_telegram']:
            await handle_registration_steps(update, context)
        
        # Payment steps
        elif current_step == 'entering_tx_hash':
            await handle_tx_hash_input(update, context)
        elif current_step == 'entering_order_id':  # <-- Add this
            await handle_order_id_input(update, context)

        # Admin steps
        elif current_step == 'admin_broadcast' and is_admin(user_id):
            await handle_broadcast_message(update, context)
        
        # Profile update steps
        elif current_step == 'updating_phone':
            phone = update.message.text.strip()
            if db.update_user_phone(user_id, phone):
                await update.message.reply_text("✅ Phone number updated successfully!")
                await handle_show_dashboard(update, context)
            else:
                await update.message.reply_text("❌ Failed to update phone number. Please try again.")
            db.clear_user_session(user_id)
        
        elif current_step == 'updating_country':
            country = update.message.text.strip()
            if db.update_user_country(user_id, country):
                await update.message.reply_text("✅ Country updated successfully!")
                await handle_show_dashboard(update, context)
            else:
                await update.message.reply_text("❌ Failed to update country. Please try again.")
            db.clear_user_session(user_id)
        
        else:
            await update.message.reply_text(
                "I'm not sure what you mean. Please use the buttons or commands."
            )
    
    except Exception as e:
        logger.error(f"Text message handling error: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads (receipts)"""
    user_id = update.effective_user.id

    log_user_action(user_id, "photo_upload")

    # Get user session
    session = db.get_user_session(user_id)

    if session and session['current_step'] in ['waiting_receipt', 'uploading_receipt']:
        await handle_receipt_upload(update, context)
    else:
        await update.message.reply_text(
            "I'm not expecting a photo right now. Please use the menu buttons."
        )

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found. Please check your .env file.")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(CallbackQueryHandler(handle_binance_method, pattern="^binance_(payid|wallet)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start scheduler
    start_scheduler(application.bot)
    
    # Create receipts directory
    os.makedirs("receipts", exist_ok=True)
    
    logger.info("Trading Mentor Bot started successfully!")
    logger.info(f"Admin IDs: {ADMIN_IDS}")
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

