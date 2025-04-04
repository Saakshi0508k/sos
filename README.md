# Advanced SOS Emergency Web App

This is an enhanced version of the SOS Emergency Web App with real-time location tracking and continuous voice monitoring. This application automatically detects emergency keywords in multiple languages and can trigger an emergency response without requiring a button press.

## Advanced Features

1. **Real-time Location Tracking**
   - Uses the browser's Geolocation API to track the user's location in real-time
   - Updates location coordinates automatically as the user moves
   - Displays the current address based on geocoded coordinates

2. **Continuous Voice Monitoring**
   - Automatically requests microphone access when the app loads
   - Continuously listens for emergency keywords in multiple languages:
     - English: "help", "emergency", "sos"
     - Hindi: "मदद", "bachao"
     - Tamil: "உதவி"
   - No need to press a button to activate voice recognition

3. **Persistence**
   - All settings (including API keys) are saved locally and persist between app restarts
   - Location data is continuously updated and available for emergency alerts

## Browser Compatibility

This app uses Web APIs that may not be available in all browsers:
- The Web Speech Recognition API works best in Chrome and Edge
- Location services require HTTPS in production environments
- Microphone access requires user permission

## Setup Instructions

1. **Create a new file named `advanced_sos_app.py`** with the provided code

2. **Install the required packages**:
   ```bash
   pip install streamlit twilio requests geopy
   ```

3. **Run the application**:
   ```bash
   streamlit run advanced_sos_app.py
   ```

4. **Configure the required credentials** in the Settings tab:
   - Your name and emergency contact
   - Twilio API credentials
   - Save the settings to make them persistent

5. **Grant permissions** when prompted by your browser:
   - Allow location access
   - Allow microphone access

## How It Works

1. **Initialization**:
   - The app loads saved credentials from a pickle file
   - It sets up JavaScript components for continuous location and voice monitoring

2. **Voice Monitoring**:
   - Uses the Web Speech Recognition API to continuously listen for speech
   - Processes speech in real-time to detect emergency keywords
   - When a keyword is detected, it triggers the SOS alert automatically

3. **Location Tracking**:
   - Uses the browser's Geolocation API to get precise coordinates
   - Updates coordinates in real-time as the user moves
   - Converts coordinates to address information using the Nominatim geocoding service

4. **Emergency Response**:
   - Sends an SMS with precise location information using Twilio
   - Makes an emergency call that repeats continuously until answered
   - Provides a Google Maps link for tracking

## Usage in Emergencies

In a real emergency:

1. **Voice Activation**: Simply say "help", "emergency", "sos", etc. in any supported language
2. **Manual Activation**: Press the SOS button if unable to speak
3. **Automatic Response**:
   - The app will send an SMS with your location
   - It will place an emergency call with a repeating message
   - Your emergency contact will receive continuous location updates

## Notes for Production Use

For production deployment:
- Host the app on a secure HTTPS connection (required for location and microphone access)
- Consider implementing end-to-end encryption for sensitive data
- Set up proper error handling and monitoring for service availability
- Test thoroughly in various browsers and devices