import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Email Configuration
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Payment Configuration
BINANCE_WALLET_ADDRESS = os.getenv('BINANCE_WALLET_ADDRESS')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
BINANCE_USER_ID = os.getenv('BINANCE_USER_ID')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
CBE_ACCOUNT = os.getenv('CBE_ACCOUNT')
ABYSSINIA_ACCOUNT = os.getenv('ABYSSINIA_ACCOUNT')
TELERAM_USERNAME = os.getenv('TELERAM_USERNAME')

# Service Pricing (USD)
SERVICES = {
    'mentorship': {
        'name': 'Mentorship',
        'description': 'Group-based trading coaching',
        'prices': {'1': 70, '3': 180, '6': 360}
    },
    'masterclass': {
        'name': 'Master Class',
        'description': 'Full course with structure',
        'prices': {'1': 250, '3': 600, '6': 1200}
    },
    'face_to_face': {
        'name': 'Face-to-Face Masterclass',
        'description': '1-on-1 in-person masterclass',
        'prices': {'1': 500, '3': 1200, '6': 2400}
    },
    'vip_signals': {
        'name': 'VIP Signals',
        'description': 'Daily signals to follow',
        'prices': {'1': 10, '3': 25, '6': 45}
    },
    'one_to_one': {
        'name': 'One-to-One Coaching',
        'description': 'Personal trading support and lessons',
        'prices': {'1': 100, '3': 250, '6': 480}
    }
}

# Service Groups (add all group IDs in your .env)
SERVICE_GROUPS = {
    'mentorship': {
        '1': int(os.getenv('GROUP_MENTORSHIP_1', 0)),
        '3': int(os.getenv('GROUP_MENTORSHIP_3', 0)),
        '6': int(os.getenv('GROUP_MENTORSHIP_6', 0)),
    },
    'masterclass': {
        '1': int(os.getenv('GROUP_MASTERCLASS_1', 0)),
        '3': int(os.getenv('GROUP_MASTERCLASS_3', 0)),
        '6': int(os.getenv('GROUP_MASTERCLASS_6', 0)),
    },
    'face_to_face': {
        '1': int(os.getenv('GROUP_FACE_TO_FACE_1', 0)),
        '3': int(os.getenv('GROUP_FACE_TO_FACE_3', 0)),
        '6': int(os.getenv('GROUP_FACE_TO_FACE_6', 0)),
    },
    'vip_signals': {
        '1': int(os.getenv('GROUP_VIP_SIGNALS_1', 0)),
        '3': int(os.getenv('GROUP_VIP_SIGNALS_3', 0)),
        '6': int(os.getenv('GROUP_VIP_SIGNALS_6', 0)),
    },
    'one_to_one': {
        '1': int(os.getenv('GROUP_ONE_TO_ONE_1', 0)),
        '3': int(os.getenv('GROUP_ONE_TO_ONE_3', 0)),
        '6': int(os.getenv('GROUP_ONE_TO_ONE_6', 0)),
    }
}

# Languages
LANGUAGES = {
    'en': 'English 🇬🇧',
    'am': 'አማርኛ 🇪🇹'
}

# Payment Methods
PAYMENT_METHODS = {
    'binance': 'Binance (Crypto)',
    'cbe': 'CBE Bank',
    'telebirr': 'Telebirr',
    'abyssinia': 'Abyssinia Bank'
}