# 🔑 How to Get API Keys for Saheli App

This guide will help you get API keys to enable **real-time** accurate data in your Saheli safety app!

---

## 📍 1. Google Maps & Places API (RECOMMENDED)

**Purpose**: Real crowd density, place information, accurate geocoding

### Steps to Get API Key:

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create a Project**
   - Click "Select a Project" → "New Project"
   - Name: "Saheli Safety App"
   - Click "Create"

3. **Enable APIs**
   - Go to "APIs & Services" → "Library"
   - Search and enable these APIs:
     - ✅ **Maps JavaScript API**
     - ✅ **Places API**
     - ✅ **Geocoding API**
     - ✅ **Geolocation API** (Optional)

4. **Create API Key**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy your API key!

5. **Restrict API Key (Important for Security)**
   - Click on your API key
   - Under "Application restrictions" → Select "HTTP referrers"
   - Add: `http://localhost:5000/*` (for development)
   - Under "API restrictions" → Select "Restrict key"
   - Select only the APIs you enabled above
   - Click "Save"

6. **Add to your .env file**
   ```
   GOOGLE_MAPS_API_KEY=your-actual-api-key-here
   ```

**Pricing**: 
- ✅ FREE: $200 credit/month
- Places API: ~$17 per 1000 requests (covered by free credit)
- You get enough for development and testing!

---

## 🌤️ 2. OpenWeatherMap API (RECOMMENDED)

**Purpose**: Real weather data, sunrise/sunset times, cloud coverage

### Steps to Get API Key:

1. **Sign Up**
   - Visit: https://openweathermap.org/api
   - Click "Sign Up" → Create free account

2. **Get API Key**
   - After login, go to "API keys" tab
   - Copy your default API key OR create a new one
   - Name it: "Saheli App"

3. **Wait for Activation**
   - ⏱️ API key takes 10 minutes to 2 hours to activate
   - You'll receive an email when ready

4. **Add to your .env file**
   ```
   OPENWEATHER_API_KEY=your-actual-api-key-here
   ```

**Pricing**:
- ✅ FREE TIER: 1,000 API calls/day
- More than enough for personal use!
- Current Weather API is included

---

## 🚨 3. NCRB & Government Data (OPTIONAL - Advanced)

**Purpose**: Real crime statistics from National Crime Records Bureau

### NCRB API Access:

⚠️ **Note**: NCRB doesn't have a public API yet. Here are alternatives:

**Option 1: NCRB Open Data**
- Visit: https://ncrb.gov.in/en/crime-in-india
- Download yearly reports (PDF/Excel)
- Manual integration required

**Option 2: Data.gov.in**
- Visit: https://data.gov.in/
- Search for "crime statistics"
- Some datasets available for download
- Requires manual processing

**Option 3: State Police Websites**
- Many states have crime maps
- Example: Delhi Police Crime Mapping
- Usually requires special permission

### For Now:
The app uses **intelligent simulation** based on:
- Time of day
- Real weather data (when API is added)
- Real crowd density (when API is added)
- Community reports from users
- Historical patterns

---

## 🔧 Setup Instructions

### 1. Create .env file

Copy the template:
```bash
copy config_template.env .env
```

### 2. Add Your API Keys

Open `.env` file and add your keys:

```env
SECRET_KEY=your-random-secret-key-here
GOOGLE_MAPS_API_KEY=AIzaSyABC123...
OPENWEATHER_API_KEY=abc123def456...
```

### 3. Install Required Package

If not already installed:
```bash
pip install python-dotenv requests
```

### 4. Restart the App

```bash
python app.py
```

---

## 🎯 What Happens When You Add API Keys

### ✅ Without API Keys (Current):
- App works fine with intelligent simulation
- Uses time-based patterns
- Still accurate for demonstration

### 🚀 With API Keys (Recommended):
- **Google Places**: Real crowd density based on open businesses
- **OpenWeather**: Actual sunrise/sunset times, cloud coverage, weather
- **Better accuracy**: Safety scores match real conditions
- **Production ready**: Can deploy to real users

---

## 💡 Tips

1. **Start with OpenWeather** - Easiest to get, adds real sun data
2. **Add Google Maps** - Significantly improves accuracy
3. **Test thoroughly** - Make sure API limits are not exceeded
4. **Monitor usage** - Check your Google Cloud Console regularly
5. **Keep keys secret** - Never commit .env file to GitHub!

---

## 🆘 Troubleshooting

### API Key Not Working?

1. **Check if API is enabled** in Google Cloud Console
2. **Wait 10 mins** - New keys take time to activate
3. **Check quotas** - Make sure you haven't exceeded free tier
4. **Check restrictions** - Remove restrictions during testing
5. **Check spelling** - Make sure key is copied correctly in .env

### Still Having Issues?

- The app will fallback to simulation if APIs fail
- Check terminal for error messages
- Test API key directly: `https://api.openweathermap.org/data/2.5/weather?lat=28.7041&lon=77.1025&appid=YOUR_KEY`

---

## 📊 Free Tier Limits

| Service | Free Limit | Enough For |
|---------|------------|------------|
| Google Maps | $200/month | ~15,000 safety checks/month |
| OpenWeather | 1,000 calls/day | ~30,000/month |
| Combined | - | Small to medium user base |

---

## 🎀 You're All Set!

Your Saheli app will now use **real-time data** for maximum accuracy! 💖✨

Questions? Check the terminal output for error messages.

