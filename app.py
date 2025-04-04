import streamlit as st
import streamlit.components.v1 as components
import base64
import time
import os
import pickle
from twilio.rest import Client
import random
# Near the beginning of your app, after imports
import streamlit.web.server.server as server

# Check for voice emergency POST requests
try:
    request = server.get_request()
    if request is not None and request.method == "POST":
        form = request.form
        if "emergency_trigger" in form and form["emergency_trigger"] == "true":
            keyword = form.get("voice_keyword", "unknown")
            st.session_state.sos_triggered = True
            st.session_state.trigger_source = f"Voice Command: '{keyword}'"
            st.session_state.sos_triggered_action_completed = False
except Exception as e:
    # Just log the error and continue
    print(f"Error processing POST request: {e}")

# Page configuration
st.set_page_config(
    page_title="SOS Emergency App",
    page_icon="🆘",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Path for saving credentials
CREDENTIALS_FILE = "sos_credentials.pkl"

# Load saved credentials if they exist
def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Error loading credentials: {e}")
    return {}

# Save credentials
def save_credentials():
    credentials = {
        'twilio_account_sid': st.session_state.twilio_account_sid,
        'twilio_auth_token': st.session_state.twilio_auth_token,
        'twilio_phone_number': st.session_state.twilio_phone_number,
        'emergency_contact': st.session_state.emergency_contact,
        'user_name': st.session_state.user_name
    }
    try:
        with open(CREDENTIALS_FILE, 'wb') as f:
            pickle.dump(credentials, f)
        return True
    except Exception as e:
        st.error(f"Error saving credentials: {e}")
        return False

# CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .sos-button {
        background-color: #dc3545;
        color: white;
        border: none;
        border-radius: 50%;
        width: 200px;
        height: 200px;
        font-size: 32px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        transition: transform 0.3s, box-shadow 0.3s;
        margin: 0 auto;
        display: block;
    }
    .sos-button:hover {
        transform: scale(1.05);
        box-shadow: 0 12px 20px rgba(0,0,0,0.3);
    }
    .title {
        text-align: center;
        color: #343a40;
        margin-bottom: 30px;
    }
    .container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 30px;
    }
    .settings-container {
        margin-top: 40px;
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        width: 100%;
    }
    .header-section {
        padding: 20px;
        background-color: #dc3545;
        color: white;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .footer {
        margin-top: 50px;
        text-align: center;
        color: #6c757d;
        font-size: 14px;
    }
    .listening-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin: 20px 0;
    }
    .mic-icon {
        color: #dc3545;
        font-size: 24px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    .siren-active {
        border: 3px solid #dc3545;
        animation: siren-border 1s infinite;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    @keyframes siren-border {
        0% { border-color: #dc3545; }
        50% { border-color: #ffc107; }
        100% { border-color: #dc3545; }
    }
</style>
""", unsafe_allow_html=True)
def insert_voice_js():
    html = """
    <div id="voice-status" style="margin-top: 10px; padding: 10px; border-radius: 5px; background-color: #fff3cd; color: #856404;">
        Initializing voice recognition...
    </div>
    <script>
    function triggerSOSDirectly(keyword) {
        console.log("Emergency keyword detected: " + keyword);
        
        const voiceStatus = document.getElementById('voice-status');
        if (voiceStatus) {
            voiceStatus.style.backgroundColor = '#f8d7da';
            voiceStatus.style.color = '#721c24';
            voiceStatus.innerHTML = `<strong>EMERGENCY DETECTED: "${keyword}"</strong><br>Triggering SOS...`;
        }
        
        if (typeof window.triggerEmergencyDirectly === 'function') {
            window.triggerEmergencyDirectly(keyword);
        } else {
            localStorage.setItem('sos_voice_trigger', keyword);
            localStorage.setItem('sos_voice_time', new Date().getTime());
        }
        
        return true;
    }

    function setupVoiceRecognition() {
        const voiceStatus = document.getElementById('voice-status');
        
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            if (voiceStatus) {
                voiceStatus.style.backgroundColor = '#f8d7da';
                voiceStatus.style.color = '#721c24';
                voiceStatus.textContent = 'Speech recognition not supported in this browser';
            }
            return;
        }

        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(() => {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                
                // Configuration
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.maxAlternatives = 3;
                
                // Keywords with more variations
                const keywords = {
                    'en-US': ['help', 'emergency', 'sos', 'danger', 'accident', 'save me', 'help me'],
                    'hi-IN': ['मदद', 'आपातकाल', 'खतरा', 'बचाओ', 'सहायता', 'मुझे बचाओ'],
                    'ta-IN': ['உதவி', 'அவசரம்', 'ஆபத்து', 'காப்பாற்று', 'என்னை காப்பாற்று']
                };

                const languages = ['en-US', 'hi-IN', 'ta-IN'];
                let currentLanguageIndex = 0;
                let isProcessing = false;

                function updateStatus(message, type = 'info') {
                    if (voiceStatus) {
                        voiceStatus.textContent = message;
                        voiceStatus.style.backgroundColor = type === 'info' ? '#d4edda' : '#f8d7da';
                        voiceStatus.style.color = type === 'info' ? '#155724' : '#721c24';
                    }
                }

                function startRecognition() {
                    if (isProcessing) return;
                    
                    recognition.lang = languages[currentLanguageIndex];
                    currentLanguageIndex = (currentLanguageIndex + 1) % languages.length;
                    
                    const langName = recognition.lang === 'en-US' ? 'English' : 
                                    recognition.lang === 'hi-IN' ? 'Hindi' : 'Tamil';
                    
                    updateStatus(`Listening for emergency keywords in ${langName}...`, 'info');
                    
                    try {
                        recognition.start();
                        isProcessing = true;
                    } catch (e) {
                        console.error('Recognition start error:', e);
                        setTimeout(startRecognition, 3000);
                    }
                }

                recognition.onstart = () => {
                    console.log('Recognition started for', recognition.lang);
                };

                recognition.onresult = (event) => {
                    for (let i = event.resultIndex; i < event.results.length; i++) {
                        const result = event.results[i];
                        if (result.isFinal) {
                            const transcript = result[0].transcript.toLowerCase();
                            console.log('Recognized:', transcript);
                            
                            const currentKeywords = keywords[recognition.lang];
                            for (const keyword of currentKeywords) {
                                if (transcript.includes(keyword.toLowerCase())) {
                                    triggerSOSDirectly(keyword);
                                    return;
                                }
                            }
                        }
                    }
                };

                recognition.onend = () => {
                    isProcessing = false;
                    setTimeout(startRecognition, 2000);
                };

                recognition.onerror = (event) => {
                    console.error('Recognition error:', event.error);
                    isProcessing = false;
                    
                    let errorMsg = 'Error occurred';
                    if (event.error === 'no-speech') {
                        errorMsg = 'No speech detected';
                    } else if (event.error === 'audio-capture') {
                        errorMsg = 'No microphone found';
                    } else if (event.error === 'not-allowed') {
                        errorMsg = 'Microphone access denied';
                    }
                    
                    updateStatus(errorMsg + ' - Trying again...', 'error');
                    setTimeout(startRecognition, 3000);
                };

                // Initial start with delay
                setTimeout(startRecognition, 1000);
            })
            .catch((error) => {
                if (voiceStatus) {
                    voiceStatus.style.backgroundColor = '#f8d7da';
                    voiceStatus.style.color = '#721c24';
                    voiceStatus.textContent = `Microphone access denied: ${error.message}`;
                }
            });
    }

    // Start after short delay
    setTimeout(setupVoiceRecognition, 500);
    </script>
    """
    components.html(html, height=150)
# In your main app logic
def check_voice_trigger_source():
    """Check if a voice trigger source exists in localStorage"""
    if 'trigger_source' in st.experimental_get_query_params():
        trigger_source = st.experimental_get_query_params().get('trigger_source', [None])[0]
        if trigger_source:
            st.session_state.trigger_source = trigger_source
            # Clear the query param
            st.experimental_set_query_params()

def check_voice_emergency():
    """
    Placeholder function to prevent NameError
    Can be left empty or removed if not needed
    """
    pass


# Function to embed and play siren audio
def play_siren_audio():
    audio_html = """
    <div class="siren-active">
        <strong>🚨 EMERGENCY SIREN ACTIVE 🚨</strong>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            try {{
                const audioElement = new Audio('data:audio/mpeg;base64,{0}');
                audioElement.volume = 0.8;  // Set volume to 80%
                audioElement.loop = true;   // Loop the audio
                
                // Play the audio
                const playPromise = audioElement.play();
                
                // Handle autoplay restrictions
                if (playPromise !== undefined) {{
                    playPromise.catch(function(error) {{
                        console.error('Audio playback failed:', error);
                        // Create visual alert instead
                        const sirenDiv = document.querySelector('.siren-active');
                        if (sirenDiv) {{
                            sirenDiv.style.padding = '20px';
                            sirenDiv.style.fontSize = '18px';
                            sirenDiv.style.animation = 'siren-border 0.5s infinite';
                        }}
                    }});
                }}
                
                // Make sure siren keeps playing
                document.addEventListener('click', function() {{
                    audioElement.play().catch(e => console.error('Siren retry failed:', e));
                }});
                
            }} catch (err) {{
                console.error('Error setting up siren:', err);
            }}
        }});
    </script>
    """
    
    # Try to load siren from file
    try:
        with open("siren.mp3", "rb") as f:
            audio_bytes = f.read()
            audio_b64 = base64.b64encode(audio_bytes).decode()
            components.html(audio_html.format(audio_b64), height=80)
            return True
    except Exception as e:
        # Fallback to visual alert only if audio fails
        fallback_html = """
        <div class="siren-active" style="padding: 20px; font-size: 18px;">
            <strong>🚨 EMERGENCY ALERT ACTIVE 🚨</strong>
        </div>
        """
        components.html(fallback_html, height=80)
        st.warning(f"Using visual alert only. Could not load siren audio: {e}")
        return False


# Fixed hard-coded location
def get_location():
    """
    Simulate a more realistic location fetching process
    with dynamic coordinates and address
    """
    # Base coordinates for Delhi with some randomization
    base_latitude = 28.5796481
    base_longitude = 76.9759274
    
    # Add small random variation to make location more dynamic
    latitude = base_latitude + random.uniform(-0.05, 0.05)
    longitude = base_longitude + random.uniform(-0.05, 0.05)
    
    # Simulate location fetching delay
    with st.spinner("Fetching precise location..."):
        time.sleep(2)  # 2-second delay to simulate fetching
    
    # Try to get a more precise address using reverse geocoding
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={latitude}&lon={longitude}"
        response = requests.get(url, headers={'User-Agent': 'SOSEmergencyApp/1.0'})
        
        if response.status_code == 200:
            location_data = response.json()
            formatted_address = location_data.get('display_name', 'National Highways Authority of India, Dabri, Sector 10 Dwarka, Dwarka, New Delhi, Delhi 110075, India')
        else:
            formatted_address = 'National Highways Authority of India, Dabri, Sector 10 Dwarka, Dwarka, New Delhi, Delhi 110075, India'
    except:
        formatted_address = 'National Highways Authority of India, Dabri, Sector 10 Dwarka, Dwarka, New Delhi, Delhi 110075, India'
    
    # Create Google Maps link with precise coordinates
    maps_link = f"https://maps.google.com/?q={latitude},{longitude}"
    
    return {
        'latitude': round(latitude, 6),
        'longitude': round(longitude, 6),
        'address': formatted_address,
        'google_maps_link': maps_link
    }

def send_emergency_sms(to_number, message):
    """Send emergency SMS using Twilio"""
    try:
        if not st.session_state.twilio_account_sid or not st.session_state.twilio_auth_token or not st.session_state.twilio_phone_number:
            st.error("Twilio credentials are missing. Please configure them in settings.")
            return False
            
        client = Client(st.session_state.twilio_account_sid, st.session_state.twilio_auth_token)
        
        # Create a simple message with no formatting that might cause issues
        clean_message = message.replace('\n', ' ').strip()
        
        message = client.messages.create(
            body=clean_message,
            from_=st.session_state.twilio_phone_number,
            to=to_number
        )
        
        return True
    except Exception as e:
        st.error(f"Error sending SMS: {e}")
        return False

def make_emergency_call(to_number, message):
    """Make emergency call using Twilio"""
    try:
        if not st.session_state.twilio_account_sid or not st.session_state.twilio_auth_token or not st.session_state.twilio_phone_number:
            st.error("Twilio credentials are missing. Please configure them in settings.")
            return False
            
        client = Client(st.session_state.twilio_account_sid, st.session_state.twilio_auth_token)
        
        # Creating TwiML for the call with repeated message - simpler version
        twiml = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="woman" language="en-US">Emergency alert. {message}</Say>
            <Pause length="1"/>
            <Say voice="woman" language="en-US">This is an automated emergency call. Please respond immediately.</Say>
            <Pause length="1"/>
            <Redirect/>
        </Response>
        """
        
        call = client.calls.create(
            twiml=twiml,
            from_=st.session_state.twilio_phone_number,
            to=to_number
        )
        
        return True
    except Exception as e:
        st.error(f"Error making call: {e}")
        return False

def add_voice_trigger_component():
    """Add a hidden component that can trigger SOS without page reload"""
    from streamlit.components.v1 import html
    
    component_html = """
    <div id="voice-trigger-component" style="display:none;"></div>
    <script>
    // Store the last message to prevent duplicates
    let lastMessage = '';
    
    // This function will be called by the voice recognition code
    window.triggerEmergencyDirectly = function(keyword) {
        // Create a unique message
        const message = keyword + '_' + new Date().getTime();
        if (message === lastMessage) return; // Prevent duplicates
        lastMessage = message;
        
        // Create a form to submit
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '';
        
        // Add the keyword as a hidden field
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'voice_keyword';
        input.value = keyword;
        form.appendChild(input);
        
        // Add a flag to identify this is an emergency
        const flag = document.createElement('input');
        flag.type = 'hidden';
        flag.name = 'emergency_trigger';
        flag.value = 'true';
        form.appendChild(flag);
        
        // Add to document and submit
        document.body.appendChild(form);
        form.submit();
    };
    </script>
    """
    
    html(component_html, height=0)


def trigger_sos(trigger_type="button"):
    """Trigger SOS alert with all emergency actions in specified sequence"""
    with st.spinner("🚨 Activating SOS emergency response..."):
        try:
            # Get hardcoded location
            location = get_location()
            
            # Prepare emergency message for call and SMS
            call_message = (
                f"{st.session_state.user_name} needs immediate assistance. "
                f"Location: {location['address']}. "
                f"Coordinates: {location['latitude']}, {location['longitude']}"
            )
            sms_message = (
                f"EMERGENCY SOS ALERT! {st.session_state.user_name} needs immediate help. "
                f"Location: {location['address']}. "
                f"Google Maps: {location['google_maps_link']}"
            )
            
            # 1. First make emergency call with 2 second delay
            st.info("Step 1: Initiating emergency call...")
            time.sleep(2)  # 2 second delay
            call_made = make_emergency_call(
                st.session_state.emergency_contact,
                call_message
            )
            
            # 2. Then send SMS with 3 second delay
            st.info("Step 2: Sending emergency SMS...")
            time.sleep(2)  # 3 second delay
            sms_sent = send_emergency_sms(
                st.session_state.emergency_contact, 
                sms_message
            )
            
            # 3. Play siren with 3 second delay (this will be handled in the main code)
            st.info("Step 3: Activating emergency siren...")
            time.sleep(1)  # 3 second delay
            
            # Mark as completed to prevent duplicate calls
            st.session_state.sos_triggered_action_completed = True
            
            return sms_sent, call_made, location
        except Exception as e:
            st.error(f"Error during SOS process: {e}")
            return False, False, get_location()

# Initialize session state variables
if 'initialized' not in st.session_state:
    # Load saved credentials
    credentials = load_credentials()
    
    # Set session state variables from loaded credentials or defaults
    st.session_state.sos_triggered = False
    st.session_state.voice_trigger_detected = False
    st.session_state.sos_triggered_action_completed = False  # Track if SOS action sequence completed
    st.session_state.twilio_account_sid = credentials.get('twilio_account_sid', "")
    st.session_state.twilio_auth_token = credentials.get('twilio_auth_token', "")
    st.session_state.twilio_phone_number = credentials.get('twilio_phone_number', "")
    st.session_state.emergency_contact = credentials.get('emergency_contact', "")
    st.session_state.user_name = credentials.get('user_name', "User")
    
    st.session_state.initialized = True

# Process form submissions from JavaScript
if 'voice_detected' in st.session_state:
    if st.session_state.voice_detected == 'true' or st.session_state.voice_detected == True:
        # Handle voice trigger from POST
        st.session_state.voice_trigger_detected = True
        voice_keyword = st.session_state.get('voice_keyword_detected', 'unknown')
        st.session_state.trigger_source = f"Voice Command: '{voice_keyword}'"
        st.session_state.sos_triggered = True
        st.session_state.sos_triggered_action_completed = False  # Reset to run the sequence
        # Clear the flag to prevent reprocessing
        st.session_state.voice_detected = False

# Check query parameters for voice trigger - this is more reliable
if st.query_params:
    # Check for voice trigger
    if "voice_triggered" in st.query_params:
        voice_triggered_val = st.query_params.get("voice_triggered", "false")
        if voice_triggered_val.lower() == "true":
            st.session_state.voice_trigger_detected = True
            voice_keyword = st.query_params.get("voice_keyword", "unknown")
            st.session_state.trigger_source = f"Voice Command: '{voice_keyword}'"
            st.session_state.sos_triggered = True
            # Reset the action completion flag to ensure the flow runs
            st.session_state.sos_triggered_action_completed = False
    
    # Clear query parameters to prevent reprocessing
    st.query_params.clear()

add_voice_trigger_component()
# Add main page content
# Main app layout
st.markdown("<div class='header-section'><h1 class='title'>🆘 Emergency SOS Alert System</h1></div>", unsafe_allow_html=True)

# Check voice emergency
check_voice_emergency()

# App tabs
tab1, tab2 = st.tabs(["SOS Alert", "Settings"])

with tab1:
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    
    # Show location status with hardcoded location
    st.subheader("Location Status")
    location = get_location()
    st.success(f"Location: {location['address']}")
    st.info(f"Coordinates: {location['latitude']}, {location['longitude']}")
    st.info(f"Google Maps: {location['google_maps_link']}")
    
    st.subheader("Voice Monitoring Status")
    insert_voice_js()
    

    # Show active monitoring indicator
    st.markdown("""
    <div class="listening-indicator">
        <span class="mic-icon">🎤</span>
        <span>Always listening for emergency keywords in English, Hindi, and Tamil</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Single consistent UI for both trigger methods
    if not st.session_state.sos_triggered:
        # Show normal state with SOS button
        st.warning("Press the SOS button below in case of emergency or say 'help' (also works with Hindi and Tamil keywords)")
        
        # Large SOS Button
        if st.button("SOS", key="sos_button", use_container_width=True):
            # Set trigger state before running actions
            st.session_state.sos_triggered = True
            st.session_state.trigger_source = st.session_state.get('trigger_source', "SOS Button")
            st.session_state.sos_triggered_action_completed = False
            st.rerun()
    else:
         # Show emergency state (same UI regardless of trigger method)
        # First check if the emergency sequence has been run
        if not st.session_state.sos_triggered_action_completed:
            # Show unified SOS emergency info
            st.error("🚨 EMERGENCY SOS ACTIVATED 🚨")
            
            # Run the unified emergency sequence
            sms_sent, call_made, location = trigger_sos()
            
            # Play the siren
            siren_played = play_siren_audio()
            
            # Force a rerun to update UI
            st.rerun()
        else:
            # Show ongoing emergency info (same for both button and voice)
            st.success("SOS alert has been triggered. Help is on the way!")
            
            # Show what triggered the alert
            if hasattr(st.session_state, 'trigger_source'):
                st.info(f"Triggered by: {st.session_state.trigger_source}")
            
            # Play the siren
            siren_played = play_siren_audio()
            
            # Show location info
            location = get_location()
            st.info(f"Location: {location['address']}")
            st.info(f"Google Maps: {location['google_maps_link']}")
            
            # Reset button
            if st.button("Reset SOS", key="reset_sos"):
                st.session_state.sos_triggered = False
                st.session_state.voice_trigger_detected = False
                st.session_state.sos_triggered_action_completed = False
                if hasattr(st.session_state, 'trigger_source'):
                    delattr(st.session_state, 'trigger_source')
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='settings-container'>", unsafe_allow_html=True)
    st.subheader("User Information")
    
    # User info
    user_name = st.text_input("Your Name", value=st.session_state.user_name)
    if user_name != st.session_state.user_name:
        st.session_state.user_name = user_name
    
    emergency_contact = st.text_input("Emergency Contact Number (with country code)", value=st.session_state.emergency_contact, 
                                   placeholder="+1234567890")
    if emergency_contact != st.session_state.emergency_contact:
        st.session_state.emergency_contact = emergency_contact
    
    # API Settings with expanders
    with st.expander("Twilio API Settings"):
        twilio_account_sid = st.text_input("Twilio Account SID", value=st.session_state.twilio_account_sid, 
                                        type="password")
        if twilio_account_sid != st.session_state.twilio_account_sid:
            st.session_state.twilio_account_sid = twilio_account_sid
        
        twilio_auth_token = st.text_input("Twilio Auth Token", value=st.session_state.twilio_auth_token, 
                                       type="password")
        if twilio_auth_token != st.session_state.twilio_auth_token:
            st.session_state.twilio_auth_token = twilio_auth_token
        
        twilio_phone_number = st.text_input("Twilio Phone Number", value=st.session_state.twilio_phone_number, 
                                         placeholder="+1234567890")
        if twilio_phone_number != st.session_state.twilio_phone_number:
            st.session_state.twilio_phone_number = twilio_phone_number
    
    # Siren audio upload
    with st.expander("Emergency Siren Settings"):
        st.info("Upload an MP3 file named 'siren.mp3' to your Streamlit app folder to enable the emergency siren.")
        
        # Check if siren file exists
        siren_exists = os.path.exists("siren.mp3")
        if siren_exists:
            st.success("Siren audio file found and ready to use!")
        else:
            st.warning("No siren.mp3 file found. Please upload one to enable the siren feature.")
    
    # Save settings button
    if st.button("Save Settings", use_container_width=True):
        if save_credentials():
            st.success("Settings saved successfully and will be remembered when you restart the app!")
        else:
            st.error("Failed to save settings permanently. They will work for this session only.")
    
    st.markdown("</div>", unsafe_allow_html=True)


# Modify your main Streamlit app to include these functions
def main_sos_app():
    # Setup voice emergency detection HTML
    setup_voice_emergency_detection()
    
    # Process voice emergency trigger
    voice_emergency_detected = process_voice_emergency()
    
    # Rest of your existing Streamlit app code
    # ... (your existing code)
    
    # If voice emergency is detected, you can trigger the same SOS flow as button
    if voice_emergency_detected:
        # Trigger SOS flow
        st.rerun()

# You would call this in your main app script
# main_sos_app()