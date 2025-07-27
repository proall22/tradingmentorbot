from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from database import db
from messages import get_message
from config import SERVICES
from utils import format_currency, create_referral_link, log_user_action

logger = logging.getLogger(__name__)

async def handle_show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user dashboard"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        if update.callback_query:
            await update.callback_query.answer("Please register first!")
            await update.callback_query.edit_message_text("Please register first using /start")
        else:
            await update.message.reply_text("Please register first using /start")
        return
    
    log_user_action(user_id, "view_dashboard")
    
    # Get active subscription
    active_sub = db.get_active_subscription(user_id)
    
    # Get referral stats
    referrals = db.get_user_referrals(user_id)
    referral_count = len(referrals) if referrals else 0
    
    # Create referral link
    bot_username = context.bot.username
    referral_link = create_referral_link(bot_username, user['referral_code'])
    
    # Format subscription info
    if active_sub:
        service_info = SERVICES.get(active_sub['service'], {})
        service_name = service_info.get('name', active_sub['service'])
        
        subscription_info = f"""
📦 **Active Subscription:**
• Service: {service_name}
• Status: ✅ Active
• Expires: {active_sub['expiry_date'].strftime('%B %d, %Y')}
• Amount Paid: {format_currency(active_sub['amount'])}
        """
    else:
        subscription_info = """
📦 **Subscription:**
• Status: ❌ No active subscription
• Ready to start your trading journey?
        """
    
    user_language = user.get('language', 'en')
    
    message = f"""
📊 **Your Dashboard**

👤 **Profile:**
• Name: {user['name']}
• Email: {user['email']}
• Phone: {user.get('phone', 'Not provided')}
• Country: {user.get('country', 'Not provided')}
• Member since: {user['joined_at'].strftime('%B %Y')}

{subscription_info}

🤝 **Referral Program:**
• Referrals: {referral_count}
• Your link: `{referral_link}`

💡 Share your referral link to earn rewards!
    """
    
    keyboard = []
    
    if not active_sub:
        keyboard.append([InlineKeyboardButton("🛒 Subscribe Now", callback_data="browse_services")])
    else:
        keyboard.append([InlineKeyboardButton("🔄 Renew Subscription", callback_data="browse_services")])
    
    keyboard.extend([
        [InlineKeyboardButton("🤝 Referral Details", callback_data="show_referrals")],
        [InlineKeyboardButton("📧 Update Profile", callback_data="update_profile")],
        [InlineKeyboardButton("🌐 Change Language", callback_data="change_language")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ])
    
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

async def handle_show_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral program details"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        if update.callback_query:
            await update.callback_query.answer("Please register first!")
            await update.callback_query.edit_message_text("Please register first using /start")
        else:
            await update.message.reply_text("Please register first using /start")
        return
    
    log_user_action(user_id, "view_referrals")
    
    # Get referral stats
    referrals = db.get_user_referrals(user_id)
    
    # Create referral link
    bot_username = context.bot.username
    referral_link = create_referral_link(bot_username, user['referral_code'])
    
    message = f"""
🤝 **Referral Program**

**Your Referral Link:**
`{referral_link}`

📊 **Statistics:**
• Total Referrals: {len(referrals) if referrals else 0}
• Pending Rewards: 0
• Total Earned: Coming soon

🎁 **How it works:**
1. Share your referral link with friends
2. When they register and make their first payment
3. You get 7 days added to your subscription
4. They get a welcome bonus too!

**Your Referrals:**
    """
    
    if referrals:
        for i, referral in enumerate(referrals[:10], 1):  # Show max 10
            status_emoji = "✅" if referral['status'] == 'completed' else "⏳"
            message += f"{i}. {status_emoji} {referral['referred_name']} - {referral['created_at'].strftime('%m/%d/%Y')}\n"
    else:
        message += "No referrals yet. Start sharing your link!"
    
    keyboard = [
        [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_referral_link")],
        [InlineKeyboardButton("📱 Share Link", url=f"https://t.me/share/url?url={referral_link}&text=Join me on Trading Mentor Bot!")],
        [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="show_dashboard")]
    ]
    
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

async def handle_copy_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle copy referral link"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        if update.callback_query:
            await update.callback_query.answer("Please register first!")
        else:
            await update.message.reply_text("Please register first using /start")
        return
    
    # Create referral link
    bot_username = context.bot.username
    referral_link = create_referral_link(bot_username, user['referral_code'])
    
    await update.callback_query.answer(
        f"Referral link: {referral_link}",
        show_alert=True
    )

async def handle_update_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile update request"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        if update.callback_query:
            await update.callback_query.answer("Please register first!")
            await update.callback_query.edit_message_text("Please register first using /start")
        else:
            await update.message.reply_text("Please register first using /start")
        return
    
    message = """
📧 **Update Profile**

What would you like to update?
    """
    
    keyboard = [
        [InlineKeyboardButton("📱 Phone Number", callback_data="update_phone")],
        [InlineKeyboardButton("🌍 Country", callback_data="update_country")],
        [InlineKeyboardButton("🌐 Language", callback_data="change_language")],
        [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="show_dashboard")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup
        )

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    from handlers.start_handler import show_main_menu
    await show_main_menu(update, context)