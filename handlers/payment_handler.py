import hashlib
import hmac
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import json
import os
from database import db
from messages import get_message
from config import BINANCE_WALLET_ADDRESS, BINANCE_API_KEY, BINANCE_SECRET_KEY, SERVICES, PAYMENT_METHODS, SERVICE_GROUPS, BINANCE_USER_ID, PHONE_NUMBER, CBE_ACCOUNT, ABYSSINIA_ACCOUNT
import binance
import aiohttp
from utils import save_receipt_file, get_expiry_date, log_user_action, format_currency
from email_service import email_service
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def handle_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.callback_query.answer("Please register first!")
        return
    
    # Get session data
    session = db.get_user_session(user_id)
    if not session or session['current_step'] != 'selecting_payment':
        await update.callback_query.answer("Session expired. Please start over.")
        return
    
    session_data = session.get('temp_data', {})
    if isinstance(session_data, str):
        try:
            session_data = json.loads(session_data)
        except:
            session_data = {}
    
    payment_method = update.callback_query.data.split('_')[1]
    
    user_language = user.get('language', 'en')
    service_info = SERVICES[session_data['service']]
    
    log_user_action(user_id, "select_payment_method", payment_method)
    
    # Create subscription
    subscription_id = db.create_subscription(
        user_id=user_id,
        service=session_data['service'],
        duration=session_data['duration'],
        amount=session_data['amount'],
        payment_method=payment_method
    )
    
    if not subscription_id:
        await update.callback_query.answer("Failed to create subscription. Please try again.")
        return
    
    # Update session with subscription ID
    session_data['subscription_id'] = subscription_id
    session_data['payment_method'] = payment_method
    
    if payment_method == 'binance':
        # Binance payment: offer two options
        db.update_user_session(user_id, "waiting_binance_method", json.dumps(session_data))
        message = (
            "💰 *Binance Payment Options*\n\n"
            "You can pay using either:\n"
            "1️⃣ *Binance Pay ID* (Recommended, lower fees)\n"
            "2️⃣ *Wallet Address (BSC)*\n\n"
            "Paying with Binance Pay ID is cheaper and faster. "
            "Choose your preferred method below:"
        )
        keyboard = [
            [InlineKeyboardButton("🔢 Pay with Binance ID", callback_data="binance_payid")],
            [InlineKeyboardButton("🏦 Pay with Wallet Address", callback_data="binance_wallet")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return

    # Custom instructions for each bank
    payment_method_name = PAYMENT_METHODS.get(payment_method, payment_method)
    extra_info = ""
    if payment_method == "cbe":
        extra_info = f"\n\nSend payment to CBE Account: `{CBE_ACCOUNT}`"
    elif payment_method == "other":
        payment_method_name = "Abyssinia Bank"
        extra_info = f"\n\nSend payment to Abyssinia Account: `{ABYSSINIA_ACCOUNT}`"
    elif payment_method == "telebirr":
        extra_info = f"\n\nSend payment to Telebirr Number: `{PHONE_NUMBER}`"

    message = get_message(
        user_language,
        'bank_payment',
        amount=session_data['amount'],
        payment_method=payment_method_name
    ) + extra_info + "\n\n⚠️ Please upload your receipt within 1 hour, or your pending payment will expire."

    # Save as pending payment with expiry
    db.update_user_session(user_id, "waiting_receipt", json.dumps(session_data))
    # Save pending payment with expiry timestamp
    expiry_time = datetime.now() + timedelta(hours=1)
    session_data['pending_expiry'] = expiry_time.isoformat()
    db.update_user_session(user_id, "waiting_receipt", json.dumps(session_data))

    keyboard = [
        [InlineKeyboardButton("📎 Upload Receipt", callback_data="upload_receipt")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_binance_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.callback_query.answer("Please register first!")
        return
    session = db.get_user_session(user_id)
    if not session or session['current_step'] != 'waiting_binance_method':
        await update.callback_query.answer("Session expired. Please start over.")
        return
    session_data = session.get('temp_data', {})
    if isinstance(session_data, str):
        try:
            session_data = json.loads(session_data)
        except:
            session_data = {}

    user_language = user.get('language', 'en')
    method = update.callback_query.data
    if method == "binance_payid":
        db.update_user_session(user_id, "entering_order_id", json.dumps(session_data))
        binance_id = BINANCE_USER_ID
        message = (
            f"🔢 *Binance Pay ID Payment*\n\n"
            f"Send exactly ${session_data['amount']} USDT to Binance Pay ID: `{binance_id}`\n"
            "This method is recommended for lower fees and instant confirmation.\n\n"
            "After payment, enter your Binance Order ID (not TX Hash) and upload a screenshot of your payment.\n"
            "Click below when done."
        )
        keyboard = [
            [InlineKeyboardButton("✅ I've sent the payment", callback_data="submit_order_id")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    elif method == "binance_wallet":
        db.update_user_session(user_id, "entering_tx_hash", json.dumps(session_data))
        message = (
            f"🏦 *Binance Wallet Address Payment*\n\n"
            f"Send exactly ${session_data['amount']} USDT to this BSC address:\n"
            f"`{BINANCE_WALLET_ADDRESS}`\n"
            "After payment, copy the TX Hash and upload a screenshot of your payment.\n"
            "Click below when done."
        )
        keyboard = [
            [InlineKeyboardButton("✅ I've sent the payment", callback_data="submit_tx_hash")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.answer("Invalid selection!")

async def handle_submit_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Binance PayID order ID submission"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.callback_query.answer("Please register first!")
        return

    user_language = user.get('language', 'en')
    session = db.get_user_session(user_id)
    if session:
        session_data = session.get('temp_data', {})
        if isinstance(session_data, str):
            try:
                session_data = json.loads(session_data)
            except:
                session_data = {}
        
        db.update_user_session(user_id, "entering_order_id", json.dumps(session_data))

    message = get_message(user_language, 'ask_order_id') + "\n\n*You must also upload a screenshot after entering the Order ID.*"
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_order_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle order ID text input for Binance PayID"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("Please register first!")
        return

    session = db.get_user_session(user_id)
    if not session or session['current_step'] != 'entering_order_id':
        await update.message.reply_text("Session expired. Please start over.")
        return

    order_id = update.message.text.strip()
    session_data = session.get('temp_data', {})
    if isinstance(session_data, str):
        try:
            session_data = json.loads(session_data)
        except:
            session_data = {}

    log_user_action(user_id, "submit_order_id", order_id[:16] + "...")

    
    if not order_id.isdigit():
        await update.message.reply_text("❌ Invalid Order ID format. Please check and try again.")
        return

    # Store order ID in session and ask for screenshot
    session_data['order_id'] = order_id
    db.update_user_session(user_id, "waiting_receipt", json.dumps(session_data))
    await update.message.reply_text(
        "✅ Order ID received.\n\nNow, please upload a screenshot of your payment for verification.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]])
    )

async def handle_submit_tx_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle TX hash submission"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.callback_query.answer("Please register first!")
        return
    
    user_language = user.get('language', 'en')
    
    
    session = db.get_user_session(user_id)
    if session:
        session_data = session.get('temp_data', {})
        if isinstance(session_data, str):
            try:
                session_data = json.loads(session_data)
            except:
                session_data = {}
        db.update_user_session(user_id, "entering_tx_hash", json.dumps(session_data))
    
    message = get_message(user_language, 'ask_tx_hash') + "\n\n*You must also upload a screenshot after entering the TX Hash.*"
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_tx_hash_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle TX hash text input"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("Please register first!")
        return
    
    session = db.get_user_session(user_id)
    if not session or session['current_step'] != 'entering_tx_hash':
        await update.message.reply_text("Session expired. Please start over.")
        return
    
    tx_hash = update.message.text.strip()
    session_data = session.get('temp_data', {})
    if isinstance(session_data, str):
        try:
            session_data = json.loads(session_data)
        except:
            session_data = {}
    
    log_user_action(user_id, "submit_tx_hash", tx_hash[:16] + "...")
    
    
    if not (len(tx_hash) >= 32 and all(c in "0123456789abcdefABCDEF" for c in tx_hash.replace("0x", ""))):
        await update.message.reply_text("❌ Invalid TX Hash format. Please check and try again.")
        return
    
    
    session_data['tx_hash'] = tx_hash
    db.update_user_session(user_id, "waiting_receipt", json.dumps(session_data))
    await update.message.reply_text(
        "✅ TX Hash received.\n\nNow, please upload a screenshot of your payment for verification.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]])
    )

async def handle_upload_receipt_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle receipt upload request"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.callback_query.answer("Please register first!")
        return
    
    user_language = user.get('language', 'en')
    
    # Check session data
    session = db.get_user_session(user_id)
    if session:
        session_data = session.get('temp_data', {})
        if isinstance(session_data, str):
            try:
                session_data = json.loads(session_data)
            except:
                session_data = {}
        db.update_user_session(user_id, "uploading_receipt", json.dumps(session_data))
    
    message = get_message(user_language, 'upload_receipt')
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup)

async def handle_receipt_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle receipt file upload"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("Please register first!")
        return
    
    session = db.get_user_session(user_id)
    session_data = session.get('temp_data', {}) if session else {}
    if isinstance(session_data, str):
        try:
            session_data = json.loads(session_data)
        except:
            session_data = {}

    # Check expiry
    expiry_str = session_data.get('pending_expiry')
    if expiry_str:
        expiry_time = datetime.fromisoformat(expiry_str)
        if datetime.now() > expiry_time:
            db.clear_user_session(user_id)
            await update.message.reply_text(
                "❌ Your pending payment has expired. Please start again.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
            )
            return

    # Check if message has photo
    if not update.message.photo:
        await update.message.reply_text("Please upload an image file.")
        return
    
    # Save receipt file
    photo_file = await update.message.photo[-1].get_file()
    file_content = await photo_file.download_as_bytearray()
    payment_id = db.create_payment(
        user_id=user_id,
        subscription_id=session_data.get('subscription_id'),
        payment_method=session_data.get('payment_method'),
        amount=session_data.get('amount'),
        receipt_path=None
    )
    receipt_path = save_receipt_file(file_content, user_id, payment_id)
    # Update payment with receipt path
    db.execute_query("UPDATE payments SET receipt_path = %s WHERE id = %s", (receipt_path, payment_id))

    # Send to admin for approval
    admin_message = (
        f"🔔 **New Payment Received**\n\n"
        f"👤 **User:** {user['name']}\n"
        f"📱 **Telegram:** @{user.get('telegram_username', 'N/A')}\n"
        f"📧 **Email:** {user.get('email', 'N/A')}\n"
        f"📞 **Phone:** {user.get('phone', 'N/A')}\n"
        f"💳 **Method:** {session_data.get('payment_method')}\n"
        f"💰 **Amount:** {format_currency(session_data.get('amount'))}\n"
        f"🆔 **Payment ID:** {payment_id}\n\n"
        f"Please review and approve in the admin panel."
    )
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{payment_id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{payment_id}")],
        [InlineKeyboardButton("👨‍💼 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    from config import ADMIN_IDS
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

    await update.message.reply_text(
        "✅ Receipt uploaded! Your payment is pending admin approval. You will be notified once approved.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
    )
    db.clear_user_session(user_id)

async def handle_cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment cancellation"""
    user_id = update.effective_user.id
    
    # Clear session
    db.clear_user_session(user_id)
    
    keyboard = [[InlineKeyboardButton("📚 Browse Services", callback_data="browse_services")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "Payment cancelled. You can try again anytime.",
        reply_markup=reply_markup
    )

async def notify_admin_new_payment(context: ContextTypes.DEFAULT_TYPE, user, session_data, payment_id):
    """Notify admin about new payment"""
    from config import ADMIN_IDS
    
    service_info = SERVICES[session_data['service']]
    
    admin_message = f"""
🔔 **New Payment Received**

👤 **User:** {user['name']} ({user['email']})
📦 **Service:** {service_info['name']}
⏰ **Duration:** {session_data['duration']} month(s)
💰 **Amount:** {format_currency(session_data['amount'])}
💳 **Method:** {session_data['payment_method']}
🆔 **Payment ID:** {payment_id}

Please review and approve in the admin panel.
    """
    
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{payment_id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{payment_id}")],
        [InlineKeyboardButton("👨‍💼 Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")