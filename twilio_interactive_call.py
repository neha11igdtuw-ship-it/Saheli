"""
Advanced Twilio Interactive Call with Flask Server
This handles user responses to questions in real-time
"""
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Create Flask app for handling Twilio callbacks
app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TO_PHONE_NUMBER = os.getenv('TEST_PHONE_NUMBER', '+919971458206')

# Store responses (in production, use database)
call_responses = {}


@app.route('/voice/start', methods=['POST'])
def start_call():
    """Initial call - Welcome message and first question"""
    response = VoiceResponse()
    
    # Welcome message
    response.say(
        "Hello! This is an automated emergency call from Saheli Women Safety App. "
        "Your friend has triggered an S O S alert and needs immediate help.",
        voice='alice',
        language='en-IN'
    )
    
    response.pause(length=1)
    
    # Question 1: Are you available?
    gather = Gather(
        num_digits=1,
        action='/voice/question1',
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
    
    # If no input
    response.say("We did not receive your input. Goodbye.", voice='alice', language='en-IN')
    response.hangup()
    
    return str(response)


@app.route('/voice/question1', methods=['POST'])
def handle_question1():
    """Handle response to question 1"""
    response = VoiceResponse()
    
    # Get the digit pressed
    digit_pressed = request.values.get('Digits', None)
    call_sid = request.values.get('CallSid', 'unknown')
    
    # Store response
    if call_sid not in call_responses:
        call_responses[call_sid] = {}
    
    if digit_pressed == '1':
        call_responses[call_sid]['available'] = 'yes'
        response.say("Great! Thank you for being available.", voice='alice', language='en-IN')
    elif digit_pressed == '2':
        call_responses[call_sid]['available'] = 'no'
        response.say("We understand. We will contact other emergency contacts.", voice='alice', language='en-IN')
    else:
        response.say("Invalid input.", voice='alice', language='en-IN')
    
    response.pause(length=1)
    
    # Question 2: Can you reach location?
    gather = Gather(
        num_digits=1,
        action='/voice/question2',
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
    
    response.say("We did not receive your input. Goodbye.", voice='alice', language='en-IN')
    response.hangup()
    
    return str(response)


@app.route('/voice/question2', methods=['POST'])
def handle_question2():
    """Handle response to question 2"""
    response = VoiceResponse()
    
    # Get the digit pressed
    digit_pressed = request.values.get('Digits', None)
    call_sid = request.values.get('CallSid', 'unknown')
    
    # Store response
    if call_sid not in call_responses:
        call_responses[call_sid] = {}
    
    if digit_pressed == '1':
        call_responses[call_sid]['can_reach'] = 'yes'
        response.say(
            "Excellent! Please proceed to the location immediately. "
            "Your friend's exact location has been sent to your phone via SMS.",
            voice='alice',
            language='en-IN'
        )
    elif digit_pressed == '2':
        call_responses[call_sid]['can_reach'] = 'no'
        response.say(
            "We understand. Please call your friend immediately to check on them. "
            "If needed, please call police at 100.",
            voice='alice',
            language='en-IN'
        )
    else:
        response.say("Invalid input.", voice='alice', language='en-IN')
    
    response.pause(length=1)
    
    # Final message
    response.say(
        "Thank you for your responses. "
        "Please contact your friend immediately or call emergency services. "
        "Stay safe. Goodbye.",
        voice='alice',
        language='en-IN'
    )
    
    response.hangup()
    
    # Print responses for debugging
    print(f"\n📊 Call Responses for {call_sid}:")
    print(f"   Available: {call_responses[call_sid].get('available', 'no response')}")
    print(f"   Can Reach: {call_responses[call_sid].get('can_reach', 'no response')}")
    
    return str(response)


@app.route('/voice/status', methods=['POST'])
def call_status():
    """Handle call status updates"""
    call_sid = request.values.get('CallSid')
    call_status = request.values.get('CallStatus')
    
    print(f"📞 Call {call_sid} status: {call_status}")
    
    return '', 200


def make_interactive_call():
    """Initiate the interactive call"""
    print("=" * 60)
    print("MAKING INTERACTIVE TWILIO CALL")
    print("=" * 60)
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        print("❌ ERROR: Twilio credentials not configured!")
        return
    
    print(f"\n📞 Calling: {TO_PHONE_NUMBER}")
    print(f"📱 From: {TWILIO_PHONE_NUMBER}")
    print(f"\n⚠️  NOTE: This requires the Flask server to be running!")
    print(f"   Server URL: http://your-server.com/voice/start")
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # For local testing, you need ngrok or similar to expose Flask server
        # Replace with your actual server URL
        server_url = "http://your-server-url.com/voice/start"
        
        call = client.calls.create(
            url=server_url,
            to=TO_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER,
            status_callback=server_url.replace('/start', '/status'),
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        
        print(f"\n✅ Call initiated!")
        print(f"📞 Call SID: {call.sid}")
        print(f"📊 Status: {call.status}")
        
        return call
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TWILIO INTERACTIVE CALL SERVER")
    print("=" * 60)
    print("\nThis Flask server handles interactive voice responses.")
    print("\nTo use:")
    print("1. Run this script: python twilio_interactive_call.py")
    print("2. Expose server using ngrok: ngrok http 5001")
    print("3. Update server_url in make_interactive_call() with ngrok URL")
    print("4. Call make_interactive_call() to initiate call")
    print("\n" + "=" * 60)
    
    # Run Flask server
    app.run(host='0.0.0.0', port=5001, debug=True)

