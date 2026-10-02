# 📞 TWILIO AUTOMATED CALL SCRIPTS

## 🎯 **TWO SCRIPTS CREATED:**

I've created **2 scripts** for making automated Twilio calls with questions:

---

## 📝 **SCRIPT 1: Simple Automated Call** (RECOMMENDED FOR TESTING)

**File**: `twilio_automated_call.py`

### **What It Does:**
- ✅ Makes an automated call to a phone number
- ✅ Plays a voice message with 2 predefined questions
- ✅ No server needed (works standalone)
- ✅ Perfect for testing and simple use cases

### **Questions Asked:**
1. "Are you available to help right now? If yes, please call your friend immediately."
2. "Can you reach the emergency location within 15 minutes? If not, please call police at 100."

### **How to Use:**

#### **Step 1: Add Phone Number to .env**
```env
# Add this line to your .env file:
TEST_PHONE_NUMBER=+919971458206  # Your phone number to test
```

#### **Step 2: Run the Script**
```bash
cd C:\SelfProject\saheliproject
.\venv\Scripts\Activate.ps1
python twilio_automated_call.py
```

#### **Step 3: Follow Prompts**
```
Testing Twilio connection...
✅ Twilio connection successful!

Make automated call now? (y/n): y

✅ Call initiated successfully!
📞 Call SID: CA1234567890...
📊 Status: queued

⏱️  The call will start ringing in a few seconds...
📱 Answer the call to hear the automated message!
```

---

## 📝 **SCRIPT 2: Interactive Call with Responses** (ADVANCED)

**File**: `twilio_interactive_call.py`

### **What It Does:**
- ✅ Makes an interactive call
- ✅ Asks questions and **collects responses**
- ✅ User presses 1 or 2 to answer
- ✅ Responds based on user input
- ⚠️ Requires Flask server + ngrok

### **Questions Asked:**
1. "Are you available to help your friend right now? Press 1 for Yes, Press 2 for No."
2. "Can you reach the emergency location within 15 minutes? Press 1 for Yes, Press 2 for No."

### **How It Works:**
```
Call starts
    ↓
Question 1: "Are you available?"
    ↓
User presses 1 (Yes) or 2 (No)
    ↓
Response: "Great! Thank you for being available." OR "We will contact others."
    ↓
Question 2: "Can you reach location?"
    ↓
User presses 1 (Yes) or 2 (No)
    ↓
Response: "Please proceed immediately!" OR "Please call police."
    ↓
Final message and hangup
```

### **How to Use:**

#### **Step 1: Install ngrok** (to expose local server)
```bash
# Download from: https://ngrok.com/download
# Or use: choco install ngrok (if you have Chocolatey)
```

#### **Step 2: Run Flask Server**
```bash
cd C:\SelfProject\saheliproject
.\venv\Scripts\Activate.ps1
python twilio_interactive_call.py
```

#### **Step 3: Expose Server with ngrok** (in another terminal)
```bash
ngrok http 5001
```

You'll get a URL like: `https://abc123.ngrok.io`

#### **Step 4: Update Script**
Edit `twilio_interactive_call.py` line 140:
```python
server_url = "https://abc123.ngrok.io/voice/start"  # Your ngrok URL
```

#### **Step 5: Make Call**
Run the `make_interactive_call()` function

---

## 🎯 **WHICH SCRIPT TO USE?**

### **For Testing / Simple Use:**
✅ **Use Script 1** (`twilio_automated_call.py`)
- No server needed
- Easy to run
- Just plays message with questions
- Perfect for testing Twilio

### **For Production / Interactive:**
✅ **Use Script 2** (`twilio_interactive_call.py`)
- Collects user responses
- Interactive experience
- Requires server setup
- Best for real app

---

## 🚀 **QUICK START (Script 1):**

### **1. Check .env File**
Make sure you have:
```env
TWILIO_ACCOUNT_SID=AC816b6a07c203ffa6c2ca0e4f44277082
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567  # Must be Twilio number!
TEST_PHONE_NUMBER=+919971458206    # Your number to call
```

### **2. Run Script**
```powershell
cd C:\SelfProject\saheliproject
.\venv\Scripts\Activate.ps1
python twilio_automated_call.py
```

### **3. Answer Call**
- Your phone will ring in 5-10 seconds
- Answer it
- Listen to automated message with questions
- Done!

---

## 📊 **WHAT YOU'LL HEAR:**

### **Script 1 (Simple):**
```
"Hello! This is an automated emergency call from Saheli Women Safety App.
Your friend needs immediate help!

[pause]

Question 1: Are you available to help right now?
If yes, please call your friend immediately.

[pause]

Question 2: Can you reach the emergency location within 15 minutes?
If not, please call police at 100.

[pause]

Your friend's location has been sent to your phone via SMS.
Please act immediately. Stay safe. Goodbye."

[call ends]
```

### **Script 2 (Interactive):**
```
"Hello! This is an automated emergency call from Saheli Women Safety App.
Your friend has triggered an S O S alert and needs immediate help.

[pause]

Question 1: Are you available to help your friend right now?
Press 1 for Yes, Press 2 for No."

[waits for input]

[If press 1:]
"Great! Thank you for being available.

[pause]

Question 2: Can you reach the emergency location within 15 minutes?
Press 1 for Yes, Press 2 for No."

[waits for input]

[If press 1:]
"Excellent! Please proceed to the location immediately.
Your friend's exact location has been sent to your phone via SMS.

[pause]

Thank you for your responses.
Please contact your friend immediately or call emergency services.
Stay safe. Goodbye."

[call ends]
```

---

## 🔧 **TROUBLESHOOTING:**

### **Error: "Invalid Twilio phone number"**
**Problem**: Using personal number instead of Twilio number

**Solution**:
1. Go to: https://www.twilio.com/console/phone-numbers
2. Get a Twilio phone number (FREE with trial)
3. Update `.env` with Twilio number:
```env
TWILIO_PHONE_NUMBER=+15551234567  # Twilio number, not yours!
```

### **Error: "Insufficient balance"**
**Problem**: Trial account has limits

**Solution**:
- Trial accounts can only call verified numbers
- Verify your number at: https://www.twilio.com/console/phone-numbers/verified
- Or upgrade account

### **Call Not Ringing**
**Check**:
1. Phone number format: `+919971458206` (with country code)
2. Twilio credentials are correct
3. Phone is not on Do Not Disturb
4. Check Twilio console for call logs

---

## 💡 **CUSTOMIZATION:**

### **Change Questions:**
Edit the `response.say()` lines in the script:

```python
response.say(
    "Your custom question here?",
    voice='alice',
    language='en-IN'
)
```

### **Change Voice:**
Options: `'alice'`, `'man'`, `'woman'`

### **Change Language:**
Options: `'en-IN'` (Indian English), `'en-US'`, `'en-GB'`

### **Add More Questions:**
Just add more `response.say()` blocks:

```python
response.pause(length=1)
response.say(
    "Question 3: Your question here?",
    voice='alice',
    language='en-IN'
)
```

---

## 📱 **INTEGRATE WITH YOUR APP:**

To use in your Saheli app, add to `app.py`:

```python
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

def make_emergency_call(to_phone, user_name, location):
    """Make automated emergency call"""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    response = VoiceResponse()
    response.say(
        f"Emergency! Your friend {user_name} needs help at {location}. "
        f"Please call them immediately or contact police.",
        voice='alice',
        language='en-IN'
    )
    
    call = client.calls.create(
        twiml=str(response),
        to=to_phone,
        from_=TWILIO_PHONE_NUMBER
    )
    
    return call.sid
```

Then call it from your SOS trigger:

```python
# In trigger_sos route
for contact in contacts:
    if contact.phone_number:
        make_emergency_call(
            contact.phone_number,
            user.username,
            location_address
        )
```

---

## ✅ **SUMMARY:**

| Feature | Script 1 (Simple) | Script 2 (Interactive) |
|---------|------------------|----------------------|
| **Ease of Use** | ✅ Very Easy | ⚠️ Requires Setup |
| **Server Needed** | ❌ No | ✅ Yes (Flask + ngrok) |
| **Collects Responses** | ❌ No | ✅ Yes |
| **Questions** | ✅ 2 questions | ✅ 2 questions |
| **Testing** | ✅ Perfect | ⚠️ Complex |
| **Production** | ✅ Good | ✅ Better |

---

## 🚀 **RECOMMENDED NEXT STEPS:**

1. **Test Script 1** first (simple, no server)
2. **Verify it works** with your Twilio account
3. **Customize questions** as needed
4. **Integrate into app** (optional)
5. **Try Script 2** if you need interactive responses

---

**Ready to test? Run Script 1 now!** 📞✨

```bash
cd C:\SelfProject\saheliproject
.\venv\Scripts\Activate.ps1
python twilio_automated_call.py
```

Your phone will ring with an automated emergency message! 🎉

