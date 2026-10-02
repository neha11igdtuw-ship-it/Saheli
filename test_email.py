# Quick Email Test Script

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_smtp(username, password, to_email):
    """Test Gmail SMTP connection"""
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "🚨 Test Email from Saheli App"
        msg['From'] = username
        msg['To'] = to_email
        
        body = """
        This is a TEST email from Saheli Safety App!
        
        If you received this, your email configuration is working! ✅
        
        Next step: Add this email to your trusted contacts and test SOS!
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"📧 Connecting to Gmail SMTP...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            print(f"🔐 Logging in as {username}...")
            server.login(username, password)
            print(f"📤 Sending test email to {to_email}...")
            server.send_message(msg)
        
        print("✅ SUCCESS! Email sent!")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Saheli Email Configuration Test")
    print("=" * 50)
    print()
    
    # Get credentials
    print("Enter your Gmail address:")
    username = input("Email: ").strip()
    
    print("\nEnter your Gmail App Password (or regular password):")
    password = input("Password: ").strip()
    
    print("\nEnter test recipient email (can be same as sender):")
    to_email = input("To: ").strip()
    
    print("\n" + "=" * 50)
    print("Testing email configuration...")
    print("=" * 50)
    
    if test_gmail_smtp(username, password, to_email):
        print("\n✅ Email is working! Now update your .env file:")
        print(f"\nSMTP_USERNAME={username}")
        print(f"SMTP_PASSWORD={password}")
        print("\nThen restart the app!")
    else:
        print("\n❌ Email test failed. Check your credentials!")
        print("\nCommon issues:")
        print("1. Enable 'Less secure app access' or use App Password")
        print("2. Enable 2-Step Verification and create App Password")
        print("3. Try https://myaccount.google.com/apppasswords")

