# 🚨 Setting Up Real SOS Alerts (Email & SMS)

Your SOS alerts will now send **REAL** emails and SMS to your trusted contacts!

---

## 📧 **Option 1: Email Alerts (FREE & EASY!)**

### **Using Gmail:**

**Step 1: Enable 2-Step Verification**
1. Go to: https://myaccount.google.com/security
2. Enable **"2-Step Verification"** if not already enabled

**Step 2: Create App Password**
1. Go to: https://myaccount.google.com/apppasswords
2. Select **"Mail"** and **"Other"** (Custom name: "Saheli App")
3. Click **"Generate"**
4. Copy the 16-character password (remove spaces)

**Step 3: Add to .env file**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  (the generated app password)
```

### **Using Outlook/Hotmail:**
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-outlook-password
```

---

## 📱 **Option 2: SMS Alerts (Recommended!)**

### **Using Twilio (FREE Trial)**

**Step 1: Sign Up**
1. Go to: https://www.twilio.com/try-twilio
2. Sign up for FREE trial account
3. Verify your phone number
4. You get **$15.50 FREE credit** (can send ~500 SMS)

**Step 2: Get Credentials**
1. After login, go to **Console Dashboard**
2. Find your:
   - **Account SID**: `ACxxxxxxxxxxxxxxxxxxxxx`
   - **Auth Token**: Click "Show" to reveal
   - **Phone Number**: Click "Get a Number" → Select any available number

**Step 3: Add to .env file**
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

**Step 4: Verify Recipient Numbers (Trial Only)**
- During free trial, you must verify each recipient's phone number in Twilio console
- Go to: Phone Numbers → Verified Caller IDs → Add new number
- Enter your trusted contacts' numbers and verify them

---

## 🎯 **Quick Setup (5 Minutes)**

### **For Testing - Email Only:**
```bash
1. Use Gmail
2. Generate App Password
3. Add to .env:
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
4. Restart app
5. Test SOS!
```

### **For Production - Email + SMS:**
```bash
1. Setup Gmail (as above)
2. Sign up for Twilio
3. Get Twilio credentials
4. Add both to .env
5. Verify phone numbers (if using trial)
6. Restart app
7. Ready to go!
```

---

## ✅ **What Happens When You Trigger SOS:**

1. **Location Capture**: Gets your exact GPS coordinates
2. **Email Alert Sent**:
   - Beautiful HTML email
   - Shows your location on Google Maps
   - Includes timestamp
   - Emergency instructions for recipients
3. **SMS Alert Sent**:
   - Urgent text message
   - Direct link to your location
   - Call-to-action (call you or police)
4. **Database Record**: Saves alert history

### **Email Preview:**
```
Subject: 🚨 URGENT: YourName needs help!

Your friend YourName needs IMMEDIATE help!

📍 Location: Sector 20, Noida
⏰ Time: 10:30 PM

[VIEW LOCATION ON MAP button]

⚠️ WHAT TO DO:
• Call YourName immediately
• If no response, contact police (100)
• Share location with others
```

### **SMS Preview:**
```
🚨 EMERGENCY SOS ALERT!

YourName needs IMMEDIATE help!

Location: Sector 20, Noida
Time: 10:30 PM

Map: https://google.com/maps?q=lat,lng

CALL THEM NOW or contact police (100)!

- Saheli Safety App
```

---

## 🔧 **Configuration Options:**

| Service | Cost | Setup Time | Reliability |
|---------|------|------------|-------------|
| **Gmail (Email)** | FREE | 2 minutes | ⭐⭐⭐⭐⭐ Excellent |
| **Twilio (SMS)** | $15 FREE trial | 5 minutes | ⭐⭐⭐⭐⭐ Excellent |
| **Both** | Mostly FREE | 7 minutes | ⭐⭐⭐⭐⭐ Best! |

---

## 💡 **Pro Tips:**

1. **Email is easiest** - Start with this!
2. **SMS is most reliable** - Contacts get instant notification
3. **Use both** for maximum safety
4. **Test before emergency** - Add yourself as contact and test
5. **Keep credentials secure** - Never commit .env to GitHub!

---

## 🧪 **Testing:**

1. Add a trusted contact with your own email/phone
2. Trigger SOS alert
3. Check your email inbox
4. Check your phone SMS
5. Verify location link works

---

## ⚠️ **Troubleshooting:**

### **Email not sending?**
- Check Gmail App Password is correct (no spaces)
- Make sure 2-Step Verification is enabled
- Check spam folder
- Try Outlook/Hotmail if Gmail doesn't work

### **SMS not sending?**
- Verify phone number in Twilio console (for trial)
- Check Twilio credits balance
- Make sure phone number format is correct: +1234567890
- Check Twilio logs in console

### **"Email not configured" message?**
- Make sure .env file has SMTP_USERNAME and SMTP_PASSWORD
- Restart the app after adding credentials

---

## 💰 **Costs:**

**FREE Options:**
- **Gmail**: Unlimited emails, FREE ✅
- **Twilio Trial**: $15 credit = ~500 SMS ✅

**Paid (if needed later):**
- **Twilio SMS**: ~$0.0075 per SMS in India
- **SendGrid** (alternative): 100 emails/day FREE

---

## 🎀 **You're All Set!**

Once configured, your SOS alerts will send **REAL** messages to your trusted contacts!

No more fake popups - this is **production-ready** emergency alert system! 💖✨

---

**Setup now**: Edit `.env` file and add your credentials!

