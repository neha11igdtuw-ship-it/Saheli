# 💖 Saheli - AI-Powered Women Safety App ✨

*"Empowering girls, ensuring safety. Stay safe, stay fabulous!"*

A comprehensive AI-powered women's safety application built with Flask that predicts and prevents unsafe situations before they occur. Saheli combines real-time location data, AI-powered safety scoring, community validation, and emergency features to create a proactive safety ecosystem.

## 🌟 Problem Statement

**Did you know? Every 15 minutes, a woman in India faces harassment in a public space** *(Source: NCRB 2023)*

Existing safety apps like bSafe, Raksha, and MySafetipin are mostly **reactive** - acting after an incident occurs. 

**Key Challenges:**
- 🚫 SOS apps act after emergencies
- ⚠️ No real-time or predictive safety insights
- 🔒 Privacy issues with continuous tracking
- 🚷 Low public awareness about area safety
- 💬 Lack of community-driven safety data

**Our Goal:** To shift women's safety from reaction to prevention — empowering women to move fearlessly, anytime, anywhere.

## 🎯 Solution - Saheli

Saheli is an AI-powered safety companion that helps women **predict and prevent** unsafe situations before they occur. It analyzes real-time location data, lighting conditions, crowd density, and past crime data to generate a **Safety Score** for every area or route.

## ✨ Core Features

### 1. 🤖 AI-Based Predictive Safety Score
- Uses lighting conditions, crowd density, and past crime data (NCRB datasets)
- Real-time safety score (0-100) for any location
- Time-aware predictions (day/night analysis)
- Adaptive learning based on community feedback

### 2. 🚨 Multi-Modal SOS System
- **Manual SOS**: One-tap emergency alert
- **Voice SOS**: Voice-activated emergency trigger
- **Gesture SOS**: Shake-to-activate alert system
- **Offline SOS**: SMS-based alerts for low connectivity
- Automatic location sharing with trusted contacts
- Audio recording during emergencies

### 3. 👯‍♀️ Trusted Circle Management
- Add unlimited trusted contacts (besties, family, etc.)
- Set primary emergency contact
- Instant notifications on SOS trigger
- Live location sharing with trusted circle
- Relationship categorization (Mom, Sister, Best Friend, etc.)

### 4. 💬 Community Validation System
- Report safe/unsafe areas in real-time
- Share incident experiences
- Rate areas with star ratings
- Mark helpful reports
- Verified community-driven safety data
- Combined with official NCRB data

### 5. 🏪 IoT Safety Beacons
- Directory of verified safe spots:
  - 🚇 Metro Stations
  - 🚔 Police Stations
  - 🏥 Hospitals
  - 🏪 24/7 Shops & Safe Places
- Quick help points with contact info
- Google Maps integration for directions
- One-tap calling to beacon locations

### 6. ✨ Adaptive Safety Mode
- Automatically activates tracking in risky zones
- Smart alerts based on user behavior
- Personalized safety recommendations
- Energy-efficient location tracking
- Privacy-first approach

### 7. 📊 Real-Time Safety Analytics
- View recent safety zones
- Historical safety trends
- Lighting and crowd density metrics
- Crime rate indicators
- AI-powered safety suggestions

### 8. 👤 Profile & Settings
- Personal information management
- Emergency contact setup
- Adaptive mode toggle
- Account statistics
- Privacy controls

## 🎨 Girly Theme Design

- **Soft Pink Gradients**: Beautiful pink-to-peach gradient backgrounds
- **Rounded UI Elements**: Pill-shaped buttons and rounded cards
- **Cute Emojis**: 💕, ✨, 🌸, 👯‍♀️, 🎀 throughout the interface
- **Playful Typography**: Friendly, girly font choices
- **Animated Elements**: Smooth transitions and hover effects
- **Feminine Color Palette**: 
  - Primary: Hot Pink (#ff6b9d)
  - Secondary: Light Pink (#ffa7c4)
  - Accent: Rose (#c06c84)
  - Background: Soft peach-to-yellow gradients

## 🛠️ Technology Stack

### Backend
- **Flask** (Python) - Web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Database (easily scalable to PostgreSQL)
- **Werkzeug** - Password hashing & security

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling with gradients & animations
- **JavaScript** - Interactive features
- **Jinja2** - Template engine

### AI & ML (Mock Implementation - Production Ready)
- Mock AI safety score calculation
- Ready for integration with:
  - **TensorFlow Lite** - ML models
  - **Scikit-learn** - Predictive algorithms
  - **NLP APIs** - Voice companion features

### Data Sources (Production)
- **NCRB** (National Crime Records Bureau)
- **Government Open Data Platform**
- **Google Maps API** - Location & routing
- **Real-time APIs** - Crowd density & lighting

### Future Add-ons
- **Blockchain** - Tamper-proof safety logs
- **IoT Wearables** - Instant SOS transmission
- **Voice AI** - Fear detection & auto-trigger

## 📋 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Navigate to the project directory**
   ```bash
   cd C:\SelfProject\saheliproject
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```powershell
     .\venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure API Keys (OPTIONAL - For Production Use)**
   
   To enable **real-time data** (recommended for accuracy):
   
   ```bash
   copy config_template.env .env
   ```
   
   Then edit `.env` file and add your API keys:
   - 🗺️ **Google Maps API**: Get from https://console.cloud.google.com/
   - 🌤️ **OpenWeatherMap API**: Get from https://openweathermap.org/api
   
   📖 **See `API_SETUP_GUIDE.md` for detailed instructions!**
   
   ⚠️ **Note**: App works perfectly without API keys! They just add real-time weather & crowd data.

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   - Open your browser: `http://localhost:5000`

## 🚀 Quick Start

### First Time Setup
1. Run `.\run.bat` (Windows) or `./run.sh` (Linux/Mac)
2. Navigate to `http://localhost:5000`
3. Create your account
4. Add trusted contacts
5. Start checking safety scores!

## 📱 Features Walkthrough

### 1. Create Account
- Username, email, password
- Optional: Phone number & emergency contact
- Secure password requirements

### 2. Add Trusted Circle
- Navigate to **Trusted Circle**
- Add besties with name, phone, relationship
- Set primary contact
- Manage your safety squad

### 3. Check Safety Score
- Navigate to **Safety Score**
- Enter area name or use current location
- Get AI-powered safety analysis:
  - Safety score (0-100)
  - Lighting conditions
  - Crowd density
  - Crime rate
  - Real-time recommendations

### 4. Trigger SOS
- Navigate to **Emergency SOS**
- Choose alert type:
  - Manual (tap button)
  - Voice (voice command)
  - Gesture (shake phone)
  - Offline (SMS-based)
- All trusted contacts notified instantly

### 5. Community Reports
- Navigate to **Community**
- Submit safety reports
- Rate areas (1-5 stars)
- View community feedback
- Mark helpful reports

### 6. Find Safety Beacons
- Navigate to **Safety Beacons**
- View nearby safe spots
- Get directions on Google Maps
- Call directly from app

## 🗃️ Project Structure

```
saheliproject/
│
├── app.py                      # Main Flask application with all routes
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                  # Git ignore file
├── run.bat                     # Windows startup script
├── run.sh                      # Linux/Mac startup script
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template with girly theme
│   ├── login.html             # Login page
│   ├── signup.html            # Signup page
│   ├── dashboard.html         # User dashboard
│   ├── trusted_circle.html    # Trusted contacts management
│   ├── sos.html               # SOS alert page
│   ├── safety_score.html      # AI safety score checker
│   ├── community.html         # Community reports
│   ├── safety_beacons.html    # IoT safety beacons
│   └── profile.html           # User profile & settings
│
└── saheli.db                   # SQLite database (auto-generated)
```

## 💾 Database Models

### User
- Personal information
- Authentication credentials
- Emergency contacts
- Preferences (adaptive mode, language)

### TrustedContact
- Contact details
- Relationship type
- Primary contact flag

### SOSAlert
- Alert type & timestamp
- Location data
- Resolution status
- Notes

### SafetyZone
- Area information
- Safety scores
- Lighting & crowd metrics
- Crime rate data
- Last updated timestamp

### CommunityReport
- User-submitted reports
- Report type (safe/unsafe/incident)
- Ratings & descriptions
- Helpful count
- Verification status

### SafetyBeacon
- Beacon type & location
- Contact information
- Verification status
- Active status

## 🔐 Security Features

- **Password Hashing**: Werkzeug secure hashing
- **Session Management**: Secure session-based auth
- **Input Validation**: Server & client-side validation
- **SQL Injection Protection**: SQLAlchemy ORM
- **CSRF Protection**: Ready for Flask-WTF integration
- **Privacy First**: Location data only on-demand

## 🌐 API Endpoints

### Authentication
- `GET/POST /signup` - User registration
- `GET/POST /login` - User login
- `GET /logout` - User logout

### Dashboard
- `GET /dashboard` - Main dashboard

### Trusted Circle
- `GET /trusted-circle` - View contacts
- `POST /add-trusted-contact` - Add contact
- `POST /delete-trusted-contact/<id>` - Remove contact

### SOS System
- `GET /sos` - SOS page
- `POST /trigger-sos` - Trigger emergency alert
- `POST /resolve-sos/<id>` - Mark alert resolved

### Safety Score
- `GET /safety-score` - Safety score page
- `POST /check-safety` - Check area safety (returns JSON)

### Community
- `GET /community` - Community reports page
- `POST /submit-report` - Submit new report
- `POST /mark-helpful/<id>` - Mark report helpful

### Safety Beacons
- `GET /safety-beacons` - View all beacons

### Profile
- `GET /profile` - User profile
- `POST /update-profile` - Update profile
- `POST /toggle-adaptive-mode` - Toggle adaptive mode

## 📊 Mock AI Features

The app includes mock AI implementations that simulate:

1. **Safety Score Calculation**
   - Time-of-day analysis
   - Lighting simulation
   - Crowd density estimation
   - Crime rate simulation

2. **Adaptive Learning**
   - User behavior tracking
   - Personalized recommendations
   - Risk prediction

*In production, these would use TensorFlow Lite models trained on NCRB data*

## 🔮 Future Enhancements

- [ ] Google Maps API integration for live maps
- [ ] Real TensorFlow/Scikit-learn ML models
- [ ] Voice AI companion (HuggingFace/OpenAI)
- [ ] SMS gateway integration for offline SOS
- [ ] Push notifications
- [ ] Mobile app (Flutter)
- [ ] Multi-language support
- [ ] Blockchain for tamper-proof logs
- [ ] IoT wearable integration
- [ ] Social media sharing
- [ ] Safe route navigation with turn-by-turn directions
- [ ] Two-factor authentication
- [ ] Password recovery
- [ ] Profile picture upload
- [ ] Video recording during emergencies

## 📞 Important Emergency Numbers (India)

- **Police Emergency**: 100
- **Women Helpline**: 1091
- **National Commission for Women**: 7827-170-170
- **Ambulance**: 102
- **Child Helpline**: 1098

## 🤝 Contributing

This is a safety-critical application. When contributing:
1. Test all security features thoroughly
2. Follow secure coding practices
3. Document all new features
4. Ensure backward compatibility
5. Add appropriate error handling

## 📄 License

This project is created for educational and social welfare purposes. Dedicated to women's safety and empowerment.

## 🙏 Acknowledgments

- **NCRB** - Crime data source
- **Government of India Open Data Platform**
- **Flask Community**
- **All the besties** who inspire us to create safer spaces 💕

## ⚠️ Disclaimer

This is a demo application showcasing the concept. For production use:
- Implement actual AI/ML models with real datasets
- Add SMS gateway integration
- Implement proper authentication & authorization
- Add rate limiting & security hardening
- Comply with data protection regulations (GDPR, etc.)
- Conduct security audits
- Add proper error logging & monitoring

## 💕 Remember

**Your safety is our priority, bestie!** In case of emergency, always call local authorities first (100 in India).

---

**Built with 💖 by Code Bloom Team**

*Empowering women, one line of code at a time!* ✨

**#WomenSafety #AI #Prevention #Saheli #StaySafe #GirlPower** 🌸
