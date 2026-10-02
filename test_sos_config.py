"""
Test script to check if SOS alerts are working
"""
import os
import sys
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

print("=" * 60)
print("SAHELI SOS ALERT CONFIGURATION CHECK")
print("=" * 60)

# Check Email Configuration
print("\n📧 EMAIL CONFIGURATION:")
print("-" * 60)
smtp_server = os.getenv('SMTP_SERVER', '')
smtp_port = os.getenv('SMTP_PORT', '')
smtp_username = os.getenv('SMTP_USERNAME', '')
smtp_password = os.getenv('SMTP_PASSWORD', '')

print(f"SMTP Server: {smtp_server if smtp_server else '❌ NOT SET'}")
print(f"SMTP Port: {smtp_port if smtp_port else '❌ NOT SET'}")
print(f"SMTP Username: {smtp_username if smtp_username else '❌ NOT SET'}")
print(f"SMTP Password: {'✅ SET (hidden)' if smtp_password else '❌ NOT SET'}")

if smtp_username and smtp_password and '@' in smtp_username:
    print("\n✅ Email is CONFIGURED")
    print("   Testing connection...")
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        # Test connection
        server = smtplib.SMTP(smtp_server, int(smtp_port), timeout=10)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.quit()
        
        print("   ✅ EMAIL CONNECTION SUCCESSFUL!")
        print("   ✅ Emails WILL be sent")
    except Exception as e:
        print(f"   ❌ EMAIL CONNECTION FAILED: {e}")
        print("   📝 Emails will be logged to pending_alerts folder")
else:
    print("\n❌ Email is NOT CONFIGURED")
    print("   📝 Emails will be logged to pending_alerts folder")

# Check SMS Configuration
print("\n📱 SMS CONFIGURATION:")
print("-" * 60)
twilio_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
twilio_token = os.getenv('TWILIO_AUTH_TOKEN', '')
twilio_phone = os.getenv('TWILIO_PHONE_NUMBER', '')

print(f"Twilio Account SID: {twilio_sid[:10] + '...' if twilio_sid else '❌ NOT SET'}")
print(f"Twilio Auth Token: {'✅ SET (hidden)' if twilio_token else '❌ NOT SET'}")
print(f"Twilio Phone: {twilio_phone if twilio_phone else '❌ NOT SET'}")

if twilio_sid and twilio_token and twilio_phone:
    print("\n✅ SMS is CONFIGURED")
    print("   Testing connection...")
    
    try:
        from twilio.rest import Client
        client = Client(twilio_sid, twilio_token)
        
        # Test by fetching account info
        account = client.api.accounts(twilio_sid).fetch()
        print(f"   ✅ TWILIO CONNECTION SUCCESSFUL!")
        print(f"   ✅ Account Status: {account.status}")
        print(f"   ✅ SMS WILL be sent")
        
        # Check if phone number is valid
        if not twilio_phone.startswith('+'):
            print(f"   ⚠️  WARNING: Phone number should start with + (e.g., +1234567890)")
        
        # Check if it's a Twilio number
        try:
            numbers = client.incoming_phone_numbers.list(phone_number=twilio_phone)
            if numbers:
                print(f"   ✅ Phone number is a valid Twilio number")
            else:
                print(f"   ⚠️  WARNING: {twilio_phone} is not in your Twilio account")
                print(f"   ⚠️  You need to use a Twilio-provided number, not your personal number")
        except:
            print(f"   ⚠️  Could not verify phone number")
            
    except Exception as e:
        print(f"   ❌ TWILIO CONNECTION FAILED: {e}")
        print("   ❌ SMS will NOT be sent")
else:
    print("\n❌ SMS is NOT CONFIGURED")
    print("   ❌ SMS will NOT be sent")

# Check Voice Call Configuration (same as SMS)
print("\n📞 VOICE CALL CONFIGURATION:")
print("-" * 60)
if twilio_sid and twilio_token and twilio_phone:
    print("✅ Voice calls are CONFIGURED (uses same Twilio credentials)")
    print("✅ Automated voice calls WILL be made")
else:
    print("❌ Voice calls are NOT CONFIGURED")
    print("❌ Voice calls will NOT be made")

# Summary
print("\n" + "=" * 60)
print("📊 SUMMARY:")
print("=" * 60)

working = []
not_working = []

if smtp_username and smtp_password:
    working.append("📧 Email (or fallback logging)")
else:
    not_working.append("📧 Email")

if twilio_sid and twilio_token and twilio_phone:
    working.append("📱 SMS")
    working.append("📞 Voice Calls")
else:
    not_working.append("📱 SMS")
    not_working.append("📞 Voice Calls")

if working:
    print("\n✅ WORKING:")
    for item in working:
        print(f"   {item}")

if not_working:
    print("\n❌ NOT WORKING:")
    for item in not_working:
        print(f"   {item}")

print("\n" + "=" * 60)
print("💡 RECOMMENDATIONS:")
print("=" * 60)

if not smtp_username or not smtp_password:
    print("\n📧 TO FIX EMAIL:")
    print("   1. Go to Settings page in the app")
    print("   2. Enter your Gmail and App Password")
    print("   3. Click 'Test Email' to verify")
    print("   4. Click 'Save Email Settings'")

if not twilio_sid or not twilio_token or not twilio_phone:
    print("\n📱 TO FIX SMS/VOICE:")
    print("   1. Sign up at https://www.twilio.com/try-twilio")
    print("   2. Get your Account SID and Auth Token")
    print("   3. Get a FREE Twilio phone number")
    print("   4. Go to Settings page in the app")
    print("   5. Enter Twilio credentials")
    print("   6. Click 'Save SMS Settings'")

print("\n" + "=" * 60)
print("Press Enter to exit...")
input()

