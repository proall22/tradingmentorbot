MESSAGES = {
    'en': {
        'welcome': """
👋 **Welcome to Trading Mentor Bot!**

We offer professional trading education and mentorship services:

📚 **Available Services:**
• Mentorship - Group-based trading coaching
• Master Class - Complete trading course
• Face-to-Face Masterclass - Personal 1-on-1 sessions
• VIP Signals - Daily trading signals
• One-to-One Coaching - Personal trading support

To get started, please complete your registration first.
        """,
        'main_menu': """
🏠 **Main Menu**

Welcome back! What would you like to do today?

Choose an option below:
        """,
        'registration_start': "Let's get you registered! First, please provide your full name:",
        'ask_email_optional': """
📧 **Email Address (Optional)**

Would you like to provide your email address? 
This helps us send you important updates and notifications.

Choose an option:
        """,
                'ask_email': "Great! Please provide your email address:",
        'ask_telegram_username': """
📱 **Telegram Username (Optional)**

Would you like to provide your Telegram username? 
This helps us communicate with you directly when needed.

Choose an option:
        """,
        'ask_telegram_username_input': "Please provide your Telegram username (without @):",
        'ask_privacy_permission': """
🔒 **Privacy Settings**

To provide you with the best service, we need permission to:
• Send you direct messages
• Add you to relevant groups/channels
• Send notifications about your subscriptions

Do you allow the bot to contact you directly?
        """,
        'ask_phone': "Please provide your phone number:",
        'ask_country': "Finally, what country are you from?",
        'registration_complete': """
✅ **Registration Complete!**

Welcome {name}! Your account has been set up successfully.

📧 Email: {email_status}
📱 Telegram: {telegram_status}
🔒 Privacy: {privacy_status}

🔗 **Your referral link:** `{referral_link}`
Share this with friends to earn rewards!

What would you like to do next?
        """,
        'email_provided': "✅ {email}",
        'email_not_provided': "❌ Not provided",
        'telegram_provided': "✅ @{username}",
        'telegram_not_provided': "❌ Not provided",
        'privacy_allowed': "✅ Direct contact allowed",
        'privacy_denied': "❌ Limited contact only",
        'choose_service': """
📚 **Choose Your Service**

Please select the service you're interested in:
        """,
        'choose_duration': """
⏰ **Choose Duration for {service}**

Select your preferred subscription length:

💰 **Pricing:**
• 1 Month: ${price_1}
• 3 Months: ${price_3} (Save ${save_3}!)
• 6 Months: ${price_6} (Save ${save_6}!)
        """,
        'choose_payment': """
💳 **Choose Payment Method**

Service: {service}
Duration: {duration} month(s)
Total: ${amount}

Please select your payment method:
        """,
        'binance_payment': """
💰 **Binance Payment Instructions**

**Amount:** ${amount} USDT
**Wallet Address:** `{wallet_address}`

1. Send exactly ${amount} USDT to the address above
2. Copy the transaction hash (TX Hash)
3. Click the button below and paste your TX Hash

⚠️ **Important:** Send only USDT to this address!
        """,
        'ask_tx_hash': "Please paste your transaction hash (TX Hash):",
        'ask_order_id': "Please enter your Binance Order ID (not TX Hash):",  # <-- Add this line
        'bank_payment': """
🏦 **Bank Transfer Instructions**

**Amount:** ${amount} USD equivalent
**Payment Method:** {payment_method}

Please make the payment and upload a screenshot of your receipt within 15 minutes.

After uploading, an admin will review and approve your payment.
        """,
        'upload_receipt': "Please upload a screenshot of your payment receipt:",
        'payment_submitted': """
✅ **Payment Submitted Successfully!**

Your payment is being reviewed by our admin team.
You'll receive a confirmation email once approved.

⏱️ Processing time: Usually within 2-4 hours
        """,
        'payment_approved': """
🎉 **Payment Approved!**

Your subscription is now ACTIVE!

Service: {service}
Duration: {duration} month(s)
Expires: {expiry_date}

Welcome to the community! 🚀
        """,
        'payment_rejected': """
❌ **Payment Rejected**

Unfortunately, your payment could not be verified.
Please contact support or try submitting again.

Reason: Invalid or unclear receipt
        """,
        'dashboard': """
📊 **Your Dashboard**

👤 **Profile:**
Name: {name}
Email: {email}
Phone: {phone}
Country: {country}
Telegram: {telegram_username}

📦 **Active Subscription:**
{subscription_info}

🔗 **Referral Program:**
Link: `{referral_link}`
Referrals: {referral_count}
        """,
        'no_subscription': "No active subscription",
        'subscription_info': """
Service: {service}
Status: {status}
Expires: {expiry_date}
        """,
        'admin_panel': """
👨‍💼 **Admin Panel**

📊 **Statistics:**
Total Users: {total_users}
New This Week: {new_users}
Pending Payments: {pending_payments}

Choose an action:
        """,
        'pending_payments': """
💳 **Pending Payments ({count})**

{payment_list}
        """,
        'payment_item': """
**Payment #{id}**
User: {user_name}
Service: {service} ({duration}m)
Amount: ${amount}
Method: {payment_method}
Date: {date}
        """,
        'choose_language': """
🌐 **Choose Your Language**

Please select your preferred language:
        """,
        'language_updated': "✅ Language updated successfully!",
        'error_email_exists': "❌ This email is already registered. Please use a different email.",
        'error_invalid_email': "❌ Please provide a valid email address.",
        'error_general': "❌ Something went wrong. Please try again.",
        'session_timeout': "⏱️ Session expired. Please start over with /start",
        'bot_payment_approved': """
🎉 **Payment Approved!**

Your subscription is now ACTIVE!

📦 **Service:** {service}
⏰ **Duration:** {duration} month(s)
💰 **Amount:** ${amount}
📅 **Expires:** {expiry_date}

Welcome to the community! 🚀

You can now access your dashboard to view your subscription details.
        """,
        'bot_payment_rejected': """
❌ **Payment Rejected**

Unfortunately, your payment could not be verified.

💰 **Amount:** ${amount}
💳 **Method:** {payment_method}

**Reason:** Invalid or unclear receipt

Please contact support or try submitting again with a clear receipt.
        """,
        'help_menu': """
❓ **Help & Support**

Here are some common questions and answers:

**Q: How do I subscribe to a service?**
A: Click "Browse Services", select your preferred service, choose duration, and make payment.

**Q: What payment methods do you accept?**
A: We accept Binance (Crypto), CBE Bank, Telebirr, and abyssinia bank transfers.

**Q: How long does payment approval take?**
A: Usually 2-4 hours during business hours.

**Q: Can I change my subscription?**
A: Contact support for subscription changes.

**Q: How do I contact support?**
A: Use the "Contact Support" button below.
        """,
        'contact_support': """
📞 **Contact Support**

Need help? Our support team is here for you!

**Support Hours:** 9 AM - 6 PM (Monday - Friday)

**Contact Methods:**
• Telegram: @support_username
• Email: support@tradingmentor.com
• Phone: +1234567890

Please describe your issue clearly for faster assistance.
        """,
        'referral_info': """
🤝 **Referral Program**

Earn rewards by inviting friends!

**How it works:**
1. Share your referral link
2. Friends register using your link
3. You earn rewards when they subscribe

**Rewards:**
• 7 days free extension for each referral
• Bonus rewards for multiple referrals

**Your Stats:**
Referrals: {referral_count}
Total Rewards: {total_rewards} days

Share your link: `{referral_link}`
        """,
    },
    'am': {
        'welcome': """
👋 **የግብር አማካሪ ቦት እንኳን ደህና መጡ!**

ሙያዊ የግብር ትምህርት እና አማካሪነት አገልግሎቶችን እናቀርባለን:

📚 **የሚገኙ አገልግሎቶች:**
• አማካሪነት - በቡድን ላይ የተመሰረተ የግብር ኮችንግ
• ዋና ክፍል - ሙሉ የግብር ኮርስ
• በፊት ለፊት ዋና ክፍል - የግል 1-በ-1 ክፍለ ጊዜዎች
• VIP ምልክቶች - ዕለታዊ የግብር ምልክቶች
• አንድ-ለ-አንድ ኮችንግ - የግል የግብር ድጋፍ

ለመጀመር፣ እባክዎ መጀመሪያ ምዝገባዎን ያጠናቅቁ።
        """,
        'main_menu': """
🏠 **ዋና ሜኑ**

እንኳን ደህና መጡ! ዛሬ ምን ማድረግ ይፈልጋሉ?

ከታች አንድ አማራጭ ይምረጡ:
        """,
        'registration_start': "እንመዝግብዎት! መጀመሪያ፣ እባክዎ ሙሉ ስምዎን ያቅርቡ:",
        'ask_email_optional': """
📧 **የኢሜል አድራሻ (አማራጭ)**

የኢሜል አድራሻዎን መስጠት ይፈልጋሉ?
ይህ አስፈላጊ ዝመናዎችን እና ማሳወቂያዎችን እንድንልክልዎ ይረዳናል።

አንድ አማራጭ ይምረጡ:
        """,
        'ask_email': "በጣም ጥሩ! እባክዎ የኢሜል አድራሻዎን ያቅርቡ:",
        'ask_telegram_username': """
📱 **Telegram Username (Optional)**

Would you like to provide your Telegram username? 
This helps us communicate with you directly when needed.

Choose an option:
        """,
        'ask_telegram_username_input': "Please provide your Telegram username (without @):",
        'ask_privacy_permission': """
🔒 **Privacy Settings**

To provide you with the best service, we need permission to:
• Send you direct messages
• Add you to relevant groups/channels
• Send notifications about your subscriptions

Do you allow the bot to contact you directly?
        """,
        'ask_phone': "Please provide your phone number:",
        'ask_country': "Finally, what country are you from?",
        'registration_complete': """
✅ **ምዝገባ ተጠናቋል!**

እንኳን ደህና መጡ {name}! መለያዎ በተሳካ ሁኔታ ተዘጋጅቷል።

📧 ኢሜል: {email_status}
📱 ቴሌግራም: {telegram_status}
🔒 ግላዊነት: {privacy_status}

🔗 **የእርስዎ የመሳቢያ ሊንክ:** `{referral_link}`
ይህንን ከጓደኞች ጋር ያጋሩ የሽልማት ለማግኘት!

በመቀጠል ምን ማድረግ ይፈልጋሉ?
        """,
        'error_general': "❌ የሆነ ችግር ተፈጥሯል። እባክዎ እንደገና ይሞክሩ።",
        'bot_payment_approved': """
🎉 **ክፍያ ተቀባይነት አግኝቷል!**

የእርስዎ ምዝገባ አሁን ንቁ ነው!

📦 **አገልግሎት:** {service}
⏰ **ጊዜ:** {duration} ወር
💰 **መጠን:** ${amount}
📅 **ያበቃል:** {expiry_date}

ወደ ማህበረሰቡ እንኳን ደህና መጡ! 🚀
        """,
        'bot_payment_rejected': """
❌ **ክፍያ ውድቅ ሆኗል**

ለሚያሳዝነው የእርስዎ ክፍያ ማረጋገጥ አልተቻለም።

💰 **መጠን:** ${amount}
💳 **ዘዴ:** {payment_method}

**ምክንያት:** ልክ ያልሆነ ወይም ግልጽ ያልሆነ ደረሰኝ

እባክዎ ድጋፍን ያነጋግሩ ወይም ግልጽ ደረሰኝ ይዘው እንደገና ይሞክሩ።
        """,
        'help_menu': """
❓ **Help & Support**

Here are some common questions and answers:

**Q: How do I subscribe to a service?**
A: Click "Browse Services", select your preferred service, choose duration, and make payment.

**Q: What payment methods do you accept?**
A: We accept Binance (Crypto), CBE Bank, Telebirr, and abyssinia bank transfers.

**Q: How long does payment approval take?**
A: Usually 2-4 hours during business hours.

**Q: Can I change my subscription?**
A: Contact support for subscription changes.

**Q: How do I contact support?**
A: Use the "Contact Support" button below.
        """,
        'contact_support': """
📞 **Contact Support**

Need help? Our support team is here for you!

**Support Hours:** 9 AM - 6 PM (Monday - Friday)

**Contact Methods:**
• Telegram: @support_username
• Email: support@tradingmentor.com
• Phone: +1234567890

Please describe your issue clearly for faster assistance.
        """,
        'referral_info': """
🤝 **Referral Program**

Earn rewards by inviting friends!

**How it works:**
1. Share your referral link
2. Friends register using your link
3. You earn rewards when they subscribe

**Rewards:**
• 7 days free extension for each referral
• Bonus rewards for multiple referrals

**Your Stats:**
Referrals: {referral_count}
Total Rewards: {total_rewards} days

Share your link: `{referral_link}`
        """,
    }
}

def get_message(user_language, key, **kwargs):
    """Get localized message with optional formatting"""
    language = user_language if user_language in MESSAGES else 'en'
    message = MESSAGES[language].get(key, MESSAGES['en'].get(key, key))
    
    if kwargs:
        try:
            return message.format(**kwargs)
        except KeyError:
            return message
    return message

