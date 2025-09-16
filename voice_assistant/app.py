from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from gtts import gTTS
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import io
import tempfile

load_dotenv()

app = Flask(__name__)

# Load environment variables from .env file

# API keys (replace with your own keys)
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

REMINDERS_FILE = 'reminders.json'
AUDIO_DIR = 'static/audio'

# Ensure required directories exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs('static', exist_ok=True)

# Ensure reminders file exists
if not os.path.exists(REMINDERS_FILE):
    with open(REMINDERS_FILE, 'w') as f:
        json.dump([], f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio_data' not in request.files:
        return jsonify({'response': 'No audio file received.'}), 400

    audio_file = request.files['audio_data']
    recognizer = sr.Recognizer()

    try:
        # Log file details
        app.logger.info(f"Received audio file: {audio_file.filename}, Content-Type: {audio_file.content_type}")
        
        # Read the uploaded file into memory
        audio_bytes = audio_file.read()
        app.logger.info(f"Audio file size: {len(audio_bytes)} bytes")
        
        if len(audio_bytes) == 0:
            return jsonify({'response': 'Empty audio file received.'}), 400

        # Create BytesIO stream from the audio data
        audio_stream = io.BytesIO(audio_bytes)
        
        # Try to process the audio file directly
        with sr.AudioFile(audio_stream) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = recognizer.record(source)

        # Recognize using Google Web Speech API
        text = recognizer.recognize_google(audio_data)
        app.logger.info(f"Successfully recognized text: {text}")

    except sr.UnknownValueError:
        app.logger.warning("Speech recognition could not understand audio")
        return jsonify({'response': "Could not understand audio. Please speak more clearly and try again."}), 400
    except sr.RequestError as e:
        app.logger.error(f"Speech recognition request error: {e}")
        return jsonify({'response': "Speech recognition service is unavailable. Please check your internet connection and try again."}), 500
    except Exception as e:
        app.logger.error(f"Audio processing error: {str(e)}")
        return jsonify({'response': f"Audio processing error: {str(e)}. Please ensure you're using Chrome browser and try again."}), 500

    # Process the command and return a response
    response = handle_command(text.lower())
    return jsonify({'response': response, 'recognized_text': text})

def handle_command(command_text):
    """Enhanced command handling with more features"""
    command_text = command_text.lower().strip()
    
    # Greeting commands
    if any(word in command_text for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        return "Hi there! How can I help you today?"
    
    # Weather commands
    if any(word in command_text for word in ["weather", "temperature", "forecast", "climate"]):
        return get_weather()
    
    # News commands
    if any(word in command_text for word in ["news", "headlines", "current events", "latest news"]):
        return get_news()
    
    # Reminder commands - multiple variations
    if any(phrase in command_text for phrase in ["remind me", "set a reminder", "setting a reminder", "create a reminder", "reminder to", "remember to"]):
        return set_reminder(command_text)
    
    # Time commands
    if any(word in command_text for word in ["time", "clock", "what time"]):
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}"
    
    # Date commands
    if any(word in command_text for word in ["date", "today", "what day", "calendar"]):
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}"
    
    # Help commands
    if any(word in command_text for word in ["help", "what can you do", "commands", "options"]):
        return "I can help you with: weather information, latest news, current time and date, setting reminders, and general conversation. Just speak naturally!"
    
    # Thank you
    if any(word in command_text for word in ["thank", "thanks", "thank you"]):
        return "You're welcome! Is there anything else I can help you with?"
    
    # Goodbye
    if any(word in command_text for word in ["goodbye", "bye", "see you", "farewell"]):
        return "Goodbye! Have a great day!"
    
    # Default response
    return f"I heard you say '{command_text}', but I'm not sure how to help with that. Try asking about weather, news, time, setting reminders, or just say hello!"

def get_weather():
    """Get weather information"""
    if not WEATHER_API_KEY:
        return "Weather API key not configured."
    
    city = 'London'  # You can make this dynamic
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric'
    try:
        res = requests.get(url, timeout=5).json()
        if res.get('cod') != 200:
            return "Couldn't fetch weather information."
        
        description = res['weather'][0]['description']
        temp = res['main']['temp']
        feels_like = res['main']['feels_like']
        return f"The weather in {city} is {description} with a temperature of {temp}°C, feels like {feels_like}°C."
    except Exception as e:
        return "Couldn't fetch the weather information."

def get_news():
    """Get latest news headlines"""
    if not NEWS_API_KEY:
        return "News API key not configured."
    
    url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}'
    try:
        res = requests.get(url, timeout=5).json()
        if res.get('status') != 'ok':
            return "Couldn't fetch the news."
        
        articles = res.get('articles', [])[:3]
        if not articles:
            return "No news articles found."
        
        headlines = [article['title'] for article in articles if article.get('title')]
        return "Here are the top headlines: " + " ... ".join(headlines)
    except Exception as e:
        return "Couldn't fetch the news."

def set_reminder(text):
    """Set a reminder with improved parsing"""
    try:
        text = text.lower().strip()
        reminder_text = ""
        
        # Try different patterns to extract the reminder content
        patterns = [
            "remind me to ",
            "remind me ",
            "set a reminder to ",
            "set a reminder for ",
            "setting a reminder to ",
            "setting a reminder for ",
            "create a reminder to ",
            "reminder to ",
            "remember to "
        ]
        
        for pattern in patterns:
            if pattern in text:
                reminder_text = text.split(pattern, 1)[1].strip()
                break
        
        # If no pattern matched, try to extract after "reminder"
        if not reminder_text and "reminder" in text:
            parts = text.split("reminder", 1)
            if len(parts) > 1:
                # Remove common words like "about", "for", "to" from the beginning
                reminder_text = parts[1].strip()
                for prefix in ["about ", "for ", "to ", "that ", ": "]:
                    if reminder_text.startswith(prefix):
                        reminder_text = reminder_text[len(prefix):].strip()
                        break
        
        if not reminder_text:
            return "I couldn't understand what you want to be reminded about. Please say something like 'remind me to call mom' or 'set a reminder to buy groceries'."
        
        # Clean up the reminder text
        reminder_text = reminder_text.strip()
        if not reminder_text:
            return "Please specify what you want to be reminded about."
        
        # Save the reminder
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Load existing reminders
        try:
            with open(REMINDERS_FILE, 'r') as f:
                reminders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            reminders = []
        
        # Add new reminder
        reminders.append({"text": reminder_text, "time": now})
        
        # Save reminders
        with open(REMINDERS_FILE, 'w') as f:
            json.dump(reminders, f, indent=2)
        
        return f"Reminder set successfully: {reminder_text}"
        
    except Exception as e:
        app.logger.error(f"Error setting reminder: {str(e)}")
        return "Sorry, I couldn't set that reminder. Please try again."

@app.route('/speak', methods=['POST'])
def speak():
    """Convert text to speech and return audio file URL"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data.get('text')
        if not text.strip():
            return jsonify({'error': 'Empty text provided'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().timestamp()
        filename = f'{timestamp}.mp3'
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Create TTS and save file
        tts = gTTS(text=text, lang='en')
        tts.save(filepath)
        
        # Return relative URL for the audio file
        audio_url = f'static/audio/{filename}'
        return jsonify({'audio_url': audio_url})
        
    except Exception as e:
        app.logger.error(f"Error in speak endpoint: {str(e)}")
        return jsonify({'error': 'Failed to generate speech'}), 500

@app.route('/reminders', methods=['GET'])
def get_reminders():
    """Get all reminders"""
    try:
        with open(REMINDERS_FILE, 'r') as f:
            reminders = json.load(f)
        return jsonify({'reminders': reminders})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({'reminders': []})

@app.route('/reminders', methods=['DELETE'])
def clear_reminders():
    """Clear all reminders"""
    try:
        with open(REMINDERS_FILE, 'w') as f:
            json.dump([], f)
        return jsonify({'message': 'All reminders cleared'})
    except Exception as e:
        return jsonify({'error': 'Failed to clear reminders'}), 500

# Cleanup old audio files on startup
def cleanup_old_audio_files():
    """Remove audio files older than 1 hour"""
    try:
        current_time = datetime.now().timestamp()
        for filename in os.listdir(AUDIO_DIR):
            if filename.endswith('.mp3'):
                file_path = os.path.join(AUDIO_DIR, filename)
                try:
                    # Extract timestamp from filename
                    file_timestamp = float(filename.split('.')[0])
                    # If file is older than 1 hour (3600 seconds), delete it
                    if current_time - file_timestamp > 3600:
                        os.remove(file_path)
                except (ValueError, OSError):
                    # If we can't parse the timestamp or delete the file, skip it
                    pass
    except Exception as e:
        app.logger.error(f"Error cleaning up audio files: {str(e)}")

if __name__ == "__main__":
    # Cleanup old audio files on startup
    cleanup_old_audio_files()
    app.run(debug=True)