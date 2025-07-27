import schedule
import time
import asyncio
import logging
from datetime import datetime, timedelta
from database import db
from email_service import email_service
from config import SERVICES

logger = logging.getLogger(__name__)

class BotScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.setup_jobs()
    
    def setup_jobs(self):
        """Setup scheduled jobs"""
        # Daily jobs
        schedule.every().day.at("09:00").do(self.check_expiring_subscriptions)
        schedule.every().day.at("10:00").do(self.send_renewal_reminders)
        schedule.every().day.at("18:00").do(self.cleanup_old_sessions)
        
        # Weekly jobs
        schedule.every().sunday.at("10:00").do(self.send_weekly_stats)
        
        logger.info("Scheduled jobs setup complete")
    
    def check_expiring_subscriptions(self):
        """Check for subscriptions expiring soon"""
        try:
            # Check subscriptions expiring in 3 days
            expiring_soon = db.get_expiring_subscriptions(3)
            
            for subscription in expiring_soon:
                service_info = SERVICES.get(subscription['service'], {})
                service_name = service_info.get('name', subscription['service'])
                
                days_left = (subscription['expiry_date'] - datetime.now()).days
                
                # Send email reminder
                email_service.send_expiry_warning(
                    subscription['name'],
                    subscription['email'],
                    service_name,
                    days_left
                )
                
                logger.info(f"Sent expiry warning to user {subscription['user_id']}")
            
            # Disable expired subscriptions
            expired_query = """
            UPDATE subscriptions 
            SET status = 'expired' 
            WHERE status = 'active' AND expiry_date < CURRENT_TIMESTAMP
            """
            db.execute_query(expired_query)
            
            logger.info("Checked expiring subscriptions")
        except Exception as e:
            logger.error(f"Failed to check expiring subscriptions: {e}")
    
    def send_renewal_reminders(self):
        """Send renewal reminders to users with expired subscriptions"""
        try:
            # Get users with recently expired subscriptions (within 7 days)
            query = """
            SELECT s.*, u.name, u.email FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.status = 'expired' 
            AND s.expiry_date > CURRENT_TIMESTAMP - INTERVAL '7 days'
            AND s.expiry_date < CURRENT_TIMESTAMP
            """
            expired_subscriptions = db.execute_query(query, fetch=True)
            
            for subscription in expired_subscriptions:
                service_info = SERVICES.get(subscription['service'], {})
                service_name = service_info.get('name', subscription['service'])
                
                # Send renewal email
                subject = f"Renew Your {service_name} Subscription"
                body = f"""
                Dear {subscription['name']},

                Your {service_name} subscription expired recently. 

                Don't miss out on continuing your trading journey! 
                Renew now and get back to learning and earning.

                Return to the bot to renew: [Bot Link]

                Best regards,
                Trading Mentor Team
                """
                
                email_service.send_email(subscription['email'], subject, body)
                
                logger.info(f"Sent renewal reminder to user {subscription['user_id']}")
        except Exception as e:
            logger.error(f"Failed to send renewal reminders: {e}")
    
    def cleanup_old_sessions(self):
        """Clean up old user sessions"""
        try:
            # Remove sessions older than 24 hours
            query = """
            DELETE FROM user_sessions 
            WHERE updated_at < CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """
            db.execute_query(query)
            
            logger.info("Cleaned up old sessions")
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
    
    def send_weekly_stats(self):
        """Send weekly statistics to admins"""
        try:
            from config import ADMIN_IDS
            
            # Get weekly stats
            user_stats = db.get_user_stats()
            revenue_stats = db.get_revenue_stats()
            
            # Get this week's revenue
            weekly_revenue_query = """
            SELECT SUM(amount) as weekly_revenue, COUNT(*) as weekly_payments
            FROM payments 
            WHERE status = 'approved' 
            AND verified_at > CURRENT_DATE - INTERVAL '7 days'
            """
            weekly_stats = db.execute_query(weekly_revenue_query, fetch=True)
            weekly_revenue = weekly_stats[0]['weekly_revenue'] if weekly_stats and weekly_stats[0]['weekly_revenue'] else 0
            weekly_payments = weekly_stats[0]['weekly_payments'] if weekly_stats else 0
            
            stats_message = f"""
            📊 **Weekly Stats Report**
            
            👥 **Users:**
            • Total: {user_stats['total_users'] if user_stats else 0}
            • New this week: {user_stats['new_this_week'] if user_stats else 0}
            • Active: {user_stats['active_users'] if user_stats else 0}
            
            💰 **Revenue:**
            • This week: ${weekly_revenue:,.2f} ({weekly_payments} payments)
            • Total: ${revenue_stats['total_revenue'] if revenue_stats else 0:,.2f}
            • Average payment: ${revenue_stats['avg_payment'] if revenue_stats else 0:,.2f}
            
            Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            """
            
            # Send to all admins
            for admin_id in ADMIN_IDS:
                asyncio.create_task(self.send_admin_message(admin_id, stats_message))
            
            logger.info("Sent weekly stats to admins")
        except Exception as e:
            logger.error(f"Failed to send weekly stats: {e}")
    
    async def send_admin_message(self, admin_id, message):
        """Send message to admin"""
        try:
            await self.bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send message to admin {admin_id}: {e}")
    
    def run_pending(self):
        """Run pending scheduled jobs"""
        schedule.run_pending()

def start_scheduler(bot):
    """Start the scheduler in a separate thread"""
    import threading
    
    scheduler = BotScheduler(bot)
    
    def scheduler_loop():
        while True:
            scheduler.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    
    logger.info("Scheduler started")
    return scheduler