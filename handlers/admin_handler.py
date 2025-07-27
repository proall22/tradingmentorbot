from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import json
from database import db
from messages import get_message
from config import SERVICES, SERVICE_GROUPS, TELERAM_USERNAME
from utils import is_admin, format_currency, get_expiry_date, log_user_action
from email_service import email_service
from datetime import datetime

logger = logging.getLogger(__name__)

async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("Access denied!")
        else:
            await update.message.reply_text("Access denied!")
        return

    log_user_action(user_id, "admin_panel_access")

    # Get statistics
    user_stats = db.get_user_stats()
    revenue_stats = db.get_revenue_stats()
    pending_payments = db.get_pending_payments()

    message = f"""
👨‍💼 **Admin Panel**

📊 **User Statistics:**
• Total Users: {user_stats['total_users'] if user_stats else 0}
• New This Week: {user_stats['new_this_week'] if user_stats else 0}
• Active Users: {user_stats['active_users'] if user_stats else 0}

💰 **Revenue Statistics:**
• Total Revenue: {format_currency(revenue_stats['total_revenue'] or 0) if revenue_stats else '$0.00'}
• Total Payments: {revenue_stats['total_payments'] if revenue_stats else 0}
• Average Payment: {format_currency(revenue_stats['avg_payment'] or 0) if revenue_stats else '$0.00'}

⏳ **Pending Payments:** {len(pending_payments) if pending_payments else 0}
    """

    keyboard = [
        [InlineKeyboardButton(f"💳 Pending Payments ({len(pending_payments) if pending_payments else 0})", callback_data="admin_pending_payments")],
        [InlineKeyboardButton("👥 All Users", callback_data="admin_all_users")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📤 Broadcast to User", callback_data="admin_broadcast_user")],
        [InlineKeyboardButton("📊 Service Stats", callback_data="admin_service_stats")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Add persistent custom keyboard for admin (quick access)
    custom_keyboard = [
        [KeyboardButton("👥 All Users"), KeyboardButton("💳 Pending Payments")],
        [KeyboardButton("📢 Broadcast"), KeyboardButton("📊 Service Stats")],
        [KeyboardButton("📤 Broadcast to User"), KeyboardButton("🔙 Back to Main Menu")],
        [KeyboardButton("🏠 Main Menu")]
    ]
    reply_markup_custom = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

    # Send both custom keyboard and inline menu
    if update.message:
        await update.message.reply_text(
            "👇 Use the menu below for quick access to admin features.",
            reply_markup=reply_markup_custom
        )
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        # If triggered by callback, send custom keyboard first
        await context.bot.send_message(
            chat_id=user_id,
            text="👇 Use the menu below for quick access to admin features.",
            reply_markup=reply_markup_custom
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending payments (admin can approve/reject)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("Access denied!")
        else:
            await update.message.reply_text("Access denied!")
        return

    pending_payments = db.get_pending_payments()

    if not pending_payments:
        message = "✅ No pending payments!"
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
    else:
        message = f"💳 **Pending Payments ({len(pending_payments)})**\n\n"
        keyboard = []
        for payment in pending_payments[:10]:  # Show max 10 at a time
            service_info = SERVICES.get(payment['service'], {})
            service_name = service_info.get('name', payment['service'])
            payment_text = f"""
**Payment #{payment['id']}**
👤 {payment['name']} ({payment['email']})
📦 {service_name} ({payment['duration']}m)
💰 {format_currency(payment['amount'])}
💳 {payment['payment_method']}
📅 {payment['created_at'].strftime('%m/%d %H:%M')}
            """
            message += payment_text + "\n"
            keyboard.append([
                InlineKeyboardButton(f"✅ Approve #{payment['id']}", callback_data=f"approve_payment_{payment['id']}"),
                InlineKeyboardButton(f"❌ Reject #{payment['id']}", callback_data=f"reject_payment_{payment['id']}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a payment and notify user (and email)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("Access denied!")
        else:
            await update.message.reply_text("Access denied!")
        return

    payment_id = int(update.callback_query.data.split('_')[2])
    payment = db.get_payment(payment_id)
    if not payment:
        await update.callback_query.answer("Payment not found.")
        return

    # Activate subscription
    subscription = db.get_active_subscription(payment['user_id'])
    if subscription:
        service = subscription['service']
        duration = str(subscription['duration'])
        group_id = SERVICE_GROUPS.get(service, {}).get(duration)
        if group_id:
            try:
                await context.bot.invite_chat_member(group_id, payment['user_id'])
            except Exception as e:
                logger.error(f"Failed to add user {payment['user_id']} to group {group_id}: {e}")

    try:
        db.approve_payment(payment_id, user_id)
        subscription_query = "SELECT * FROM subscriptions WHERE id = %s"
        subscription_result = db.execute_query(subscription_query, (payment['subscription_id'],), fetch=True)
        if subscription_result:
            subscription = subscription_result[0]
            start_date = datetime.now()
            expiry_date = get_expiry_date(subscription['duration'])
            db.activate_subscription(subscription['id'], start_date, expiry_date)
            user = db.get_user(payment['user_id'])
            if user:
                service_info = SERVICES.get(subscription['service'], {})
                service_name = service_info.get('name', subscription['service'])
                # Send confirmation email
                email_service.send_payment_confirmation(
                    user['name'],
                    user['email'],
                    service_name,
                    subscription['duration'],
                    payment['amount']
                )
                # Send confirmation to user
                user_language = user.get('language', 'en')
                bot_message = get_message(
                    user_language,
                    'bot_payment_approved',
                    service=service_name,
                    duration=subscription['duration'],
                    amount=payment['amount'],
                    expiry_date=expiry_date.strftime('%B %d, %Y')
                )
                keyboard = [[InlineKeyboardButton("📊 My Dashboard", callback_data="show_dashboard")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                try:
                    await context.bot.send_message(
                        chat_id=payment['user_id'],
                        text=bot_message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user {payment['user_id']}: {e}")

        log_user_action(user_id, "approve_payment", payment_id)
        await update.callback_query.answer("✅ Payment approved!")
        await handle_pending_payments(update, context)
    except Exception as e:
        logger.error(f"Failed to approve payment {payment_id}: {e}")
        await update.callback_query.answer("❌ Failed to approve payment!")

async def handle_reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reject a payment and notify user (and email)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("Access denied!")
        else:
            await update.message.reply_text("Access denied!")
        return

    payment_id = int(update.callback_query.data.split('_')[2])
    payment = db.get_payment(payment_id)
    if not payment:
        await update.callback_query.answer("Payment not found!")
        return

    if payment['status'] != 'pending':
        await update.callback_query.answer("Payment already processed!")
        return

    try:
        db.reject_payment(payment_id, user_id)
        user = db.get_user(payment['user_id'])
        if user:
            user_language = user.get('language', 'en')
            user_message = get_message(
                user_language,
                'bot_payment_rejected',
                amount=payment['amount'],
                payment_method=payment['payment_method']
            )
            # Prepare support contact
            SUPPORT_USERNAME = f"{TELERAM_USERNAME}" if TELERAM_USERNAME else "support"
            keyboard = [
                [InlineKeyboardButton("📚 Try Again", callback_data="browse_services")],
                [InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{SUPPORT_USERNAME}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await context.bot.send_message(
                    chat_id=payment['user_id'],
                    text=user_message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Failed to notify user {payment['user_id']}: {e}")
            # Send rejection email
            email_service.send_email(
                user['email'],
                "Payment Rejected",
                f"Dear {user['name']},\n\nYour payment was rejected. Please contact support or try again.\n\nBest regards,\nTrading Mentor Team"
            )
        log_user_action(user_id, "reject_payment", payment_id)
        await update.callback_query.answer("❌ Payment rejected!")
        await handle_pending_payments(update, context)
    except Exception as e:
        logger.error(f"Failed to reject payment {payment_id}: {e}")
        await update.callback_query.answer("❌ Failed to reject payment!")

async def handle_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all users"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("Access denied!")
        else:
            await update.message.reply_text("Access denied!")
        return
    
    users = db.get_all_users()
    
    if not users:
        message = "No users found!"
    else:
        message = f"👥 **All Users ({len(users)})**\n\n"
        
        for user in users[:20]:  # Show max 20 at a time
            active_sub = db.get_active_subscription(user['user_id'])
            status = "🟢 Active" if active_sub else "🔴 No subscription"
            
            message += f"""
**{user['name']}**
📧 {user['email']}
📱 {user.get('phone', 'N/A')}
🌍 {user.get('country', 'N/A')}
📅 {user['joined_at'].strftime('%m/%d/%Y')}
📊 {status}

            """
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    elif update.message:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        

async def handle_broadcast_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup broadcast message"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("Access denied!")
        else:
            await update.message.reply_text("Access denied!")
        return
    
    # Set session for broadcast
    db.update_user_session(user_id, "admin_broadcast", json.dumps({}))
    
    message = """
📢 **Broadcast Message**

Please type the message you want to send to all users.

Use these placeholders:
• {name} - User's name
• {service} - Current service
• {expiry} - Subscription expiry

Type your message:
    """
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    elif update.message:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message input"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("Access denied!")
        else:
            await update.message.reply_text("Access denied!")
        return
    
    session = db.get_user_session(user_id)
    if not session or session['current_step'] != 'admin_broadcast':
        await update.message.reply_text("Session expired. Please start over.")
        return
    
    broadcast_text = update.message.text.strip()
    
    # Get all active users
    users = db.get_all_users(status=True)
    
    if not users:
        await update.message.reply_text("No users found to broadcast to.")
        return
    
    # Clear session
    db.clear_user_session(user_id)
    
    # Send broadcast
    sent_count = 0
    failed_count = 0

    status_message = await update.message.reply_text(
        f"📢 Broadcasting to {len(users)} users...\n\nSent: 0\nFailed: 0"
    )
    
    for i, user in enumerate(users):
        try:
            # Get user's active subscription for personalization
            active_sub = db.get_active_subscription(user['user_id'])
            service_name = active_sub['service'].replace('_', ' ').title() if active_sub else 'None'
            expiry_date = active_sub['expiry_date'].strftime('%B %d, %Y') if active_sub else 'N/A'
            
            # Format message with user data
            personalized_message = broadcast_text.format(
                name=user['name'],
                service=service_name,
                expiry=expiry_date
            )
            
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=personalized_message,
                parse_mode='Markdown'
            )
            sent_count += 1
            
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user['user_id']}: {e}")
            failed_count += 1
        
        # Update status every 10 messages
        if (i + 1) % 10 == 0:
            try:
                await status_message.edit_text(
                    f"📢 Broadcasting to {len(users)} users...\n\nSent: {sent_count}\nFailed: {failed_count}\nProgress: {i + 1}/{len(users)}"
                )
            except:
                pass
    
    # Final status
    await status_message.edit_text(
        f"✅ Broadcast completed!\n\nSent: {sent_count}\nFailed: {failed_count}\nTotal: {len(users)}"
    )
    
    log_user_action(user_id, "broadcast_message", f"sent:{sent_count}_failed:{failed_count}")

async def handle_broadcast_user_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup broadcast to single user (choose from user list)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("Access denied!")
        else:
            await update.message.reply_text("Access denied!")
        return

    # Get all users (limit to 20 for menu)
    users = db.get_all_users()
    if not users:
        await update.message.reply_text("No users found!")
        return

    # Build inline keyboard with user names and IDs
    keyboard = []
    for user in users[:20]:
        display = f"{user['name']} ({user['user_id']})"
        keyboard.append([InlineKeyboardButton(display, callback_data=f"admin_broadcast_user_select_{user['user_id']}")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "📤 *Broadcast to User*\n\nSelect a user to send a direct message:"
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_broadcast_user_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt admin to enter message for selected user"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Access denied!")
        return

    # Extract target user_id from callback data
    target_user_id = int(update.callback_query.data.split('_')[-1])
    db.update_user_session(user_id, "admin_broadcast_user", json.dumps({"target_user_id": target_user_id}))

    target_user = db.get_user(target_user_id)
    if not target_user:
        await update.callback_query.edit_message_text("User not found.")
        return

    message = f"✉️ *Send Message to {target_user['name']} ({target_user_id})*\n\nType your message below:"
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_broadcast_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast to single user (send message)"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Access denied!")
        return

    session = db.get_user_session(user_id)
    if not session or session['current_step'] != 'admin_broadcast_user':
        await update.message.reply_text("Session expired. Please start over.")
        return

    temp_data = session.get('temp_data', {})
    target_id = temp_data.get('target_user_id')
    if not target_id:
        await update.message.reply_text("No user selected. Please start over.")
        return

    message_text = update.message.text.strip()
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=message_text,
            parse_mode='Markdown'
        )
        await update.message.reply_text(f"✅ Message sent to user {target_id}.")
    except Exception as e:
        logger.error(f"Failed to send broadcast to user {target_id}: {e}")
        await update.message.reply_text(f"❌ Failed to send message to user {target_id}.")
    db.clear_user_session(user_id)