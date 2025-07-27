import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta
from config import DATABASE_URL

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
        self.drop_and_recreate_tables()
        self.create_tables()
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise e
    
    def drop_and_recreate_tables(self):
        """Drop existing tables and recreate them with correct schema"""
        try:
            drop_queries = [
                "DROP TABLE IF EXISTS user_sessions CASCADE",
                "DROP TABLE IF EXISTS coupons CASCADE", 
                "DROP TABLE IF EXISTS referrals CASCADE",
                "DROP TABLE IF EXISTS payments CASCADE",
                "DROP TABLE IF EXISTS subscriptions CASCADE",
                "DROP TABLE IF EXISTS users CASCADE"
            ]
            
            for query in drop_queries:
                self.execute_query(query)
            
            logger.info("Existing tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
    
    def execute_query(self, query, params=None, fetch=False):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                self.connection.commit()
                return True
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Query execution failed: {e}")
            return None
    
    def create_tables(self):
        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(50),
                country VARCHAR(100),
                language VARCHAR(10) DEFAULT 'en',
                referral_code VARCHAR(50) UNIQUE,
                referred_by BIGINT,
                telegram_username VARCHAR(100),
                privacy_allowed BOOLEAN DEFAULT FALSE,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                service VARCHAR(50) NOT NULL,
                duration INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_method VARCHAR(50),
                status VARCHAR(20) DEFAULT 'pending',
                start_date TIMESTAMP,
                expiry_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                subscription_id INTEGER REFERENCES subscriptions(id),
                payment_method VARCHAR(50) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                tx_hash VARCHAR(255),
                receipt_path VARCHAR(500),
                status VARCHAR(20) DEFAULT 'pending',
                verified_by BIGINT,
                verified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS referrals (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT REFERENCES users(user_id),
                referred_id BIGINT REFERENCES users(user_id),
                reward_type VARCHAR(50),
                reward_amount INTEGER,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS coupons (
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) UNIQUE NOT NULL,
                discount_type VARCHAR(20) NOT NULL,
                discount_value DECIMAL(10,2) NOT NULL,
                applicable_services TEXT[],
                max_uses INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id BIGINT PRIMARY KEY,
                current_step VARCHAR(100),
                temp_data JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        for table in tables:
            self.execute_query(table)
    
    # User operations
    def create_user(self, user_id, name, email, phone, country, referral_code, telegram_username='', privacy_allowed=False):
        query = """
        INSERT INTO users (user_id, name, email, phone, country, referral_code, telegram_username, privacy_allowed)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
        RETURNING user_id
        """
        result = self.execute_query(query, (user_id, name, email, phone, country, referral_code, telegram_username, privacy_allowed), fetch=True)
        return result is not None
    
    def get_user(self, user_id):
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None
    
    def get_user_by_email(self, email):
        query = "SELECT * FROM users WHERE email = %s"
        result = self.execute_query(query, (email,), fetch=True)
        return result[0] if result else None
    
    def update_user_language(self, user_id, language):
        query = "UPDATE users SET language = %s WHERE user_id = %s"
        return self.execute_query(query, (language, user_id))
    
    def update_user_phone(self, user_id, phone):
        query = "UPDATE users SET phone = %s WHERE user_id = %s"
        return self.execute_query(query, (phone, user_id))
    
    def update_user_country(self, user_id, country):
        query = "UPDATE users SET country = %s WHERE user_id = %s"
        return self.execute_query(query, (country, user_id))
    
    def get_user_by_referral_code(self, referral_code):
        query = "SELECT * FROM users WHERE referral_code = %s"
        result = self.execute_query(query, (referral_code,), fetch=True)
        return result[0] if result else None
    
    # Subscription operations
    def create_subscription(self, user_id, service, duration, amount, payment_method):
        query = """
        INSERT INTO subscriptions (user_id, service, duration, amount, payment_method)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        result = self.execute_query(query, (user_id, service, duration, amount, payment_method), fetch=True)
        return result[0]['id'] if result else None
    
    def get_active_subscription(self, user_id):
        query = """
        SELECT * FROM subscriptions 
        WHERE user_id = %s AND status = 'active' AND expiry_date > CURRENT_TIMESTAMP
        ORDER BY expiry_date DESC LIMIT 1
        """
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None
    
    def activate_subscription(self, subscription_id, start_date, expiry_date):
        query = """
        UPDATE subscriptions 
        SET status = 'active', start_date = %s, expiry_date = %s
        WHERE id = %s
        """
        return self.execute_query(query, (start_date, expiry_date, subscription_id))
    
    def get_expiring_subscriptions(self, days_ahead=3):
        query = """
        SELECT s.*, u.name, u.email FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.status = 'active' AND s.expiry_date BETWEEN CURRENT_TIMESTAMP 
        AND CURRENT_TIMESTAMP + INTERVAL '%s days'
        """
        return self.execute_query(query, (days_ahead,), fetch=True)
    
    # Payment operations
    def create_payment(self, user_id, subscription_id, payment_method, amount, tx_hash=None, receipt_path=None):
        query = """
        INSERT INTO payments (user_id, subscription_id, payment_method, amount, tx_hash, receipt_path)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        result = self.execute_query(query, (user_id, subscription_id, payment_method, amount, tx_hash, receipt_path), fetch=True)
        return result[0]['id'] if result else None
    
    def get_pending_payments(self):
        query = """
        SELECT p.*, u.name, u.email, s.service, s.duration FROM payments p
        JOIN users u ON p.user_id = u.user_id
        JOIN subscriptions s ON p.subscription_id = s.id
        WHERE p.status = 'pending'
        ORDER BY p.created_at DESC
        """
        return self.execute_query(query, fetch=True)
    
    def approve_payment(self, payment_id, admin_id):
        query = """
        UPDATE payments 
        SET status = 'approved', verified_by = %s, verified_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        return self.execute_query(query, (admin_id, payment_id))
    
    def reject_payment(self, payment_id, admin_id):
        query = """
        UPDATE payments 
        SET status = 'rejected', verified_by = %s, verified_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        return self.execute_query(query, (admin_id, payment_id))
    
    def get_payment(self, payment_id):
        query = "SELECT * FROM payments WHERE id = %s"
        result = self.execute_query(query, (payment_id,), fetch=True)
        return result[0] if result else None
    
    # Session management
    def update_user_session(self, user_id, step, temp_data=None):
        query = """
        INSERT INTO user_sessions (user_id, current_step, temp_data)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
        current_step = EXCLUDED.current_step,
        temp_data = EXCLUDED.temp_data,
        updated_at = CURRENT_TIMESTAMP
        """
        # Convert temp_data to JSON string if it's a dict
        if isinstance(temp_data, dict):
            import json
            temp_data = json.dumps(temp_data)
        return self.execute_query(query, (user_id, step, temp_data))
    
    def get_user_session(self, user_id):
        query = "SELECT * FROM user_sessions WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        if result:
            session = dict(result[0])
            # Parse temp_data if it's a JSON string
            if session.get('temp_data') and isinstance(session['temp_data'], str):
                try:
                    import json
                    session['temp_data'] = json.loads(session['temp_data'])
                except:
                    session['temp_data'] = {}
            return session
        return None
    
    def clear_user_session(self, user_id):
        query = "DELETE FROM user_sessions WHERE user_id = %s"
        return self.execute_query(query, (user_id,))
    
    # Referral operations
    def create_referral(self, referrer_id, referred_id, reward_type='extension', reward_amount=7):
        query = """
        INSERT INTO referrals (referrer_id, referred_id, reward_type, reward_amount)
        VALUES (%s, %s, %s, %s)
        """
        return self.execute_query(query, (referrer_id, referred_id, reward_type, reward_amount))
    
    def get_user_referrals(self, user_id):
        query = """
        SELECT r.*, u.name as referred_name FROM referrals r
        JOIN users u ON r.referred_id = u.user_id
        WHERE r.referrer_id = %s
        ORDER BY r.created_at DESC
        """
        return self.execute_query(query, (user_id,), fetch=True)

    def count_completed_referrals(self, user_id):
        """Count completed referrals for a user"""
        query = "SELECT COUNT(*) FROM referrals WHERE referrer_id = %s AND status = 'completed'"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0]['count'] if result else 0

    def set_user_referred_by(self, user_id, referrer_id):
        """Set referred_by for a user"""
        query = "UPDATE users SET referred_by = %s WHERE user_id = %s"
        return self.execute_query(query, (referrer_id, user_id))
    
    # Admin queries
    def get_all_users(self, status=None):
        if status:
            query = "SELECT * FROM users WHERE is_active = %s ORDER BY joined_at DESC"
            return self.execute_query(query, (status,), fetch=True)
        else:
            query = "SELECT * FROM users ORDER BY joined_at DESC"
            return self.execute_query(query, fetch=True)
    
    def get_user_stats(self):
        query = """
        SELECT 
            COUNT(*) as total_users,
            COUNT(CASE WHEN joined_at > CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as new_this_week,
            COUNT(CASE WHEN is_active = true THEN 1 END) as active_users
        FROM users
        """
        result = self.execute_query(query, fetch=True)
        return result[0] if result else None
    
    def get_revenue_stats(self):
        query = """
        SELECT 
            SUM(amount) as total_revenue,
            COUNT(*) as total_payments,
            AVG(amount) as avg_payment
        FROM payments WHERE status = 'approved'
        """
        result = self.execute_query(query, fetch=True)
        return result[0] if result else None

# Global database instance
db = Database()
