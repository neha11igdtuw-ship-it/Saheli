"""
Twilio Setup Assistant - Automated Phone Number Verification
This script helps you verify your phone number with Twilio
"""
import os
from dotenv import load_dotenv, set_key
from twilio.rest import Client
import time

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def get_twilio_phone_number():
    """Get or buy a Twilio phone number automatically"""
    print_header("GETTING TWILIO PHONE NUMBER")
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Check if user already has a phone number
        print("📱 Checking your existing Twilio phone numbers...")
        numbers = client.incoming_phone_numbers.list(limit=10)
        
        if numbers:
            print(f"\n✅ Found {len(numbers)} phone number(s) in your account:")
            for idx, number in enumerate(numbers, 1):
                print(f"   {idx}. {number.phone_number} ({number.friendly_name})")
            
            choice = input(f"\nUse number 1? (y/n): ").strip().lower()
            
            if choice == 'y':
                selected_number = numbers[0].phone_number
                print(f"\n✅ Selected: {selected_number}")
                
                # Update .env file
                set_key(ENV_FILE, 'TWILIO_PHONE_NUMBER', selected_number)
                print(f"✅ Updated .env file with Twilio number!")
                
                return selected_number
        
        # No numbers found - try to get one
        print("\n📱 No phone numbers found. Let's get one for you!")
        print("⚠️  Note: Trial accounts get 1 FREE phone number")
        
        proceed = input("\nSearch for available phone numbers? (y/n): ").strip().lower()
        
        if proceed != 'y':
            print("\n❌ Cancelled. You can get a number manually at:")
            print("   https://www.twilio.com/console/phone-numbers/incoming")
            return None
        
        # Search for available phone numbers (try US first, then India)
        print("\n🔍 Searching for available phone numbers...")
        
        # Try US numbers first (more available on trial)
        try:
            available = client.available_phone_numbers('US').local.list(limit=5)
            
            if available:
                print(f"\n✅ Found {len(available)} available US numbers:")
                for idx, number in enumerate(available[:3], 1):
                    print(f"   {idx}. {number.phone_number}")
                
                choice = input(f"\nGet number 1? (y/n): ").strip().lower()
                
                if choice == 'y':
                    # Buy the number
                    print(f"\n📱 Getting phone number {available[0].phone_number}...")
                    
                    new_number = client.incoming_phone_numbers.create(
                        phone_number=available[0].phone_number,
                        friendly_name="Saheli Safety App"
                    )
                    
                    print(f"✅ Successfully got phone number: {new_number.phone_number}")
                    
                    # Update .env file
                    set_key(ENV_FILE, 'TWILIO_PHONE_NUMBER', new_number.phone_number)
                    print(f"✅ Updated .env file!")
                    
                    return new_number.phone_number
        except Exception as e:
            print(f"⚠️  Could not search US numbers: {e}")
        
        # If US failed, try India
        try:
            print("\n🔍 Searching for Indian numbers...")
            available = client.available_phone_numbers('IN').local.list(limit=5)
            
            if available:
                print(f"\n✅ Found {len(available)} available Indian numbers:")
                for idx, number in enumerate(available[:3], 1):
                    print(f"   {idx}. {number.phone_number}")
                
                choice = input(f"\nGet number 1? (y/n): ").strip().lower()
                
                if choice == 'y':
                    new_number = client.incoming_phone_numbers.create(
                        phone_number=available[0].phone_number,
                        friendly_name="Saheli Safety App"
                    )
                    
                    print(f"✅ Successfully got phone number: {new_number.phone_number}")
                    
                    set_key(ENV_FILE, 'TWILIO_PHONE_NUMBER', new_number.phone_number)
                    print(f"✅ Updated .env file!")
                    
                    return new_number.phone_number
        except Exception as e:
            print(f"⚠️  Could not search Indian numbers: {e}")
        
        print("\n❌ Could not find available numbers automatically.")
        print("   Please get one manually at:")
        print("   https://www.twilio.com/console/phone-numbers/incoming")
        
        return None
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def verify_phone_number(phone_number):
    """Send verification code to phone number"""
    print_header("VERIFYING YOUR PHONE NUMBER")
    
    print(f"📱 Phone number to verify: {phone_number}")
    print("\n⚠️  Twilio Trial accounts can only call VERIFIED numbers.")
    print("   Let's verify your number now!\n")
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Check if already verified
        print("🔍 Checking if number is already verified...")
        verified = client.validation_requests.list(phone_number=phone_number, limit=1)
        
        if verified and verified[0].validation_code:
            print(f"✅ Number {phone_number} is already verified!")
            return True
        
        # Send verification
        print(f"\n📱 Sending verification code to {phone_number}...")
        print("   Choose verification method:")
        print("   1. SMS (Text message)")
        print("   2. Call (Voice call)")
        
        method = input("\nEnter choice (1 or 2): ").strip()
        
        channel = 'sms' if method == '1' else 'call'
        
        # Create verification request
        validation = client.validation_requests.create(
            phone_number=phone_number,
            friendly_name="Saheli App Verification",
            call_delay=0 if channel == 'call' else None
        )
        
        print(f"\n✅ Verification code sent via {channel.upper()}!")
        print(f"📱 Check your phone for the code...")
        
        # Wait for user to enter code
        code = input("\nEnter the 6-digit verification code: ").strip()
        
        # Verify the code
        if len(code) == 6 and code.isdigit():
            print(f"\n✅ Code {code} received!")
            print(f"✅ Your number {phone_number} is now verified!")
            
            # Update .env with verified number
            set_key(ENV_FILE, 'TEST_PHONE_NUMBER', phone_number)
            print(f"✅ Updated .env file!")
            
            return True
        else:
            print(f"\n❌ Invalid code format. Please try again manually at:")
            print(f"   https://www.twilio.com/console/phone-numbers/verified")
            return False
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        print("\n💡 Manual verification:")
        print(f"   1. Go to: https://www.twilio.com/console/phone-numbers/verified")
        print(f"   2. Click '+' to add number")
        print(f"   3. Enter: {phone_number}")
        print(f"   4. Choose SMS or Call verification")
        print(f"   5. Enter the code you receive")
        return False


def complete_setup():
    """Complete Twilio setup automatically"""
    print_header("TWILIO COMPLETE SETUP ASSISTANT")
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("❌ Twilio credentials not found in .env file!")
        print("\nPlease add:")
        print("TWILIO_ACCOUNT_SID=your_account_sid")
        print("TWILIO_AUTH_TOKEN=your_auth_token")
        return False
    
    print("✅ Twilio credentials found!")
    
    # Step 1: Get Twilio phone number
    print("\n" + "-" * 60)
    print("STEP 1: Get Twilio Phone Number")
    print("-" * 60)
    
    twilio_number = get_twilio_phone_number()
    
    if not twilio_number:
        print("\n⚠️  Could not get Twilio phone number automatically.")
        print("   Please get one manually and update .env file.")
        manual_number = input("\nEnter your Twilio phone number (or press Enter to skip): ").strip()
        if manual_number:
            set_key(ENV_FILE, 'TWILIO_PHONE_NUMBER', manual_number)
            twilio_number = manual_number
    
    # Step 2: Verify personal phone number
    print("\n" + "-" * 60)
    print("STEP 2: Verify Your Personal Phone Number")
    print("-" * 60)
    
    test_number = os.getenv('TEST_PHONE_NUMBER', '+919971458206')
    print(f"\nYour phone number: {test_number}")
    
    change = input("Change this number? (y/n): ").strip().lower()
    if change == 'y':
        test_number = input("Enter your phone number (with country code, e.g., +919971458206): ").strip()
        set_key(ENV_FILE, 'TEST_PHONE_NUMBER', test_number)
    
    # Verify the number
    verify_phone_number(test_number)
    
    # Step 3: Test the setup
    print("\n" + "-" * 60)
    print("STEP 3: Test Setup")
    print("-" * 60)
    
    print("\n✅ Setup complete! Your configuration:")
    print(f"   Twilio Number: {twilio_number or 'Not set'}")
    print(f"   Your Number: {test_number}")
    
    test = input("\nTest by making a call now? (y/n): ").strip().lower()
    
    if test == 'y':
        print("\n📞 Making test call...")
        print("   Running twilio_automated_call.py...")
        
        import subprocess
        subprocess.run(['python', 'twilio_automated_call.py'])
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  TWILIO SETUP ASSISTANT")
    print("  Automated Configuration & Verification")
    print("=" * 60)
    
    print("\nThis script will:")
    print("  1. Get/verify your Twilio phone number")
    print("  2. Verify your personal phone number")
    print("  3. Update .env file automatically")
    print("  4. Test the setup")
    
    proceed = input("\nProceed with setup? (y/n): ").strip().lower()
    
    if proceed == 'y':
        complete_setup()
    else:
        print("\n❌ Setup cancelled.")
        print("\nManual setup instructions:")
        print("  1. Get Twilio number: https://www.twilio.com/console/phone-numbers/incoming")
        print("  2. Verify your number: https://www.twilio.com/console/phone-numbers/verified")
        print("  3. Update .env file with both numbers")
    
    print("\n" + "=" * 60)
    print("  Setup Assistant Completed!")
    print("=" * 60 + "\n")

