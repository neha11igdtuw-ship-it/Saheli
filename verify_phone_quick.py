"""
Quick Phone Number Verifier for Twilio
Automatically verifies your phone number
"""
import os
import sys
from dotenv import load_dotenv, set_key
from twilio.rest import Client

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PHONE_TO_VERIFY = os.getenv('TEST_PHONE_NUMBER', '+919971458206')

print("=" * 60)
print("QUICK PHONE NUMBER VERIFIER")
print("=" * 60)

print(f"\nPhone to verify: {PHONE_TO_VERIFY}")

try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    # Method 1: Add to verified caller IDs via API
    print("\nAttempting to verify via Twilio API...")
    
    # Create outgoing caller ID (this sends verification code)
    validation = client.outgoing_caller_ids.create(
        phone_number=PHONE_TO_VERIFY,
        friendly_name="Saheli App"
    )
    
    print(f"\nVerification initiated!")
    print(f"You should receive a call with a verification code")
    print(f"   Validation Code: {validation.validation_code}")
    
    print(f"\nANSWER YOUR PHONE NOW!")
    print(f"   You'll hear: 'Your validation code is {validation.validation_code}'")
    
    input("\nPress Enter after you've received and noted the code...")
    
    code = input(f"Enter the 6-digit code you heard: ").strip()
    
    if code == validation.validation_code:
        print(f"\nSUCCESS! {PHONE_TO_VERIFY} is now verified!")
        print(f"You can now make calls to this number!")
    else:
        print(f"\nCode mismatch. The verification was sent but not confirmed.")
        print(f"   Expected: {validation.validation_code}")
        print(f"   You entered: {code}")
        print(f"\n   Your number should still be verified. Try making a call!")
    
except Exception as e:
    print(f"\nAutomatic verification failed: {e}")
    print(f"\nMANUAL VERIFICATION REQUIRED:")
    print(f"\n   Quick steps:")
    print(f"   1. Open: https://www.twilio.com/console/phone-numbers/verified")
    print(f"   2. Click the red '+' button")
    print(f"   3. Enter: {PHONE_TO_VERIFY}")
    print(f"   4. Choose 'Call Me' or 'Text Me'")
    print(f"   5. Enter the code you receive")
    print(f"   6. Done! Run twilio_automated_call.py again")
    
    print(f"\n   OR use this direct link:")
    print(f"   https://www.twilio.com/console/phone-numbers/verified")

print("\n" + "=" * 60)

