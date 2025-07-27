# Trading Mentorship Telegram Bot

A comprehensive Telegram bot for managing trading education services, payments, and user subscriptions.

## Features

### 🎯 Core Functionality
- **User Registration System** - Complete profile management with email verification
- **Multi-Service Platform** - Mentorship, Masterclass, VIP Signals, One-to-One Coaching
- **Dual Payment Processing** - Binance crypto payments and local bank transfers
- **Admin Dashboard** - Complete payment approval and user management system
- **Subscription Management** - Automated expiry tracking and renewal reminders
- **Referral Program** - Built-in referral tracking with rewards
- **Multi-language Support** - English and Amharic language options

### 💳 Payment Features
- **Binance Integration** - Crypto payments with transaction hash verification
- **Local Banking** - Support for CBE, Telebirr, and other bank transfers
- **Receipt Upload** - Image upload and admin review system
- **Payment Tracking** - Complete payment history and status management

### 👨‍💼 Admin Features
- **Payment Approval** - Review and approve/reject payment receipts
- **User Management** - View all users, active subscriptions, and statistics
- **Broadcast System** - Send messages to all users or specific groups
- **Analytics Dashboard** - Revenue stats, user growth, and performance metrics

### 🤖 Automation
- **Email Notifications** - Welcome emails, payment confirmations, expiry warnings
- **Scheduled Tasks** - Daily checks for expiring subscriptions and renewals
- **Session Management** - Secure user state management throughout interactions

## Installation

1. **Install Dependencies**
```bash
pip install python-telegram-bot python-dotenv psycopg2-binary pandas python-binance pillow schedule
```

2. **Environment Setup**
Copy `.env.example` to `.env` and configure:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DATABASE_URL=postgresql://username:password@localhost/trading_bot
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
BINANCE_WALLET_ADDRESS=your_binance_wallet_address
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
```

3. **Database Setup**
- Install PostgreSQL
- Create a database for the bot
- The bot will automatically create required tables on first run

4. **Email Configuration**
- Use Gmail with App Password for email notifications
- Enable 2FA and generate an App Password

## Usage

### Starting the Bot
```bash
python run.py
```

### Bot Commands
- `/start` - Initialize bot and show main menu
- `/admin` - Access admin panel (admin only)

### User Flow
1. **Registration** - Users provide name, email, phone, country
2. **Service Selection** - Choose from available services with different durations
3. **Payment** - Select Binance crypto or bank transfer
4. **Verification** - Admin reviews and approves payments
5. **Access** - Users get activated subscriptions and access to services

### Admin Operations
- Review pending payments in admin panel
- Approve/reject payment receipts
- View user statistics and manage subscriptions
- Send broadcast messages to users
- Monitor revenue and growth metrics

## Service Pricing

| Service | 1 Month | 3 Months | 6 Months |
|---------|---------|----------|----------|
| Mentorship | $70 | $180 | $360 |
| Master Class | $250 | $600 | $1,200 |
| Face-to-Face Masterclass | $500 | $1,200 | $2,400 |
| VIP Signals | $10 | $25 | $45 |
| One-to-One Coaching | $100 | $250 | $480 |

## File Structure

```
trading-bot/
├── main.py                 # Bot entry point
├── config.py              # Configuration settings
├── database.py            # Database operations
├── email_service.py       # Email functionality
├── messages.py            # Localized messages
├── utils.py               # Utility functions
├── scheduler.py           # Automated tasks
├── handlers/              # Bot command handlers
│   ├── start_handler.py
│   ├── registration_handler.py
│   ├── service_handler.py
│   ├── payment_handler.py
│   ├── admin_handler.py
│   ├── dashboard_handler.py
│   └── language_handler.py
├── receipts/              # Uploaded payment receipts
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Security Features

- **Input Validation** - All user inputs are validated and sanitized
- **Admin Protection** - Admin functions are restricted by user ID verification
- **Payment Security** - Transaction hashes and receipts are tracked for uniqueness
- **Session Management** - Secure temporary data storage with automatic cleanup
- **Error Handling** - Comprehensive error logging and user-friendly error messages

## Monitoring & Maintenance

### Automated Monitoring
- Daily subscription expiry checks
- Automated renewal reminders
- Weekly statistics reports to admins
- Session cleanup for expired user states

### Logging
- Comprehensive logging to `bot.log`
- User action tracking for audit trails
- Error logging with detailed stack traces
- Performance monitoring for database operations

## Support

For issues or questions:
1. Check the logs in `bot.log`
2. Verify database connectivity
3. Ensure all environment variables are set correctly
4. Contact the development team

## License

This project is proprietary software for trading education services.