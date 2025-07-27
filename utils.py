import uuid
import re
import os
import hashlib  # Added for MD5 hashing
from datetime import datetime, timedelta
import logging
import requests

logger = logging.getLogger(__name__)

def generate_referral_code(user_id):
    """Generate unique referral code for user"""
    timestamp = str(int(datetime.now().timestamp()))
    raw_string = f"{user_id}_{timestamp}"
    hash_object = hashlib.md5(raw_string.encode())
    return hash_object.hexdigest()[:8].upper()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def validate_phone(phone):
    """Validate Ethiopian phone number format (09..., 07..., +251...)"""
    phone = phone.strip().replace(' ', '').replace('-', '')
    pattern = r'^(09\d{8}|07\d{8}|\+251\d{9})$'
    return re.match(pattern, phone) is not None

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"

def calculate_savings(price_1, price_multi, months=None):
    """Calculate savings for multi-month subscriptions"""
    if months is not None:
        return (price_1 * months) - price_multi
    # fallback for original usage
    return price_1 - price_multi

def get_duration_text(months):
    """Get human readable duration text"""
    if months == 1:
        return "1 month"
    else:
        return f"{months} months"

def format_datetime(dt):
    """Format datetime for display"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    if dt:
        return dt.strftime("%B %d, %Y at %I:%M %p")
    return "N/A"

def get_expiry_date(duration_months):
    """Calculate expiry date from duration"""
    return datetime.now() + timedelta(days=duration_months * 30)

def save_receipt_file(file_content, user_id, payment_id):
    """Save uploaded receipt file"""
    try:
        # Create receipts directory if not exists
        receipts_dir = "receipts"
        os.makedirs(receipts_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipt_{user_id}_{payment_id}_{timestamp}.jpg"
        filepath = os.path.join(receipts_dir, filename)
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"Receipt saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save receipt: {e}")
        return None

def create_referral_link(bot_username, referral_code):
    """Create referral link for user"""
    return f"https://t.me/{bot_username}?start=ref_{referral_code}"

def is_admin(user_id):
    """Check if user is admin"""
    from config import ADMIN_IDS
    return user_id in ADMIN_IDS

def log_user_action(user_id, action, details=None):
    """Log user actions for tracking"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] User {user_id}: {action}"
    if details:
        log_message += f" - {details}"
    logger.info(log_message)

def chunk_list(lst, chunk_size):
    """Split list into chunks"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def escape_markdown(text):
    """Escape markdown special characters"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_user_info(user):
    """Format user information for display"""
    return f"""
**Name:** {user['name']}
**Email:** {user['email']}
**Phone:** {user.get('phone', 'N/A')}
**Country:** {user.get('country', 'N/A')}
**Joined:** {format_datetime(user['joined_at'])}
**Status:** {'Active' if user['is_active'] else 'Inactive'}
    """

def get_service_emoji(service):
    """Get emoji for service type"""
    emojis = {
        'mentorship': '👥',
        'masterclass': '📚',
        'face_to_face': '🤝',
        'vip_signals': '📈',
        'one_to_one': '👨‍🏫'
    }
    return emojis.get(service, '📦')

def generate_payment_reference():
    """Generate unique payment reference"""
    return f"PAY_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"

def truncate_text(text, max_length=50):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def clean_country_input(country):
    """Remove emoji/flag from country input, accept both text and flag"""
    # Remove flag emojis (unicode range)
    return re.sub(r'[\U0001F1E6-\U0001F1FF]+', '', country).strip()

# Simple in-memory cache (for production, use persistent cache/db)
_translation_cache = {}

def translate_to_amharic(text):
    """Translate English text to Amharic using Google Translate unofficial API, with caching."""
    if not text:
        return ""
    if text in _translation_cache:
        return _translation_cache[text]
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": "am",
        "dt": "t",
        "q": text
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            translated = result[0][0][0]
            _translation_cache[text] = translated
            return translated
    except Exception as e:
        # Log error if needed
        pass
    return text  # fallback to original if failed

# Usage example in your message handler:
# if user_language == 'am' and key not in MESSAGES['am']:
#     message = translate_to_amharic(MESSAGES['en'][key])