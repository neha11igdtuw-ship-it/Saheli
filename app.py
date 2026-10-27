from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import desc
import os
import re
import json
import random
import requests
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from concurrent.futures import ThreadPoolExecutor
import csv
from functools import lru_cache
import socket

# Load environment variables from .env file
# NOTE: On some organization-managed laptops, environment variables may be pre-set (even as empty strings).
# We use override=True so the values saved in `.env` from the Settings page actually take effect after restart.
load_dotenv(override=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Render's free tier has no persistent disk: a SQLite file on it is wiped on
# every redeploy and every restart after the service sleeps from inactivity,
# silently losing every signup, trusted contact, and SOS alert. Use Postgres
# (DATABASE_URL, e.g. Render's managed Postgres add-on) whenever it's
# configured; fall back to local SQLite only for local development.
_database_url = os.environ.get('DATABASE_URL', '').strip()
if _database_url:
    # Render (and some other hosts) still hand out the legacy 'postgres://'
    # scheme; SQLAlchemy's psycopg2 dialect requires 'postgresql://'.
    if _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = _database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///saheli.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# API Keys Configuration
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')
IPGEOLOCATION_API_KEY = os.environ.get('IPGEOLOCATION_API_KEY', '')

# Email/SMS Configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_USE_SSL = os.environ.get('SMTP_USE_SSL', '').strip().lower() in ('1', 'true', 'yes', 'on')
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '').strip()
BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', SMTP_USERNAME).strip()
BREVO_SENDER_NAME = os.environ.get('BREVO_SENDER_NAME', 'Saheli').strip()
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
BREVO_WHATSAPP_SENDER_NUMBER = os.environ.get('BREVO_WHATSAPP_SENDER_NUMBER', '').strip()
BREVO_WHATSAPP_TEMPLATE_ID = os.environ.get('BREVO_WHATSAPP_TEMPLATE_ID', '').strip()
NCRB_DATA_FILE = os.environ.get('NCRB_DATA_FILE', '')

db = SQLAlchemy(app)
app.jinja_env.filters['fromjson'] = lambda s: json.loads(s) if s else None

# ==================== DATABASE MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    emergency_contact = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    adaptive_mode_enabled = db.Column(db.Boolean, default=True)
    preferred_language = db.Column(db.String(20), default='en')
    
    # Relationships
    trusted_contacts = db.relationship('TrustedContact', backref='user', lazy=True, cascade='all, delete-orphan')
    sos_alerts = db.relationship('SOSAlert', backref='user', lazy=True, cascade='all, delete-orphan')
    community_reports = db.relationship('CommunityReport', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class TrustedContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    relationship = db.Column(db.String(50), nullable=True)  # Mom, Sister, Friend, etc.
    is_primary = db.Column(db.Boolean, default=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TrustedContact {self.name}>'


class SOSAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # voice, gesture, manual, auto
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_address = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_resolved = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    # Dispatch lifecycle: 'pending' (grace window, cancellable) -> 'sending' -> 'sent' | 'cancelled' | 'failed'
    dispatch_status = db.Column(db.String(20), default='pending', nullable=False)
    contacts_total = db.Column(db.Integer, default=0)
    results_json = db.Column(db.Text, nullable=True)  # per-channel attempted/sent counts + per-contact outcomes
    location_attached = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<SOSAlert {self.id} - {self.alert_type}>'


class SafetyZone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area_name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    safety_score = db.Column(db.Float, nullable=False)  # 0-100
    lighting_score = db.Column(db.Float, nullable=True)  # 0-100
    crowd_density = db.Column(db.String(20), nullable=True)  # low, medium, high
    crime_rate = db.Column(db.String(20), nullable=True)  # low, medium, high
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<SafetyZone {self.area_name} - Score: {self.safety_score}>'


class CommunityReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    area_name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    report_type = db.Column(db.String(50), nullable=False)  # safe, unsafe, incident
    description = db.Column(db.Text, nullable=True)
    safety_rating = db.Column(db.Integer, nullable=True)  # 1-5
    is_verified = db.Column(db.Boolean, default=False)
    helpful_count = db.Column(db.Integer, default=0)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CommunityReport {self.area_name} - {self.report_type}>'


class SafetyBeacon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    beacon_type = db.Column(db.String(50), nullable=False)  # metro, shop, police_station, hospital
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(500), nullable=True)
    contact_number = db.Column(db.String(15), nullable=True)
    is_verified = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SafetyBeacon {self.name}>'


# ==================== HELPER FUNCTIONS ====================

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"


# ==================== SOS ALERT FUNCTIONS ====================

def send_email_alert(to_email, user_name, location_url, location_address):
    """Send email alert to trusted contact"""
    # Allow Brevo API fallback when SMTP is blocked
    smtp_configured = bool(SMTP_USERNAME and SMTP_PASSWORD and '@' in SMTP_USERNAME)
    brevo_configured = bool(BREVO_API_KEY and BREVO_SENDER_EMAIL and '@' in BREVO_SENDER_EMAIL)

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"URGENT: {user_name} needs help"
        msg['From'] = SMTP_USERNAME or (BREVO_SENDER_EMAIL if BREVO_SENDER_EMAIL else "Saheli")
        msg['To'] = to_email

        # Bravery & Wisdom email styling (matches new UI theme)
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f8fafc;">
          <div style="max-width: 600px; margin: 0 auto; background: white; padding: 28px; border-radius: 16px; border: 1px solid #cbd5e1; box-shadow: 0 10px 25px rgba(15,23,42,0.10);">
            <div style="background: linear-gradient(180deg, #0b1220, #111827); color: white; padding: 16px 18px; border-radius: 12px;">
              <h1 style="margin: 0; font-size: 20px;">Emergency SOS Alert</h1>
              <p style="margin: 6px 0 0 0; opacity: 0.9; font-size: 13px;">Saheli Women Safety App</p>
            </div>

            <div style="margin-top: 18px; padding: 16px; border-radius: 12px; background: #fffbeb; border: 1px solid rgba(180,83,9,0.35);">
              <p style="margin: 0; color: #0f172a; font-size: 15px;">
                <strong>{user_name}</strong> triggered an SOS and may need immediate help.
              </p>
              <p style="margin: 10px 0 0 0; color: #475569; font-size: 13px;">
                <strong>Location:</strong> {location_address}<br>
                <strong>Time:</strong> {datetime.now().strftime('%I:%M %p, %B %d, %Y')}
              </p>
            </div>

            <div style="text-align: center; margin: 18px 0;">
              <a href="{location_url}" style="display: inline-block; background: #0f766e; color: white; padding: 12px 18px; text-decoration: none; border-radius: 12px; font-weight: bold;">
                View Location on Map
              </a>
            </div>

            <div style="border-top: 1px solid #e2e8f0; padding-top: 14px; color: #475569; font-size: 13px;">
              <strong>What to do:</strong>
              <ol style="margin: 8px 0 0 18px;">
                <li>Call {user_name} immediately</li>
                <li>If no response, contact local authorities</li>
                <li>Share the map link with nearby helpers</li>
              </ol>
            </div>
          </div>
        </body>
        </html>
        """

        text = (
            f"EMERGENCY SOS ALERT\n\n"
            f"{user_name} may need immediate help.\n"
            f"Location: {location_address}\n"
            f"Time: {datetime.now().strftime('%I:%M %p, %B %d, %Y')}\n"
            f"Map: {location_url}\n"
        )

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        # Prefer Brevo when available (HTTPS works even when SMTP ports are blocked)
        if brevo_configured:
            ok2, err2 = send_email_via_brevo(to_email, msg['Subject'], html, text)
            if ok2:
                print(f"✅ Brevo email sent to {to_email}")
                return True
            print(f"❌ Brevo email failed: {err2}")
            # If Brevo fails for any reason, try SMTP as fallback (if configured)
            if smtp_configured:
                ok, err = smtp_send_message(msg)
                if ok:
                    print(f"✅ Email sent to {to_email}")
                    return True
                print(f"❌ SMTP Email error: {err}")
            return False

        # Brevo not configured → use SMTP
        if smtp_configured:
            ok, err = smtp_send_message(msg)
            if not ok:
                print(f"❌ SMTP Email error: {err}")
                return False
            print(f"✅ Email sent to {to_email}")
            return True

        print("❌ Email not configured (SMTP missing and Brevo not configured).")
        return False

        print(f"✅ Email sent to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP auth failed: {e}")
        return False
    except Exception as e:
        print(f"❌ SMTP Email error: {e}")
        return False


def send_call_notification_email(to_email, user_name):
    """Notify a trusted contact that the user is trying to call them."""
    smtp_configured = bool(SMTP_USERNAME and SMTP_PASSWORD and '@' in SMTP_USERNAME)
    brevo_configured = bool(BREVO_API_KEY and BREVO_SENDER_EMAIL and '@' in BREVO_SENDER_EMAIL)
    if not to_email:
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Saheli: {user_name} is trying to reach you"
        msg['From'] = SMTP_USERNAME or (BREVO_SENDER_EMAIL if BREVO_SENDER_EMAIL else "Saheli")
        msg['To'] = to_email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f8fafc;">
          <div style="max-width: 600px; margin: 0 auto; background: white; padding: 28px; border-radius: 16px; border: 1px solid #cbd5e1;">
            <div style="background: linear-gradient(180deg, #0b1220, #111827); color: white; padding: 16px 18px; border-radius: 12px;">
              <h1 style="margin: 0; font-size: 18px;">Call Notification</h1>
            </div>
            <p style="margin: 16px 0 0 0; color: #0f172a;">
              <strong>{user_name}</strong> initiated a call to you from the Saheli app.
            </p>
            <p style="margin: 10px 0 0 0; color: #475569; font-size: 13px;">
              Time: {datetime.now().strftime('%I:%M %p, %B %d, %Y')}
            </p>
            <p style="margin: 16px 0 0 0; color: #475569; font-size: 13px;">
              If you missed the call, please call them back and check on their safety.
            </p>
          </div>
        </body>
        </html>
        """

        text = (
            f"Call Notification\n\n"
            f"{user_name} initiated a call to you from Saheli.\n"
            f"Time: {datetime.now().strftime('%I:%M %p, %B %d, %Y')}\n"
            f"If you missed the call, please call them back and check on their safety.\n"
        )

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        # Prefer Brevo when available
        if brevo_configured:
            ok2, err2 = send_email_via_brevo(to_email, msg['Subject'], html, text)
            if ok2:
                print(f"✅ Brevo call-notification email sent to {to_email}")
                return True
            print(f"❌ Brevo call-notification email failed: {err2}")
            # fallback to SMTP if configured
            if smtp_configured:
                ok, err = smtp_send_message(msg)
                if ok:
                    return True
                print(f"❌ Call notification SMTP error: {err}")
            return False

        # Brevo not configured → use SMTP
        if smtp_configured:
            ok, err = smtp_send_message(msg)
            if not ok:
                print(f"❌ Call notification email error: {err}")
                return False
            return True

        return False
    except Exception as e:
        print(f"❌ Call notification email error: {e}")
        return False


def smtp_send_message(msg):
    """
    Robust SMTP sender.
    - Uses STARTTLS on SMTP_PORT by default
    - Falls back to implicit SSL (465) if STARTTLS times out/fails
    """
    if not SMTP_SERVER or not SMTP_PORT:
        return False, "SMTP server/port not configured"

    def _send_starttls(server, port):
        with smtplib.SMTP(server, port, timeout=25) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)

    def _send_ssl(server, port):
        with smtplib.SMTP_SSL(server, port, timeout=25) as s:
            s.ehlo()
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)

    # If user explicitly configured SSL, honor it
    if SMTP_USE_SSL or SMTP_PORT == 465:
        try:
            _send_ssl(SMTP_SERVER, SMTP_PORT)
            return True, None
        except (socket.timeout, TimeoutError) as e:
            return False, f"SSL timed out ({SMTP_SERVER}:{SMTP_PORT})"
        except Exception as e:
            return False, f"SSL error ({SMTP_SERVER}:{SMTP_PORT}): {e}"

    # Try STARTTLS on configured port
    try:
        _send_starttls(SMTP_SERVER, SMTP_PORT)
        return True, None
    except smtplib.SMTPAuthenticationError as e:
        return False, f"auth failed (use Gmail App Password): {e}"
    except (socket.timeout, TimeoutError):
        # common on restricted networks; try SSL 465
        try:
            _send_ssl(SMTP_SERVER, 465)
            return True, None
        except Exception as e:
            return False, f"STARTTLS timed out and SSL(465) failed: {e}"
    except Exception as e:
        # Try SSL 465 as a last resort
        try:
            _send_ssl(SMTP_SERVER, 465)
            return True, None
        except Exception as e2:
            return False, f"STARTTLS failed ({e}); SSL(465) failed ({e2})"


def send_email_via_brevo(to_email, subject, html_content, text_content):
    """
    Send email using Brevo Transactional Email API (HTTPS/443).
    Requires:
      - BREVO_API_KEY
      - BREVO_SENDER_EMAIL
    """
    if not BREVO_API_KEY:
        return False, "BREVO_API_KEY not configured"
    if not (BREVO_SENDER_EMAIL and '@' in BREVO_SENDER_EMAIL):
        return False, "BREVO_SENDER_EMAIL not configured/invalid"

    payload = {
        "sender": {"email": BREVO_SENDER_EMAIL, "name": BREVO_SENDER_NAME or "Saheli"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content,
    }

    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            data=json.dumps(payload),
            timeout=20,
        )
        if 200 <= resp.status_code < 300:
            return True, None
        return False, f"Brevo HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Brevo error: {e}"


def send_sms_alert(to_phone, user_name, location_url, location_address):
    """Send SMS alert using Twilio"""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        print("Twilio not configured. Skipping SMS alert.")
        return False
    
    try:
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message_body = f"""
🚨 EMERGENCY SOS ALERT!

{user_name} needs IMMEDIATE help!

Location: {location_address}
Time: {datetime.now().strftime('%I:%M %p')}

Map: {location_url}

CALL THEM NOW or contact police (100)!

- Saheli Safety App
        """
        
        message = client.messages.create(
            body=message_body.strip(),
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        print(f"✅ SMS sent to {to_phone}: {message.sid}")
        return True
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False


def make_voice_call(to_phone, user_name, location_address):
    """Make automated voice call using Twilio"""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        print("Twilio not configured. Skipping voice call.")
        return False
    
    try:
        from twilio.rest import Client
        from twilio.twiml.voice_response import VoiceResponse
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Create TwiML for voice message
        response = VoiceResponse()
        response.say(
            f"Emergency S O S Alert! Your friend {user_name} needs immediate help! "
            f"They are located at {location_address}. "
            f"Please call them now or contact police at 100. "
            f"This is an automated message from Saheli Safety App.",
            voice='alice',
            language='en-IN'
        )
        
        # Make the call
        call = client.calls.create(
            twiml=str(response),
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        print(f"✅ Voice call initiated to {to_phone}: {call.sid}")
        return True
    except Exception as e:
        print(f"❌ Voice call error: {e}")
        return False


def _normalize_whatsapp_number(phone_number):
    """Brevo's WhatsApp API expects digits only (country code + number, no '+' or spaces)."""
    return re.sub(r'\D', '', phone_number or '')


def send_whatsapp_alert(to_phone, user_name, location_url, location_address):
    """Send SOS alert via WhatsApp using Brevo's transactional WhatsApp API.

    Requires BREVO_API_KEY (with 'Transactional WhatsApp' permission),
    BREVO_WHATSAPP_SENDER_NUMBER (a WhatsApp sender activated on Brevo), and
    BREVO_WHATSAPP_TEMPLATE_ID (a Meta-approved message template's id) to be
    configured. WhatsApp Business policy requires every business-initiated
    message to reference an approved template id - free-form text is not
    supported here.
    """
    if not BREVO_API_KEY or not BREVO_WHATSAPP_SENDER_NUMBER or not BREVO_WHATSAPP_TEMPLATE_ID:
        print("Brevo WhatsApp not configured. Skipping WhatsApp alert.")
        return False

    contact_number = _normalize_whatsapp_number(to_phone)
    if not contact_number:
        return False

    # NOTE: Brevo's public API reference does not document the exact field name for
    # injecting template variables into a WhatsApp send - "params" is our best guess
    # based on Brevo's other transactional-messaging endpoints. If Brevo rejects this
    # field, its 400 response's `message` will say so; adjust the key name (or template
    # design) based on that real error rather than this comment.
    payload = {
        "senderNumber": _normalize_whatsapp_number(BREVO_WHATSAPP_SENDER_NUMBER),
        "contactNumbers": [contact_number],
        "templateId": int(BREVO_WHATSAPP_TEMPLATE_ID),
        "params": {
            "user_name": user_name,
            "location_address": location_address,
            "location_url": location_url,
        },
    }

    try:
        resp = requests.post(
            "https://api.brevo.com/v3/whatsapp/sendMessage",
            headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json", "Accept": "application/json"},
            data=json.dumps(payload),
            timeout=20,
        )
        if 200 <= resp.status_code < 300:
            print(f"✅ WhatsApp alert sent to {to_phone}: {resp.json().get('messageId')}")
            return True
        print(f"❌ WhatsApp alert error: HTTP {resp.status_code} {resp.text}")
        return False
    except Exception as e:
        print(f"❌ WhatsApp alert error: {e}")
        return False


def dispatch_sos_alert(alert_id, grace_seconds=0):
    """Actually send SOS alerts for a given SOSAlert row and persist real,
    per-channel results so the UI can show honest status (never a blind
    'sent successfully' before anything was attempted).

    Runs on a background timer so the user gets a short, cancellable grace
    window ("I'm safe") before contacts are actually notified.
    """
    def _run():
        with app.app_context():
            alert = db.session.get(SOSAlert, alert_id)
            if not alert or alert.dispatch_status != 'pending':
                return  # cancelled, or already handled

            alert.dispatch_status = 'sending'
            db.session.commit()

            user = db.session.get(User, alert.user_id)
            contacts = TrustedContact.query.filter_by(user_id=user.id).all()
            latitude, longitude = alert.latitude, alert.longitude
            location_address = alert.location_address or 'Location not specified'
            map_url = (
                f"https://www.google.com/maps?q={latitude},{longitude}"
                if latitude is not None and longitude is not None
                else "https://www.google.com/maps"
            )

            # Fire every channel for every contact concurrently. Sequentially,
            # one slow/unreachable provider (seen in practice: Twilio call +
            # SMS + WhatsApp + SMTP each taking real wall-clock time back to
            # back) stacks up to a minute-plus before anyone is notified —
            # unacceptable for an emergency alert. A thread pool collapses
            # total latency to roughly the single slowest channel.
            totals = {'email': 0, 'sms': 0, 'call': 0, 'whatsapp': 0}
            attempted = {'email': 0, 'sms': 0, 'call': 0, 'whatsapp': 0}
            per_contact_map = {c.id: {'name': c.name, 'email': None, 'sms': None, 'call': None, 'whatsapp': None} for c in contacts}

            jobs = []  # (contact_id, channel, callable)
            for contact in contacts:
                if contact.email:
                    attempted['email'] += 1
                    jobs.append((contact.id, 'email', lambda c=contact: send_email_alert(c.email, user.username, map_url, location_address)))
                if contact.phone_number:
                    attempted['sms'] += 1
                    jobs.append((contact.id, 'sms', lambda c=contact: send_sms_alert(c.phone_number, user.username, map_url, location_address)))
                    attempted['call'] += 1
                    jobs.append((contact.id, 'call', lambda c=contact: make_voice_call(c.phone_number, user.username, location_address)))
                    attempted['whatsapp'] += 1
                    jobs.append((contact.id, 'whatsapp', lambda c=contact: send_whatsapp_alert(c.phone_number, user.username, map_url, location_address)))

            if jobs:
                with ThreadPoolExecutor(max_workers=min(16, len(jobs))) as pool:
                    futures = {pool.submit(fn): (contact_id, channel) for contact_id, channel, fn in jobs}
                    for future in futures:
                        contact_id, channel = futures[future]
                        try:
                            ok = future.result()
                        except Exception as e:
                            print(f"❌ {channel} dispatch error for contact {contact_id}: {e}")
                            ok = False
                        per_contact_map[contact_id][channel] = ok
                        if ok:
                            totals[channel] += 1

            per_contact = list(per_contact_map.values())

            any_sent = any(totals.values())
            alert.dispatch_status = 'sent' if (any_sent or not contacts) else 'failed'
            alert.results_json = json.dumps({'attempted': attempted, 'sent': totals, 'contacts': per_contact})
            db.session.commit()

            print(
                "📊 Alerts attempted: "
                f"{attempted['email']} emails, {attempted['sms']} SMS, {attempted['call']} calls, {attempted['whatsapp']} WhatsApp | "
                "sent: "
                f"{totals['email']} emails, {totals['sms']} SMS, {totals['call']} calls, {totals['whatsapp']} WhatsApp"
            )

    timer = threading.Timer(grace_seconds, _run)
    timer.daemon = True
    timer.start()
    return timer


# Tracks in-flight grace-window timers so an "I'm safe" cancel can stop dispatch
# before any contact is actually notified. In-process only (fine for a single
# dev/Flask-debug process; swap for a durable queue before multi-worker prod use).
_pending_sos_timers = {}
_pending_sos_timers_lock = threading.Lock()


# ==================== HELPER FUNCTIONS ====================

def calculate_safety_score(latitude, longitude, time_of_day=None):
    """
    Calculate AI-based safety score for a location
    
    PRODUCTION DATA SOURCES TO INTEGRATE:
    1. NCRB (National Crime Records Bureau) API - Crime data
    2. Google Places API - Crowd density, business hours
    3. OpenWeatherMap API - Weather conditions
    4. Satellite/Street View API - Lighting conditions
    5. Local Police Database - Recent incidents
    6. Community Reports - User-submitted safety data
    
    For now using enhanced mock with realistic patterns
    """
    if time_of_day is None:
        time_of_day = datetime.now()

    breakdown = {
        'base_score': 70,
        'time_factor': {'value': 0, 'source': 'real', 'detail': None},
        'crime_factor': {'value': 0, 'source': 'unavailable', 'detail': None},
        'community_factor': {'value': 0, 'source': 'unavailable', 'detail': None},
        'unmodeled_variation': {'value': 0, 'source': 'simulated', 'detail': None},
    }

    # Base score starts at 70
    score = 70

    # === TIME FACTOR (REAL DATA) ===
    hour = time_of_day.hour
    if 22 <= hour or hour <= 5:
        time_adj, time_detail = -25, 'Night (10 PM – 5 AM)'
    elif 18 <= hour < 22:
        time_adj, time_detail = -12, 'Evening (6 PM – 10 PM)'
    elif 6 <= hour < 9:
        time_adj, time_detail = 8, 'Morning rush (6 AM – 9 AM)'
    elif 9 <= hour < 18:
        time_adj, time_detail = 15, 'Daytime (9 AM – 6 PM)'
    else:
        time_adj, time_detail = 0, None
    score += time_adj
    breakdown['time_factor'] = {'value': time_adj, 'source': 'real', 'detail': time_detail}

    # === LOCATION FACTOR (Using real coordinates) ===
    # NCRB crime factor (state-level index from official NCRB dataset, if configured)
    crime_index = get_ncrb_crime_index(latitude, longitude)
    if crime_index is not None:
        # 0.0 (lower risk) → no change, 1.0 (higher risk) → -22 points
        crime_adj = -(crime_index * 22)
        score += crime_adj
        breakdown['crime_factor'] = {
            'value': round(crime_adj, 2), 'source': 'ncrb_dataset',
            'detail': f'State-level NCRB crime index: {round(crime_index, 2)}'
        }
    else:
        breakdown['crime_factor'] = {
            'value': 0, 'source': 'not_configured',
            'detail': 'No NCRB dataset configured (NCRB_DATA_FILE) — this factor is not applied, not estimated.'
        }

    # === COMMUNITY DATA (REAL from your database) ===
    # Get community reports for this area
    from sqlalchemy import func
    nearby_reports = CommunityReport.query.filter(
        func.abs(CommunityReport.latitude - latitude) < 0.01,
        func.abs(CommunityReport.longitude - longitude) < 0.01
    ).all()

    if nearby_reports:
        # Calculate average safety rating from community
        avg_rating = sum(r.safety_rating for r in nearby_reports if r.safety_rating) / len(nearby_reports)
        community_factor = (avg_rating - 3) * 5  # Convert 1-5 rating to score adjustment
        score += community_factor
        breakdown['community_factor'] = {
            'value': round(community_factor, 2), 'source': 'real',
            'detail': f'{len(nearby_reports)} nearby community report(s), avg rating {round(avg_rating, 1)}/5'
        }
    else:
        breakdown['community_factor'] = {
            'value': 0, 'source': 'no_data',
            'detail': 'No community reports near this location yet.'
        }

    # Add realistic variation based on location
    variation = random.randint(-10, 10)
    score += variation
    breakdown['unmodeled_variation'] = {
        'value': variation, 'source': 'simulated',
        'detail': 'Placeholder noise standing in for factors not yet integrated (lighting infra, foot-traffic data, etc). Not derived from real data.'
    }

    # Ensure score is within bounds
    score = max(0, min(100, score))

    return round(score, 2), breakdown


def get_lighting_score(latitude, longitude):
    """
    Get lighting score using OpenWeatherMap API for real weather/sunlight data
    """
    try:
        if OPENWEATHER_API_KEY:
            # Get current weather and sun data
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHER_API_KEY}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Get sunrise/sunset times
                sunrise = datetime.fromtimestamp(data['sys']['sunrise'])
                sunset = datetime.fromtimestamp(data['sys']['sunset'])
                current_time = datetime.now()
                
                # Calculate lighting based on sun position
                if sunrise <= current_time <= sunset:
                    # Daytime
                    # Check cloud coverage
                    clouds = data.get('clouds', {}).get('all', 0)  # 0-100%
                    base_score = 95 - (clouds * 0.2)  # Clouds reduce lighting
                    
                    # Check weather conditions
                    weather = data.get('weather', [{}])[0].get('main', '')
                    if weather in ['Rain', 'Thunderstorm']:
                        base_score -= 15
                    elif weather in ['Drizzle', 'Snow']:
                        base_score -= 10
                    elif weather == 'Fog':
                        base_score -= 20
                    
                    return max(60, min(95, round(base_score, 2)))
                else:
                    # Nighttime - use mock data for street lighting
                    # TODO: Integrate with municipal street lighting database
                    base_score = random.uniform(40, 70)
                    return round(base_score, 2)
    except Exception as e:
        print(f"Error fetching lighting data: {e}")
    
    # Fallback to time-based estimation
    hour = datetime.now().hour
    if 6 <= hour < 18:
        base_score = random.uniform(80, 95)
    elif 18 <= hour < 20:
        base_score = random.uniform(60, 75)
    else:
        base_score = random.uniform(40, 70)
    
    return round(base_score, 2)


def get_crowd_density(latitude, longitude):
    """
    Get crowd density using Google Places API (Popular Times)
    """
    try:
        if GOOGLE_MAPS_API_KEY:
            # Find nearby places
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                'location': f"{latitude},{longitude}",
                'radius': 500,  # 500 meter radius
                'key': GOOGLE_MAPS_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Count open/busy places
                    total_places = len(results)
                    open_places = sum(1 for place in results 
                                     if place.get('opening_hours', {}).get('open_now', False))
                    
                    # More open places = higher crowd density
                    crowd_percentage = (open_places / total_places) * 100 if total_places > 0 else 50
                    
                    # Adjust based on time of day
                    hour = datetime.now().hour
                    if 8 <= hour < 10 or 17 <= hour < 20:
                        crowd_percentage *= 1.3  # Rush hours
                    elif hour >= 23 or hour < 6:
                        crowd_percentage *= 0.4  # Late night
                    
                    # Convert to density levels
                    crowd_percentage = min(100, crowd_percentage)
                    if crowd_percentage >= 70:
                        return 'high'
                    elif crowd_percentage >= 40:
                        return 'medium'
                    else:
                        return 'low'
    except Exception as e:
        print(f"Error fetching crowd density: {e}")
    
    # Fallback to time-based estimation
    hour = datetime.now().hour
    if 9 <= hour < 11 or 17 <= hour < 20:
        densities = ['high', 'medium']
        weights = [0.7, 0.3]
    elif 12 <= hour < 14:
        densities = ['medium', 'high', 'low']
        weights = [0.5, 0.3, 0.2]
    elif 22 <= hour or hour <= 6:
        densities = ['low', 'medium']
        weights = [0.8, 0.2]
    else:
        densities = ['low', 'medium', 'high']
        weights = [0.4, 0.4, 0.2]
    
    return random.choices(densities, weights=weights)[0]


def get_crime_rate(latitude, longitude):
    """
    Get crime rate based on NCRB data simulation
    
    PRODUCTION: Integrate with:
    - NCRB Database API (https://ncrb.gov.in)
    - State Police Databases
    - Recent incident reports (last 6 months)
    - Crime type classification
    
    Real NCRB Integration Steps:
    1. Get NCRB API access from Ministry of Home Affairs
    2. Query crime incidents by coordinates + radius
    3. Categorize by severity (harassment, assault, theft, etc.)
    4. Weight by recency (recent = higher weight)
    5. Calculate crime density per square km
    """
    
    # TODO: Replace with actual NCRB API call
    # Example:
    # ncrb_data = requests.get(
    #     'https://ncrb.gov.in/api/v1/crimes',
    #     params={
    #         'latitude': latitude,
    #         'longitude': longitude,
    #         'radius': 5,  # 5 km radius
    #         'months': 6,   # Last 6 months
    #         'type': 'women_safety'
    #     },
    #     headers={'Authorization': 'Bearer YOUR_API_KEY'}
    # )
    
    # If NCRB dataset is configured, use it to derive a relative crime band.
    crime_index = get_ncrb_crime_index(latitude, longitude)
    if crime_index is not None:
        if crime_index < 0.33:
            return 'low'
        if crime_index < 0.66:
            return 'medium'
        return 'high'

    # Fallback: simulation (when NCRB not configured)
    rates = ['low', 'medium', 'high']
    weights = [0.70, 0.25, 0.05]
    return random.choices(rates, weights=weights)[0]


@lru_cache(maxsize=1)
def _load_ncrb_state_index():
    """
    Loads a state-level NCRB-derived crime index CSV into memory.

    Expected CSV columns:
      - state
      - index  (float 0..1, higher => higher relative risk)

    Provide the file path via NCRB_DATA_FILE env var.
    Download official NCRB datasets via `https://ncrb.gov.in` / `https://data.gov.in`
    and preprocess into this simple index format.
    """
    if not NCRB_DATA_FILE:
        return None

    path = NCRB_DATA_FILE
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)

    if not os.path.exists(path):
        print(f"❌ NCRB data file not found: {path}")
        return None

    try:
        mapping = {}
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = (row.get('state') or '').strip().lower()
                idx = row.get('index')
                if not state or idx is None:
                    continue
                try:
                    val = float(idx)
                except Exception:
                    continue
                mapping[state] = max(0.0, min(1.0, val))
        if not mapping:
            print("❌ NCRB data file loaded but no valid rows found.")
            return None
        print(f"✅ NCRB state index loaded: {len(mapping)} states")
        return mapping
    except Exception as e:
        print(f"❌ Failed to load NCRB data: {e}")
        return None


@lru_cache(maxsize=512)
def _reverse_geocode_state(latitude_rounded, longitude_rounded):
    """Reverse geocode via Nominatim to extract Indian state name (cached)."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "json", "lat": latitude_rounded, "lon": longitude_rounded, "zoom": 10, "addressdetails": 1},
            headers={"User-Agent": "SaheliSafetyApp/1.0 (contact: local)"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        addr = data.get("address") or {}
        state = (addr.get("state") or "").strip()
        return state or None
    except Exception:
        return None


def get_ncrb_crime_index(latitude, longitude):
    """
    Returns a normalized 0..1 crime index for the user's state based on NCRB datasets,
    if NCRB_DATA_FILE is configured. Otherwise returns None.
    """
    mapping = _load_ncrb_state_index()
    if not mapping or latitude is None or longitude is None:
        return None

    # Cache key control (avoid huge cache from raw floats)
    lat_r = round(float(latitude), 2)
    lon_r = round(float(longitude), 2)
    state = _reverse_geocode_state(lat_r, lon_r)
    if not state:
        return None

    # Normalize key matching
    key = state.strip().lower()
    return mapping.get(key)


@app.route('/notify-call', methods=['POST'])
def notify_call():
    """Send an email notification to the contact being called (if configured)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    contact_phone = (request.form.get('phone_number') or '').strip()
    if not contact_phone:
        return jsonify({'success': False, 'message': 'Phone number required'}), 400

    user = db.session.get(User, session['user_id'])
    contact = TrustedContact.query.filter_by(user_id=user.id, phone_number=contact_phone).first()
    if not contact:
        return jsonify({'success': False, 'message': 'Contact not found'}), 404

    if not contact.email:
        return jsonify({'success': False, 'message': 'This contact has no email saved.'}), 400

    if not (SMTP_USERNAME and SMTP_PASSWORD and '@' in SMTP_USERNAME):
        return jsonify({'success': False, 'message': 'Email is not configured. Go to Settings to add SMTP details.'}), 400

    # Don't block the UX for call initiation; send in background
    def _send():
        ok = send_call_notification_email(contact.email, user.username)
        if not ok:
            print("❌ Call notification email failed (SMTP/Brevo).")

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()

    return jsonify({'success': True})


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone_number = request.form.get('phone_number', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        
        # Validation
        if not username or not email or not password:
            flash('All required fields must be filled', 'error')
            return render_template('signup.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return render_template('signup.html')
        
        if not validate_email(email):
            flash('Invalid email format', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('signup.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            phone_number=phone_number,
            emergency_contact=emergency_contact
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        
        if not username_or_email or not password:
            flash('Please enter both username/email and password', 'error')
            return render_template('login.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))


# ==================== DASHBOARD & MAIN FEATURES ====================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    trusted_count = TrustedContact.query.filter_by(user_id=user.id).count()
    active_alerts = SOSAlert.query.filter_by(user_id=user.id, is_active=True).count()
    
    return render_template('dashboard.html', user=user, trusted_count=trusted_count, active_alerts=active_alerts)


# ==================== TRUSTED CIRCLE ROUTES ====================

@app.route('/trusted-circle')
def trusted_circle():
    if 'user_id' not in session:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    contacts = TrustedContact.query.filter_by(user_id=user.id).order_by(TrustedContact.is_primary.desc()).all()
    
    return render_template('trusted_circle.html', user=user, contacts=contacts)


@app.route('/add-trusted-contact', methods=['POST'])
def add_trusted_contact():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    relationship = request.form.get('relationship', '').strip()
    is_primary = request.form.get('is_primary') == 'on'
    
    if not name or not phone:
        flash('Name and phone number are required', 'error')
        return redirect(url_for('trusted_circle'))
    
    # If setting as primary, unset other primary contacts
    if is_primary:
        TrustedContact.query.filter_by(user_id=session['user_id'], is_primary=True).update({'is_primary': False})
    
    new_contact = TrustedContact(
        user_id=session['user_id'],
        name=name,
        phone_number=phone,
        email=email,
        relationship=relationship,
        is_primary=is_primary
    )
    
    try:
        db.session.add(new_contact)
        db.session.commit()
        flash(f'{name} added to your trusted circle! 💕', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding contact', 'error')
    
    return redirect(url_for('trusted_circle'))


@app.route('/delete-trusted-contact/<int:contact_id>', methods=['POST'])
def delete_trusted_contact(contact_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    contact = TrustedContact.query.filter_by(id=contact_id, user_id=session['user_id']).first()
    if contact:
        db.session.delete(contact)
        db.session.commit()
        flash('Contact removed from trusted circle', 'success')
    else:
        flash('Contact not found', 'error')
    
    return redirect(url_for('trusted_circle'))


# ==================== SOS ALERT ROUTES ====================

@app.route('/sos')
def sos_page():
    if 'user_id' not in session:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    recent_alerts = SOSAlert.query.filter_by(user_id=user.id).order_by(desc(SOSAlert.triggered_at)).limit(10).all()
    
    return render_template('sos.html', user=user, recent_alerts=recent_alerts)


SOS_GRACE_SECONDS = int(os.environ.get('SOS_GRACE_SECONDS', 10))


@app.route('/trigger-sos', methods=['POST'])
def trigger_sos():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    alert_type = request.form.get('alert_type', 'manual')
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    location_address = request.form.get('location_address', '')
    location_attached = latitude is not None and longitude is not None

    user = db.session.get(User, session['user_id'])
    contacts = TrustedContact.query.filter_by(user_id=user.id).all()

    # Create SOS Alert in a 'pending' state: nothing has been sent yet.
    sos_alert = SOSAlert(
        user_id=session['user_id'],
        alert_type=alert_type,
        latitude=latitude,
        longitude=longitude,
        location_address=location_address or 'Location not specified',
        dispatch_status='pending',
        contacts_total=len(contacts),
        location_attached=location_attached,
    )

    try:
        db.session.add(sos_alert)
        db.session.commit()

        if len(contacts) == 0:
            # Nothing to dispatch; close it out immediately and be explicit about why.
            sos_alert.dispatch_status = 'failed'
            sos_alert.results_json = json.dumps({'reason': 'no_trusted_contacts'})
            db.session.commit()
            flash('⚠️ No trusted contacts added! Please add contacts first.', 'warning')
            return jsonify({
                'success': True,
                'alert_id': sos_alert.id,
                'dispatch_status': 'failed',
                'grace_seconds': 0,
                'contacts_total': 0,
                'location_attached': location_attached,
                'message': 'SOS Alert created but you have no trusted contacts to notify.'
            })

        # Start the grace-window timer. Contacts are only actually notified
        # once it elapses — the user can cancel ("I'm safe") before then.
        timer = dispatch_sos_alert(sos_alert.id, grace_seconds=SOS_GRACE_SECONDS)
        with _pending_sos_timers_lock:
            _pending_sos_timers[sos_alert.id] = timer

        return jsonify({
            'success': True,
            'alert_id': sos_alert.id,
            'dispatch_status': 'pending',
            'grace_seconds': SOS_GRACE_SECONDS,
            'contacts_total': len(contacts),
            'location_attached': location_attached,
            'message': f'SOS armed. Notifying {len(contacts)} trusted contact(s) in {SOS_GRACE_SECONDS}s unless cancelled.'
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ trigger_sos error: {e}")
        return jsonify({'success': False, 'message': 'Error triggering SOS'}), 500


@app.route('/cancel-sos/<int:alert_id>', methods=['POST'])
def cancel_sos(alert_id):
    """'I'm safe' — cancel an SOS alert during its grace window, before any
    trusted contact has actually been notified."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    alert = SOSAlert.query.filter_by(id=alert_id, user_id=session['user_id']).first()
    if not alert:
        return jsonify({'success': False, 'message': 'Alert not found'}), 404

    if alert.dispatch_status != 'pending':
        return jsonify({
            'success': False,
            'message': 'Too late to cancel — alerts have already started sending.',
            'dispatch_status': alert.dispatch_status
        }), 409

    with _pending_sos_timers_lock:
        timer = _pending_sos_timers.pop(alert_id, None)
    if timer:
        timer.cancel()

    alert.dispatch_status = 'cancelled'
    alert.is_active = False
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'message': "Marked safe. No contacts were notified.", 'dispatch_status': 'cancelled'})


def reconcile_sos_alert_if_overdue(alert):
    """Safety net for the grace-window timer: if the Flask process restarted or
    crashed between arming an SOS and the timer firing (the in-memory
    `_pending_sos_timers` dict does not survive a restart), a 'pending' alert
    would otherwise sit un-dispatched forever with trusted contacts never
    notified — silent failure is the worst outcome for a safety feature.
    Called on every status poll, so the client's own polling loop closes this
    gap within seconds even with no timer at all.
    """
    if alert.dispatch_status != 'pending':
        return
    elapsed = (datetime.utcnow() - alert.triggered_at).total_seconds()
    if elapsed < SOS_GRACE_SECONDS:
        return  # still within the legitimate cancel window

    with _pending_sos_timers_lock:
        timer = _pending_sos_timers.pop(alert.id, None)
    if timer:
        timer.cancel()
    # dispatch_sos_alert's own guard (status must still be 'pending') makes this
    # safe even if the original timer fires concurrently — only one path wins.
    dispatch_sos_alert(alert.id, grace_seconds=0)


@app.route('/sos-status/<int:alert_id>')
def sos_status(alert_id):
    """Poll for real dispatch status: whether alerts were actually attempted/sent,
    per-channel, per-contact — not just 'SOS sent'."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    alert = SOSAlert.query.filter_by(id=alert_id, user_id=session['user_id']).first()
    if not alert:
        return jsonify({'success': False, 'message': 'Alert not found'}), 404

    reconcile_sos_alert_if_overdue(alert)

    results = json.loads(alert.results_json) if alert.results_json else None
    return jsonify({
        'success': True,
        'alert_id': alert.id,
        'dispatch_status': alert.dispatch_status,
        'contacts_total': alert.contacts_total,
        'location_attached': alert.location_attached,
        'results': results,
    })


@app.route('/resolve-sos/<int:alert_id>', methods=['POST'])
def resolve_sos(alert_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    alert = SOSAlert.query.filter_by(id=alert_id, user_id=session['user_id']).first()
    if alert:
        alert.is_active = False
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.session.commit()
        flash('SOS Alert marked as resolved', 'success')
    
    return redirect(url_for('sos_page'))


@app.route('/fake-call')
def fake_call():
    """Show fake incoming call screen for emergency escape"""
    if 'user_id' not in session:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('login'))
    
    # Get caller info from query params or use realistic defaults
    caller_name = request.args.get('name', 'Mom')
    
    # Generate realistic Indian phone number format if not provided
    import random
    default_number = f'+91 {random.choice(["98", "99", "97", "96", "95"])}{random.randint(100, 999)} {random.randint(10000, 99999)}'
    caller_number = request.args.get('number', default_number)
    
    return render_template('fake_call.html', caller_name=caller_name, caller_number=caller_number)


# ==================== SAFETY SCORE & ZONES ====================

@app.route('/safety-score')
def safety_score_page():
    if 'user_id' not in session:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    
    # Get recent safety zones
    safety_zones = SafetyZone.query.order_by(desc(SafetyZone.last_updated)).limit(20).all()
    
    # Pass API keys to template
    ipgeo_api_key = IPGEOLOCATION_API_KEY if IPGEOLOCATION_API_KEY else ''
    google_maps_key = GOOGLE_MAPS_API_KEY if GOOGLE_MAPS_API_KEY else ''
    
    return render_template('safety_score.html', user=user, safety_zones=safety_zones, 
                         IPGEOLOCATION_API_KEY=ipgeo_api_key,
                         GOOGLE_MAPS_API_KEY=google_maps_key)


@app.route('/check-safety', methods=['POST'])
def check_safety():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    area_name = request.form.get('area_name', 'Unknown Area')
    
    if not latitude or not longitude:
        return jsonify({'success': False, 'message': 'Location required'}), 400
    
    # Calculate safety metrics
    safety_score, score_breakdown = calculate_safety_score(latitude, longitude, datetime.now())
    lighting_score = get_lighting_score(latitude, longitude)
    crowd_density = get_crowd_density(latitude, longitude)
    crime_rate = get_crime_rate(latitude, longitude)
    
    # Check if zone exists, update or create
    zone = SafetyZone.query.filter_by(area_name=area_name).first()
    
    if zone:
        zone.safety_score = safety_score
        zone.lighting_score = lighting_score
        zone.crowd_density = crowd_density
        zone.crime_rate = crime_rate
        zone.last_updated = datetime.utcnow()
    else:
        zone = SafetyZone(
            area_name=area_name,
            latitude=latitude,
            longitude=longitude,
            safety_score=safety_score,
            lighting_score=lighting_score,
            crowd_density=crowd_density,
            crime_rate=crime_rate
        )
        db.session.add(zone)
    
    db.session.commit()
    
    # Determine safety level
    if safety_score >= 75:
        safety_level = 'safe'
        safety_message = 'This area is generally safe! 💚'
    elif safety_score >= 50:
        safety_level = 'moderate'
        safety_message = 'Exercise caution in this area. 💛'
    else:
        safety_level = 'unsafe'
        safety_message = 'This area may be unsafe. Consider alternative route. 💖'
    
    return jsonify({
        'success': True,
        'safety_score': safety_score,
        'lighting_score': lighting_score,
        'crowd_density': crowd_density,
        'crime_rate': crime_rate,
        'safety_level': safety_level,
        'message': safety_message,
        'score_breakdown': score_breakdown,
        'ncrb_configured': bool(NCRB_DATA_FILE),
    })


# ==================== COMMUNITY REPORTS ====================

@app.route('/community')
def community_page():
    if 'user_id' not in session:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    reports = CommunityReport.query.order_by(desc(CommunityReport.reported_at)).limit(50).all()
    
    return render_template('community.html', user=user, reports=reports)


@app.route('/submit-report', methods=['POST'])
def submit_report():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    area_name = request.form.get('area_name', '').strip()
    report_type = request.form.get('report_type', '')
    description = request.form.get('description', '').strip()
    safety_rating = request.form.get('safety_rating', type=int)
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    
    if not area_name or not report_type:
        flash('Area name and report type are required', 'error')
        return redirect(url_for('community_page'))
    
    report = CommunityReport(
        user_id=session['user_id'],
        area_name=area_name,
        latitude=latitude,
        longitude=longitude,
        report_type=report_type,
        description=description,
        safety_rating=safety_rating
    )
    
    try:
        db.session.add(report)
        db.session.commit()
        flash('Thank you for contributing to community safety! 💕', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error submitting report', 'error')
    
    return redirect(url_for('community_page'))


@app.route('/mark-helpful/<int:report_id>', methods=['POST'])
def mark_helpful(report_id):
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    report = CommunityReport.query.get(report_id)
    if report:
        report.helpful_count += 1
        db.session.commit()
        return jsonify({'success': True, 'count': report.helpful_count})
    
    return jsonify({'success': False}), 404


# ==================== SAFETY BEACONS ====================

@app.route('/safety-beacons')
def safety_beacons_page():
    if 'user_id' not in session:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    beacons = SafetyBeacon.query.filter_by(is_active=True).all()
    
    return render_template('safety_beacons.html', user=user, beacons=beacons)


# ==================== PROFILE & SETTINGS ====================

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/settings')
def settings():
    if 'user_id' not in session:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    contact_count = TrustedContact.query.filter_by(user_id=user.id).count()
    
    # Check if email/SMS is configured
    smtp_configured = bool(SMTP_USERNAME and SMTP_PASSWORD and '@' in SMTP_USERNAME)
    brevo_configured = bool(BREVO_API_KEY and BREVO_SENDER_EMAIL and '@' in BREVO_SENDER_EMAIL)
    email_configured = smtp_configured or brevo_configured
    sms_configured = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER)
    whatsapp_configured = bool(BREVO_API_KEY and BREVO_WHATSAPP_SENDER_NUMBER and BREVO_WHATSAPP_TEMPLATE_ID)

    return render_template('settings.html',
                          user=user,
                          email_configured=email_configured,
                          smtp_configured=smtp_configured,
                          brevo_configured=brevo_configured,
                          sms_configured=sms_configured,
                          whatsapp_configured=whatsapp_configured,
                          contact_count=contact_count,
                          current_email=SMTP_USERNAME if email_configured else '',
                          current_brevo_sender=BREVO_SENDER_EMAIL if brevo_configured else '',
                          current_brevo_sender_name=BREVO_SENDER_NAME if brevo_configured else 'Saheli',
                          current_twilio_sid=TWILIO_ACCOUNT_SID[:10] + '...' if TWILIO_ACCOUNT_SID else '',
                          current_twilio_phone=TWILIO_PHONE_NUMBER if TWILIO_PHONE_NUMBER else '',
                          current_whatsapp_sender=BREVO_WHATSAPP_SENDER_NUMBER,
                          current_whatsapp_template_id=BREVO_WHATSAPP_TEMPLATE_ID)


@app.route('/settings/test-email', methods=['POST'])
def test_email_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.json
    username = data.get('smtp_username', '').strip()
    password = data.get('smtp_password', '').strip()
    test_email = data.get('test_email', username).strip()
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'})
    
    # Test the email
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "🚨 Test Email from Saheli App"
        msg['From'] = username
        msg['To'] = test_email
        
        body = """
        ✅ SUCCESS! Your email configuration is working!
        
        This is a test email from Saheli Women Safety App.
        
        Your SOS alerts will now be sent to your trusted contacts via email.
        
        Next steps:
        1. Save this configuration
        2. Add trusted contacts with their email addresses
        3. Test the SOS alert system
        
        Stay safe! 💖
        - Saheli Safety Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Temporarily use provided credentials for a real send test.
        # Use SSL fallback if STARTTLS is blocked by the network.
        global SMTP_USERNAME, SMTP_PASSWORD
        old_user, old_pass = SMTP_USERNAME, SMTP_PASSWORD
        SMTP_USERNAME, SMTP_PASSWORD = username, password
        ok, err = smtp_send_message(msg)
        SMTP_USERNAME, SMTP_PASSWORD = old_user, old_pass

        if not ok:
            return jsonify({
                'success': False,
                'message': f'❌ Email send failed: {err}\n\nIf SMTP ports are blocked, use Brevo Email API (HTTPS). Add BREVO_API_KEY and BREVO_SENDER_EMAIL in .env.'
            })
        
        return jsonify({
            'success': True,
            'message': f'✅ Test email sent successfully to {test_email}! Check your inbox (and spam folder).'
        })
    except smtplib.SMTPAuthenticationError:
        return jsonify({
            'success': False,
            'message': '❌ Authentication failed! Please check:\n1. Email address is correct\n2. Using App Password (not regular password)\n3. 2-Step Verification is enabled'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ Error: {str(e)}'
        })


@app.route('/settings/test-brevo', methods=['POST'])
def test_brevo_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    data = request.json or {}
    api_key = (data.get('brevo_api_key') or '').strip()
    sender_email = (data.get('brevo_sender_email') or '').strip()
    sender_name = (data.get('brevo_sender_name') or 'Saheli').strip()
    test_email = (data.get('test_email') or sender_email).strip()

    if not api_key or not sender_email:
        return jsonify({'success': False, 'message': 'API key and sender email are required'}), 400
    if '@' not in sender_email or '@' not in test_email:
        return jsonify({'success': False, 'message': 'Please enter valid email addresses'}), 400

    payload = {
        "sender": {"email": sender_email, "name": sender_name},
        "to": [{"email": test_email}],
        "subject": "Test Email from Saheli (Brevo)",
        "textContent": "✅ SUCCESS! Brevo email configuration is working.\n\nYour SOS alerts can now be sent via Brevo (HTTPS).",
        "htmlContent": "<p><strong>✅ SUCCESS!</strong> Brevo email configuration is working.</p><p>Your SOS alerts can now be sent via Brevo (HTTPS).</p>",
    }

    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"},
            data=json.dumps(payload),
            timeout=20,
        )
        if 200 <= resp.status_code < 300:
            return jsonify({'success': True, 'message': f'✅ Test email sent successfully to {test_email}!'})
        return jsonify({'success': False, 'message': f'❌ Brevo error: HTTP {resp.status_code} {resp.text}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Brevo request failed: {str(e)}'}), 500


@app.route('/settings/save-brevo', methods=['POST'])
def save_brevo_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    data = request.json or {}
    api_key = (data.get('brevo_api_key') or '').strip()
    sender_email = (data.get('brevo_sender_email') or '').strip()
    sender_name = (data.get('brevo_sender_name') or 'Saheli').strip()

    if not api_key or not sender_email:
        return jsonify({'success': False, 'message': 'API key and sender email are required'}), 400

    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []

        def upsert(key, value):
            nonlocal lines
            found = False
            for i, line in enumerate(lines):
                if line.startswith(key + '='):
                    lines[i] = f'{key}={value}\n'
                    found = True
                    break
            if not found:
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] = lines[-1] + '\n'
                lines.append(f'{key}={value}\n')

        upsert('BREVO_API_KEY', api_key)
        upsert('BREVO_SENDER_EMAIL', sender_email)
        upsert('BREVO_SENDER_NAME', sender_name)

        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return jsonify({'success': True, 'message': 'Brevo configuration saved! Please restart the app.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving configuration: {str(e)}'}), 500


@app.route('/settings/test-whatsapp', methods=['POST'])
def test_whatsapp_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    data = request.json or {}
    api_key = (data.get('brevo_api_key') or BREVO_API_KEY or '').strip()
    sender_number = (data.get('whatsapp_sender_number') or '').strip()
    template_id = (data.get('whatsapp_template_id') or '').strip()
    test_number = (data.get('test_number') or '').strip()

    if not api_key or not sender_number or not template_id or not test_number:
        return jsonify({'success': False, 'message': 'Sender number, template ID, and a test recipient number are all required'}), 400

    payload = {
        "senderNumber": _normalize_whatsapp_number(sender_number),
        "contactNumbers": [_normalize_whatsapp_number(test_number)],
        "templateId": int(template_id),
    }

    try:
        resp = requests.post(
            "https://api.brevo.com/v3/whatsapp/sendMessage",
            headers={"api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"},
            data=json.dumps(payload),
            timeout=20,
        )
        if 200 <= resp.status_code < 300:
            return jsonify({'success': True, 'message': f'Test WhatsApp message sent! messageId: {resp.json().get("messageId")}'})
        return jsonify({'success': False, 'message': f'Brevo WhatsApp error: HTTP {resp.status_code} {resp.text}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Brevo WhatsApp request failed: {str(e)}'}), 500


@app.route('/settings/save-whatsapp', methods=['POST'])
def save_whatsapp_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    data = request.json or {}
    sender_number = (data.get('whatsapp_sender_number') or '').strip()
    template_id = (data.get('whatsapp_template_id') or '').strip()

    if not sender_number or not template_id:
        return jsonify({'success': False, 'message': 'Sender number and template ID are required'}), 400

    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []

        def upsert(key, value):
            nonlocal lines
            found = False
            for i, line in enumerate(lines):
                if line.startswith(key + '='):
                    lines[i] = f'{key}={value}\n'
                    found = True
                    break
            if not found:
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] = lines[-1] + '\n'
                lines.append(f'{key}={value}\n')

        upsert('BREVO_WHATSAPP_SENDER_NUMBER', sender_number)
        upsert('BREVO_WHATSAPP_TEMPLATE_ID', template_id)

        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return jsonify({'success': True, 'message': 'WhatsApp configuration saved! Please restart the app.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving configuration: {str(e)}'}), 500


@app.route('/settings/save-email', methods=['POST'])
def save_email_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.json
    username = data.get('smtp_username', '').strip()
    password = data.get('smtp_password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'})
    
    # Update .env file
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        
        # Read current .env
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update or add SMTP settings
        smtp_username_found = False
        smtp_password_found = False
        
        for i, line in enumerate(lines):
            if line.startswith('SMTP_USERNAME='):
                lines[i] = f'SMTP_USERNAME={username}\n'
                smtp_username_found = True
            elif line.startswith('SMTP_PASSWORD='):
                lines[i] = f'SMTP_PASSWORD={password}\n'
                smtp_password_found = True
        
        # Add if not found
        if not smtp_username_found:
            lines.append(f'\nSMTP_USERNAME={username}\n')
        if not smtp_password_found:
            lines.append(f'SMTP_PASSWORD={password}\n')
        
        # Write back to .env
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return jsonify({
            'success': True,
            'message': 'Email configuration saved! Please restart the app.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving configuration: {str(e)}'
        })


@app.route('/settings/save-sms', methods=['POST'])
def save_sms_config():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.json
    sid = data.get('twilio_sid', '').strip()
    token = data.get('twilio_token', '').strip()
    phone = data.get('twilio_phone', '').strip()
    
    # Update .env file
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        
        # Read current .env
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update or add Twilio settings
        sid_found = token_found = phone_found = False
        
        for i, line in enumerate(lines):
            if line.startswith('TWILIO_ACCOUNT_SID='):
                lines[i] = f'TWILIO_ACCOUNT_SID={sid}\n'
                sid_found = True
            elif line.startswith('TWILIO_AUTH_TOKEN='):
                lines[i] = f'TWILIO_AUTH_TOKEN={token}\n'
                token_found = True
            elif line.startswith('TWILIO_PHONE_NUMBER='):
                lines[i] = f'TWILIO_PHONE_NUMBER={phone}\n'
                phone_found = True
        
        # Add if not found
        if not sid_found:
            lines.append(f'\nTWILIO_ACCOUNT_SID={sid}\n')
        if not token_found:
            lines.append(f'TWILIO_AUTH_TOKEN={token}\n')
        if not phone_found:
            lines.append(f'TWILIO_PHONE_NUMBER={phone}\n')
        
        # Write back to .env
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return jsonify({
            'success': True,
            'message': 'SMS configuration saved! Please restart the app.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving configuration: {str(e)}'
        })


@app.route('/profile')
def profile_old():
    if 'user_id' not in session:
        flash('Please login to access this feature', 'error')
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    
    email = request.form.get('email', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    emergency_contact = request.form.get('emergency_contact', '').strip()
    
    if email and validate_email(email):
        user.email = email
    
    user.phone_number = phone_number
    user.emergency_contact = emergency_contact
    
    try:
        db.session.commit()
        flash('Profile updated successfully! 💕', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile', 'error')
    
    return redirect(url_for('profile'))


@app.route('/toggle-adaptive-mode', methods=['POST'])
def toggle_adaptive_mode():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    user = db.session.get(User, session['user_id'])
    user.adaptive_mode_enabled = not user.adaptive_mode_enabled
    db.session.commit()
    
    return jsonify({'success': True, 'enabled': user.adaptive_mode_enabled})


# ==================== INITIALIZE DATABASE ====================

def ensure_sos_alert_columns():
    """Lightweight additive migration: add new SOSAlert columns to an existing
    sqlite DB file without wiping data (no Flask-Migrate configured in this project).

    Sqlite-only: on Postgres (or any fresh database), db.create_all() already
    creates sos_alert with every column the current model defines, so there is
    nothing to patch — and 'PRAGMA table_info' is sqlite-specific syntax that
    would error on another dialect.
    """
    if db.engine.dialect.name != 'sqlite':
        return

    from sqlalchemy import text
    with db.engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(sos_alert)"))}
        additions = {
            'dispatch_status': "ALTER TABLE sos_alert ADD COLUMN dispatch_status VARCHAR(20) DEFAULT 'sent'",
            'contacts_total': "ALTER TABLE sos_alert ADD COLUMN contacts_total INTEGER DEFAULT 0",
            'results_json': "ALTER TABLE sos_alert ADD COLUMN results_json TEXT",
            'location_attached': "ALTER TABLE sos_alert ADD COLUMN location_attached BOOLEAN DEFAULT 0",
        }
        for column, ddl in additions.items():
            if column not in existing:
                conn.execute(text(ddl))
                conn.commit()
                print(f"✅ Migrated sos_alert: added column {column}")


def sweep_orphaned_pending_sos():
    """On startup, dispatch any SOSAlert left 'pending' by a previous process
    that crashed or was killed mid-grace-window. Its in-memory timer died with
    that process, so without this sweep the alert — and the person who
    triggered it — would be stuck waiting on a notification that can now never
    fire on its own. Favor dispatching late over not dispatching at all.
    """
    orphaned = SOSAlert.query.filter_by(dispatch_status='pending').all()
    for alert in orphaned:
        print(f"⚠️ Recovering orphaned pending SOS alert #{alert.id} from a previous process — dispatching now.")
        dispatch_sos_alert(alert.id, grace_seconds=0)


def init_db():
    with app.app_context():
        db.create_all()
        ensure_sos_alert_columns()
        sweep_orphaned_pending_sos()

        # Add some demo safety beacons
        if SafetyBeacon.query.count() == 0:
            demo_beacons = [
                SafetyBeacon(name='Metro Station - Connaught Place', beacon_type='metro', 
                           latitude=28.6304, longitude=77.2177, address='Connaught Place, New Delhi',
                           contact_number='1800-180-6666', is_verified=True),
                SafetyBeacon(name='Police Station - Karol Bagh', beacon_type='police_station',
                           latitude=28.6519, longitude=77.1860, address='Karol Bagh, New Delhi',
                           contact_number='011-25813344', is_verified=True),
                SafetyBeacon(name='24/7 Medical Store - Saket', beacon_type='shop',
                           latitude=28.5244, longitude=77.2066, address='Saket, New Delhi',
                           contact_number='011-26854123', is_verified=True),
                SafetyBeacon(name='Women Help Desk - Nehru Place', beacon_type='police_station',
                           latitude=28.5494, longitude=77.2501, address='Nehru Place, New Delhi',
                           contact_number='1091', is_verified=True),
            ]
            for beacon in demo_beacons:
                db.session.add(beacon)
            
            db.session.commit()
        
        print("✨ Database initialized successfully! 💕")


# Must run at import time, not only under `if __name__ == '__main__'`: a
# production WSGI server (gunicorn app:app, as used on Render) imports this
# module directly and never executes that guard. Without this, the database
# tables are never created on a fresh/ephemeral disk, and every DB-touching
# route (including /login) fails with a 500.
init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
