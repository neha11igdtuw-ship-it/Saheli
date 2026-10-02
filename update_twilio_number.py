"""
Update Twilio Phone Number in .env file
"""
import os
import sys
from dotenv import load_dotenv, set_key

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Path to .env file
ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')

# New Twilio phone number
NEW_TWILIO_NUMBER = '+12298148941'

print("=" * 60)
print("UPDATING TWILIO PHONE NUMBER")
print("=" * 60)

print(f"\nNew Twilio Phone Number: {NEW_TWILIO_NUMBER}")

try:
    # Update the .env file
    set_key(ENV_FILE, 'TWILIO_PHONE_NUMBER', NEW_TWILIO_NUMBER)
    
    print(f"\nSUCCESS! Updated .env file!")
    print(f"   TWILIO_PHONE_NUMBER={NEW_TWILIO_NUMBER}")
    
    # Reload and verify
    load_dotenv(override=True)
    updated_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    print(f"\nVerified! Current value: {updated_number}")
    
    print("\n" + "=" * 60)
    print("READY TO MAKE CALLS!")
    print("=" * 60)
    
    print("\nYour Twilio configuration:")
    print(f"  Twilio Number: {NEW_TWILIO_NUMBER}")
    print(f"  Your Number: {os.getenv('TEST_PHONE_NUMBER', '+919971458206')}")
    
    print("\nNext steps:")
    print("  1. Verify your personal number: python verify_phone_quick.py")
    print("  2. Make test call: python twilio_automated_call.py")
    
except Exception as e:
    print(f"\nError updating .env file: {e}")
    print("\nManual update:")
    print(f"   Open .env file and change:")
    print(f"   TWILIO_PHONE_NUMBER=+12298148941")

print("\n" + "=" * 60)

