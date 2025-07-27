from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
import logging
import json
from database import db
from messages import get_message
from utils import generate_referral_code, create_referral_link, validate_email, log_user_action, validate_phone, clean_country_input
from email_service import email_service

logger = logging.getLogger(__name__)

async def handle_registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start registration process"""
    user_id = update.effective_user.id
    user_language = 'en'  # Default, will be updated if user changes
    
    log_user_action(user_id, "registration_start")
    
    # Update session
    db.update_user_session(user_id, "registration_name")
    
    message = get_message(user_language, 'registration_start')
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Add /help to custom keyboard before registration starts
    recovery_keyboard = [
        [KeyboardButton("/start"), KeyboardButton("/help")]
    ]
    reply_markup_recovery = ReplyKeyboardMarkup(recovery_keyboard, resize_keyboard=True)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
        await context.bot.send_message(
            chat_id=user_id,
            text="If you need help, click /help.",
            reply_markup=reply_markup_recovery
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup
        )
        await update.message.reply_text(
            "If you need help, click /help.",
            reply_markup=reply_markup_recovery
        )

async def handle_email_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle email option selection"""
    user_id = update.effective_user.id
    user_language = 'en'
    
    session = db.get_user_session(user_id)
    if not session:
        await update.callback_query.edit_message_text("Session expired. Please start with /start")
        return
    
    temp_data = session.get('temp_data') or {}
    if isinstance(temp_data, str):
        try:
            temp_data = json.loads(temp_data)
        except:
            temp_data = {}
    
    if update.callback_query.data == "add_email_yes":
        # Ask for email
        db.update_user_session(user_id, "registration_email", json.dumps(temp_data))
        message = get_message(user_language, 'ask_email')
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        # Skip email, go to telegram
        temp_data['email'] = None
        db.update_user_session(user_id, "registration_telegram_option", json.dumps(temp_data))
        
        message = get_message(user_language, 'ask_telegram_username')
        keyboard = [
            [InlineKeyboardButton("✅ Yes, add Telegram", callback_data="add_telegram_yes")],
            [InlineKeyboardButton("❌ No, skip", callback_data="add_telegram_no")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)

async def handle_telegram_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle telegram option selection"""
    user_id = update.effective_user.id
    user_language = 'en'
    
    session = db.get_user_session(user_id)
    if not session:
        await update.callback_query.edit_message_text("Session expired. Please start with /start")
        return
    
    temp_data = session.get('temp_data') or {}
    if isinstance(temp_data, str):
        try:
            temp_data = json.loads(temp_data)
        except:
            temp_data = {}
    
    if update.callback_query.data == "add_telegram_yes":
        # Ask for telegram username
        db.update_user_session(user_id, "registration_telegram", json.dumps(temp_data))
        message = get_message(user_language, 'ask_telegram_username_input')
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        # Skip telegram, go to privacy
        temp_data['telegram_username'] = None
        db.update_user_session(user_id, "registration_privacy", json.dumps(temp_data))
        
        message = get_message(user_language, 'ask_privacy_permission')
        keyboard = [
            [InlineKeyboardButton("✅ Yes, allow contact", callback_data="privacy_allow")],
            [InlineKeyboardButton("❌ No, limited contact", callback_data="privacy_deny")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)

async def handle_privacy_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle privacy option selection"""
    user_id = update.effective_user.id
    user_language = 'en'
    
    session = db.get_user_session(user_id)
    if not session:
        await update.callback_query.edit_message_text("Session expired. Please start with /start")
        return
    
    temp_data = session.get('temp_data') or {}
    if isinstance(temp_data, str):
        try:
            temp_data = json.loads(temp_data)
        except:
            temp_data = {}
    
    privacy_allowed = update.callback_query.data == "privacy_allow"
    temp_data['privacy_allowed'] = privacy_allowed
    
    # Go to phone
    db.update_user_session(user_id, "registration_phone", json.dumps(temp_data))
    message = get_message(user_language, 'ask_phone')
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup)

async def handle_registration_steps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle registration step by step"""
    user_id = update.effective_user.id
    user_language = 'en'
    
    # Get current session
    session = db.get_user_session(user_id)
    if not session:
        await update.message.reply_text("Session expired. Please start with /start")
        return
    
    current_step = session['current_step']
    temp_data = session.get('temp_data') or {}
    
    # Parse temp_data if it's a string (JSON)
    if isinstance(temp_data, str):
        try:
            temp_data = json.loads(temp_data)
        except:
            temp_data = {}
    
    if current_step == "registration_name":
        # Store name and ask for email option
        name = update.message.text.strip()
        if not name.isalpha() or len(name) < 2:
            await show_error_with_menu(update, "Please provide a valid name (letters only, at least 2 characters).")
            return
        temp_data['name'] = name
        db.update_user_session(user_id, "registration_email_option", json.dumps(temp_data))
        
        message = get_message(user_language, 'ask_email_optional')
        keyboard = [
            [InlineKeyboardButton("✅ Yes, add email", callback_data="add_email_yes")],
            [InlineKeyboardButton("❌ No, skip", callback_data="add_email_no")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        
    elif current_step == "registration_email":
        # Store email and ask for telegram option
        email = update.message.text.strip().lower()
        
        if not validate_email(email):
            await update.message.reply_text(
                get_message(user_language, 'error_invalid_email')
            )
            return
        
        # Check if email already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            await update.message.reply_text(
                get_message(user_language, 'error_email_exists')
            )
            return
        
        temp_data['email'] = email
        db.update_user_session(user_id, "registration_telegram_option", json.dumps(temp_data))
        
        message = get_message(user_language, 'ask_telegram_username')
        keyboard = [
            [InlineKeyboardButton("✅ Yes, add Telegram", callback_data="add_telegram_yes")],
            [InlineKeyboardButton("❌ No, skip", callback_data="add_telegram_no")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        
    elif current_step == "registration_telegram":
        # Store telegram and ask for privacy
        telegram_username = update.message.text.strip().replace('@', '')
        temp_data['telegram_username'] = telegram_username
        db.update_user_session(user_id, "registration_privacy", json.dumps(temp_data))
        
        message = get_message(user_language, 'ask_privacy_permission')
        keyboard = [
            [InlineKeyboardButton("✅ Yes, allow contact", callback_data="privacy_allow")],
            [InlineKeyboardButton("❌ No, limited contact", callback_data="privacy_deny")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        
    elif current_step == "registration_phone":
        # Store phone and ask for country
        phone = update.message.text.strip()
        if not validate_phone(phone):
            await show_error_with_menu(update, "Please enter a valid Ethiopian phone number (09..., 07..., or +251...).")
            return
        temp_data['phone'] = phone
        db.update_user_session(user_id, "registration_country", json.dumps(temp_data))
        
        message = get_message(user_language, 'ask_country')
        await update.message.reply_text(message)
        
    elif current_step == "registration_country":
        # Complete registration
        country = clean_country_input(update.message.text.strip())
        if not country or len(country) < 2:
            await show_error_with_menu(update, "Please enter a valid country name.")
            return
        temp_data['country'] = country
        
        # Generate referral code
        referral_code = generate_referral_code(user_id)
        
        # Check for referral in session
        referred_by = None
        referrer = None
        if temp_data.get('referral_code'):
            referrer = db.get_user_by_referral_code(temp_data['referral_code'])
            if referrer:
                referred_by = referrer['user_id']

        start_session = db.get_user_session(user_id)
        if start_session and start_session.get('temp_data'):
            start_data = start_session['temp_data']
            if isinstance(start_data, str):
                try:
                    start_data = json.loads(start_data)
                except:
                 start_data = {}
            if start_data.get('referral_code'):
                referrer = db.get_user_by_referral_code(start_data['referral_code'])
                if referrer:
                    referred_by = referrer['user_id']
        
        # Also check if there's a referral code in current temp_data
        if temp_data.get('referral_code'):
            referrer = db.get_user_by_referral_code(temp_data['referral_code'])
            if referrer:
                referred_by = referrer['user_id']
        
        # Get telegram username from update
        telegram_username = temp_data.get('telegram_username', '')
        if not telegram_username and update.effective_user.username:
            telegram_username = update.effective_user.username
        
        # Create user
        try:
            db.create_user(
                user_id=user_id,
                name=temp_data['name'],
                email=temp_data.get('email'),
                phone=temp_data['phone'],
                country=temp_data['country'],
                referral_code=referral_code,
                telegram_username=telegram_username,
                privacy_allowed=temp_data.get('privacy_allowed', False)
            )
            # Notify all admins with updated panel
            from config import ADMIN_IDS
            from handlers.admin_handler import handle_admin_panel
            for admin_id in ADMIN_IDS:
                try:
                    fake_update = type('FakeUpdate', (), {
                        'effective_user': type('User', (), {'id': admin_id})(),
                        'message': None,
                        'callback_query': None
                    })()
                    await handle_admin_panel(fake_update, context)
                except Exception as e:
                    logger.error(f"Failed to update admin panel for admin {admin_id}: {e}")  
            
            # Create referral if applicable
            if referred_by:
                db.create_referral(referred_by, user_id)
                db.create_referral(referred_by, user_id)
                log_user_action(user_id, "referred_by", referred_by)
            
            # Clear session
            db.clear_user_session(user_id)
            
            # Send welcome email if email provided
            if temp_data.get('email'):
                try:
                    email_service.send_welcome_email(temp_data['name'], temp_data['email'])
                except Exception as e:
                    logger.error(f"Failed to send welcome email: {e}")
            
            # Create referral link
            bot_username = context.bot.username
            referral_link = create_referral_link(bot_username, referral_code)
            
            # Format status messages
            email_status = get_message(user_language, 'email_provided', email=temp_data['email']) if temp_data.get('email') else get_message(user_language, 'email_not_provided')
            telegram_status = get_message(user_language, 'telegram_provided', username=telegram_username) if telegram_username else get_message(user_language, 'telegram_not_provided')
            privacy_status = get_message(user_language, 'privacy_allowed') if temp_data.get('privacy_allowed') else get_message(user_language, 'privacy_denied')
            
            # Show completion message
            message = get_message(
                user_language, 
                'registration_complete',
                name=temp_data['name'],
                email_status=email_status,
                telegram_status=telegram_status,
                privacy_status=privacy_status,
                referral_link=referral_link
            )
            
            # Custom keyboard (persistent menu)
            custom_keyboard = [
                [KeyboardButton("📚 Browse Services"), KeyboardButton("📊 Dashboard")],
                [KeyboardButton("🤝 Referrals"), KeyboardButton("❓ Help")],
                [KeyboardButton("🌐 Language")]
            ]
            reply_markup_custom = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
            
            # Send the custom keyboard (persistent menu)
            await update.message.reply_text(
                "👇 Use the menu below for quick access to main features.",
                reply_markup=reply_markup_custom
            )
            
            keyboard = [
                [InlineKeyboardButton("📚 Browse Services", callback_data="browse_services")],
                [InlineKeyboardButton("📊 My Dashboard", callback_data="show_dashboard")],
                [InlineKeyboardButton("🤝 Referral Program", callback_data="show_referrals")]
            ]
            reply_markup_inline = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup_inline
            )
            
            log_user_action(user_id, "registration_complete")
            
            # Notify all admins with updated panel
            from config import ADMIN_IDS
            from handlers.admin_handler import handle_admin_panel
            for admin_id in ADMIN_IDS:
                try:
                    # Create a fake Update object for each admin
                    class FakeUpdate:
                        def __init__(self, admin_id):
                            self.effective_user = type('User', (), {'id': admin_id})()
                            self.message = None
                            self.callback_query = None
                    fake_update = FakeUpdate(admin_id)
                    await handle_admin_panel(fake_update, context)
                except Exception as e:
                    logger.error(f"Failed to update admin panel for admin {admin_id}: {e}")
            return
            
        except Exception as e:
            logger.error(f"Registration failed for user {user_id}: {e}")
            user = db.get_user(user_id)
            if not user:
               recovery_keyboard = [
                [KeyboardButton("/start"), KeyboardButton("/help")]
               ]

            reply_markup_recovery = ReplyKeyboardMarkup(recovery_keyboard, resize_keyboard=True)
            await update.message.reply_text(
                get_message(user_language, 'error_general'), 
                reply_markup=reply_markup_recovery
            )
        # else:
        #     # Registered users get normal error message
        #     await update.message.reply_text(
        #         get_message(user_language, 'error_general')
        #     )

async def handle_cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle registration cancellation"""
    user_id = update.effective_user.id
    
    # Clear session
    db.clear_user_session(user_id)
    
    await update.callback_query.edit_message_text(
        "Registration cancelled. You can start again anytime with /start"
    )

async def show_error_with_menu(update, error_message):
    """Show error with quick access menu"""
    keyboard = [
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        [InlineKeyboardButton("🔄 Restart Registration", callback_data="register_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"❌ {error_message}\n\nYou can use the menu below:",
        reply_markup=reply_markup
    )

async def handle_resume_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = db.get_user_session(user_id)
    if session:
        # Continue from last step
        await handle_registration_steps(update, context)
    else:
        await handle_registration_start(update, context)

