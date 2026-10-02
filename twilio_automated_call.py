"""
Twilio Automated Call Script with Interactive Voice Response (IVR)
This script makes a call and asks predefined questions
"""
import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

# Load environment variables
load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Your phone number to call (from .env or hardcode for testing)
TO_PHONE_NUMBER = os.getenv('TEST_PHONE_NUMBER', '+918076640996')  # Your number

def create_twiml_for_questions():
    """
    Create TwiML (Twilio Markup Language) for interactive voice call
    This will be hosted on a URL that Twilio can access
    """
    response = VoiceResponse()
    
    # Welcome message
    response.say(
        "Hello! This is an automated call from Saheli Women Safety App. "
        "We have detected an emergency alert from your friend.",
        voice='alice',
        language='en-IN'
    )
    
    response.pause(length=1)
    
    # Question 1: Are you available to help?
    gather = Gather(
        num_digits=1,
        action='/voice/question1-response',  # URL to handle response
        method='POST',
        timeout=10
    )
    gather.say(
        "Question 1: Are you available to help your friend right now? "
        "Press 1 for Yes, Press 2 for No.",
        voice='alice',
        language='en-IN'
    )
    response.append(gather)
    
    # If no input, repeat
    response.say(
        "We did not receive your input. Please try again.",
        voice='alice',
        language='en-IN'
    )
    response.redirect('/voice/ask-questions')
    
    return str(response)


def create_twiml_question2():
    """Question 2 TwiML"""
    response = VoiceResponse()
    
    response.say(
        "Thank you for your response.",
        voice='alice',
        language='en-IN'
    )
    
    response.pause(length=1)
    
    # Question 2: Can you reach the location?
    gather = Gather(
        num_digits=1,
        action='/voice/question2-response',
        method='POST',
        timeout=10
    )
    gather.say(
        "Question 2: Can you reach the emergency location within 15 minutes? "
        "Press 1 for Yes, Press 2 for No.",
        voice='alice',
        language='en-IN'
    )
    response.append(gather)
    
    response.say(
        "We did not receive your input.",
        voice='alice',
        language='en-IN'
    )
    response.redirect('/voice/question2')
    
    return str(response)


def create_twiml_final():
    """Final message TwiML"""
    response = VoiceResponse()
    
    response.say(
        "Thank you for your responses. "
        "Your friend's location has been sent to your phone via SMS. "
        "Please contact them immediately or call police at 100. "
        "Stay safe. Goodbye.",
        voice='alice',
        language='en-IN'
    )
    
    response.hangup()
    
    return str(response)


def make_simple_automated_call():
    """
    Make a simple automated call with predefined message
    (No questions, just plays a message)
    """
    print("=" * 60)
    print("MAKING SIMPLE AUTOMATED CALL")
    print("=" * 60)
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        print("❌ ERROR: Twilio credentials not found in .env file!")
        print("\nPlease add to .env:")
        print("TWILIO_ACCOUNT_SID=your_account_sid")
        print("TWILIO_AUTH_TOKEN=your_auth_token")
        print("TWILIO_PHONE_NUMBER=your_twilio_number")
        return
    
    print(f"\n📞 Calling: {TO_PHONE_NUMBER}")
    print(f"📱 From: {TWILIO_PHONE_NUMBER}")
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Create TwiML for the call
        response = VoiceResponse()
        
        # Message with questions
        response.say(
            "Hello! This is an automated emergency call from Saheli Women Safety App. "
            "Your friend needs immediate help!",
            voice='alice',
            language='en-IN'
        )
        
        response.pause(length=1)
        
        # Question 1
        response.say(
            "Question 1: Are you available to help right now? "
            "If yes, please call your friend immediately.",
            voice='alice',
            language='en-IN'
        )
        
        response.pause(length=2)
        
        # Question 2
        response.say(
            "Question 2: Can you reach the emergency location within 15 minutes? "
            "If not, please call police at 100.",
            voice='alice',
            language='en-IN'
        )
        
        response.pause(length=1)
        
        response.say(
            "Your friend's location has been sent to your phone via SMS. "
            "Please act immediately. Stay safe. Goodbye.",
            voice='alice',
            language='en-IN'
        )
        
        # Make the call
        call = client.calls.create(
            twiml=str(response),
            to=TO_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER
        )
        
        print(f"\n✅ Call initiated successfully!")
        print(f"📞 Call SID: {call.sid}")
        print(f"📊 Status: {call.status}")
        print(f"\n⏱️  The call will start ringing in a few seconds...")
        print(f"📱 Answer the call to hear the automated message!")
        
        return call
        
    except Exception as e:
        print(f"\n❌ ERROR making call: {e}")
        print("\nPossible issues:")
        print("1. Invalid Twilio credentials")
        print("2. Twilio phone number not verified")
        print("3. Insufficient Twilio balance")
        print("4. Invalid 'To' phone number format")
        return None


def make_interactive_call_with_gather():
    """
    Make an interactive call that can collect responses
    NOTE: This requires a web server to handle responses
    """
    print("=" * 60)
    print("MAKING INTERACTIVE CALL (WITH QUESTIONS)")
    print("=" * 60)
    print("\n⚠️  NOTE: Interactive calls require a web server to handle responses.")
    print("For now, using simple automated call instead...\n")
    
    return make_simple_automated_call()


def test_twilio_connection():
    """Test if Twilio credentials are valid"""
    print("=" * 60)
    print("TESTING TWILIO CONNECTION")
    print("=" * 60)
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("❌ Twilio credentials not found!")
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Fetch account details
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        
        print(f"\n✅ Twilio connection successful!")
        print(f"📊 Account SID: {account.sid}")
        print(f"📊 Account Status: {account.status}")
        print(f"📊 Account Type: {account.type}")
        
        # Check phone number
        if TWILIO_PHONE_NUMBER:
            print(f"\n📱 Twilio Phone Number: {TWILIO_PHONE_NUMBER}")
            
            # Verify it's a valid Twilio number
            try:
                numbers = client.incoming_phone_numbers.list(phone_number=TWILIO_PHONE_NUMBER)
                if numbers:
                    print(f"✅ Phone number verified in your account")
                else:
                    print(f"⚠️  WARNING: {TWILIO_PHONE_NUMBER} not found in your account")
                    print(f"   You need to use a Twilio-provided number!")
            except Exception as e:
                print(f"⚠️  Could not verify phone number: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Twilio connection failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TWILIO AUTOMATED CALL SCRIPT")
    print("=" * 60)
    
    # Test connection first
    if test_twilio_connection():
        print("\n" + "=" * 60)
        print("READY TO MAKE CALL")
        print("=" * 60)
        
        choice = input("\nMake automated call now? (y/n): ").strip().lower()
        
        if choice == 'y':
            make_simple_automated_call()
        else:
            print("\n✅ Test completed. Run script again to make a call.")
    else:
        print("\n❌ Please fix Twilio configuration first!")
    
    print("\n" + "=" * 60)
    print("Script completed!")
    print("=" * 60)

