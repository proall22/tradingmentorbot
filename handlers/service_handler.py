from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import json
from database import db
from messages import get_message
from config import SERVICES
from utils import format_currency, calculate_savings, get_service_emoji, log_user_action

logger = logging.getLogger(__name__)

async def handle_browse_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available services"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        if update.callback_query:
            await update.callback_query.answer("Please register first!")
            await update.callback_query.edit_message_text("Please register first using /start")
        else:
            await update.message.reply_text("Please register first using /start")
        return
    
    user_language = user.get('language', 'en')
    
    log_user_action(user_id, "browse_services")
    
    message = get_message(user_language, 'choose_service')
    
    keyboard = []
    for service_key, service_info in SERVICES.items():
        emoji = get_service_emoji(service_key)
        name = service_info['name']
        price = service_info['prices']['1']  # Show 1-month price
        
        button_text = f"{emoji} {name} - from {format_currency(price)}"
        keyboard.append([InlineKeyboardButton(
            button_text, 
            callback_data=f"select_service_{service_key}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    
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

async def handle_select_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle service selection"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        if update.callback_query:
            await update.callback_query.answer("Please register first!")
            await update.callback_query.edit_message_text("Please register first using /start")
        else:
            await update.message.reply_text("Please register first using /start")
        return
    
    # Extract service from callback data
    service_key = update.callback_query.data.split('_', 2)[2]
    
    if service_key not in SERVICES:
        await update.callback_query.answer("Invalid service!")
        return
    
    user_language = user.get('language', 'en')
    service_info = SERVICES[service_key]
    
    log_user_action(user_id, "select_service", service_key)
    
    # Store service selection in session
    db.update_user_session(user_id, "selecting_duration", json.dumps({"service": service_key}))
    
    # Calculate savings
    price_1 = service_info['prices']['1']
    price_3 = service_info['prices']['3']
    price_6 = service_info['prices']['6']
    
    save_3 = (price_1 * 3) - price_3
    save_6 = (price_1 * 6) - price_6
    
    message = get_message(
        user_language,
        'choose_duration',
        service=service_info['name'],
        price_1=price_1,
        price_3=price_3,
        price_6=price_6,
        save_3=save_3,
        save_6=save_6
    )
    
    keyboard = [
        [InlineKeyboardButton(f"1 Month - {format_currency(price_1)}", callback_data=f"duration_1_{service_key}")],
        [InlineKeyboardButton(f"3 Months - {format_currency(price_3)} (Save {format_currency(save_3)}!)", callback_data=f"duration_3_{service_key}")],
        [InlineKeyboardButton(f"6 Months - {format_currency(price_6)} (Save {format_currency(save_6)}!)", callback_data=f"duration_6_{service_key}")],
        [InlineKeyboardButton("🔙 Back to Services", callback_data="browse_services")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_select_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duration selection"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        if update.callback_query:
            await update.callback_query.answer("Please register first!")
            await update.callback_query.edit_message_text("Please register first using /start")
        else:
            await update.message.reply_text("Please register first using /start")
        return
    
    # Parse callback data: duration_X_service
    callback_parts = update.callback_query.data.split('_')
    if len(callback_parts) < 3:
        await update.callback_query.answer("Invalid selection!")
        return
    
    duration = callback_parts[1]
    service_key = '_'.join(callback_parts[2:])  # Handle service keys with underscores
    
    logger.info(f"Duration selection - Duration: {duration}, Service: {service_key}")
    
    if service_key not in SERVICES or duration not in ['1', '3', '6']:
        await update.callback_query.answer(f"Invalid selection! Service: {service_key}, Duration: {duration}")
        return
    
    user_language = user.get('language', 'en')
    service_info = SERVICES[service_key]
    amount = service_info['prices'][duration]

     # --- Discount Logic ---
    # Service discount
    service_discount = service_info.get('discount', 0)
    # Referral discount
    completed_referrals = db.count_completed_referrals(user_id)
    referral_discount = completed_referrals // 100  # $1 per 100 completed referrals

    total_discount = service_discount + referral_discount
    final_amount = max(amount - total_discount, 0)
    
    log_user_action(user_id, "select_duration", f"{service_key}_{duration}m")
    
    # Store selection in session
    session_data = {
        "service": service_key,
        "duration": int(duration),
        "amount": amount,
        "original_amount": amount,
        "service_discount": service_discount,
        "referral_discount": referral_discount,
        "total_discount": total_discount
    }
    db.update_user_session(user_id, "selecting_payment", json.dumps(session_data))
    
    message = get_message(
        user_language,
        'choose_payment',
        service=service_info['name'],
        duration=duration,
        amount=amount
    )
    if total_discount > 0:
        message += f"\n\n💸 *Discount applied: ${total_discount}*"
    
    keyboard = [
        [InlineKeyboardButton("💰 Binance (Crypto)", callback_data="payment_binance")],
        [InlineKeyboardButton("🏦 CBE Bank", callback_data="payment_cbe")],
        [InlineKeyboardButton("📱 Telebirr", callback_data="payment_telebirr")],
        [InlineKeyboardButton("🏛️ Abyssinia Bank", callback_data="payment_other_bank")],
        [InlineKeyboardButton("🔙 Back to Duration", callback_data=f"select_service_{service_key}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

