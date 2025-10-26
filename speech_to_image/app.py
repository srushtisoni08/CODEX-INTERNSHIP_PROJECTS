from flask import Flask, request, render_template, jsonify
import os
from werkzeug.utils import secure_filename
import whisper
import requests
from deep_translator import GoogleTranslator
import logging
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import subprocess
import tempfile
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'mp4', 'm4a', 'flac', 'ogg', 'webm', 'aac', 'wma'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Whisper model once at startup
whisper_model = None

def init_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("=" * 60)
        print("Loading Whisper model (this may take a few minutes first time)...")
        print("=" * 60)
        start_time = time.time()
        
        # Use tiny model for faster loading and processing
        whisper_model = whisper.load_model("tiny")  # Changed from "base" to "tiny"
        
        elapsed = time.time() - start_time
        print(f"✅ Whisper model loaded successfully in {elapsed:.2f} seconds!")
        print("=" * 60)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

def convert_audio_to_wav(input_path):
    """Convert audio file to WAV format using ffmpeg if available, otherwise return original"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_wav_path = temp_wav.name
        
        try:
            print(f"Converting audio to WAV format...")
            subprocess.run([
                'ffmpeg', '-i', input_path, 
                '-acodec', 'pcm_s16le', 
                '-ar', '16000', 
                '-ac', '1', 
                temp_wav_path, '-y'
            ], check=True, capture_output=True)
            print(f"✅ Audio converted successfully")
            return temp_wav_path
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"⚠️  FFmpeg conversion failed, using original file: {e}")
            os.unlink(temp_wav_path)
            return input_path
            
    except Exception as e:
        print(f"❌ Audio conversion error: {e}")
        return input_path

def transcribe_audio(file_path):
    converted_path = None
    try:
        init_whisper_model()
        
        print(f"\n{'='*60}")
        print(f"🎤 Starting transcription of: {os.path.basename(file_path)}")
        print(f"   File size: {os.path.getsize(file_path) / 1024:.2f} KB")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Convert to WAV first
        converted_path = convert_audio_to_wav(file_path)
        
        # Transcribe
        print("⏳ Transcribing audio (this may take 10-30 seconds)...")
        result = whisper_model.transcribe(
            converted_path,
            language=None,
            task="transcribe",
            verbose=False,  # Changed to False to reduce console spam
            word_timestamps=False,
            fp16=False  # Disable FP16 for better compatibility
        )
        
        elapsed = time.time() - start_time
        
        transcribed_text = result["text"].strip()
        detected_language = result.get("language", "unknown")
        
        print(f"\n✅ Transcription completed in {elapsed:.2f} seconds")
        print(f"   Detected language: {detected_language}")
        print(f"   Transcribed text: {transcribed_text[:100]}...")
        print(f"{'='*60}\n")
        
        if not transcribed_text:
            print("⚠️  Empty transcription result")
            return None
            
        return transcribed_text
        
    except Exception as e:
        logging.error(f"❌ Transcription error: {e}")
        print(f"\n{'='*60}")
        print(f"❌ TRANSCRIPTION FAILED")
        print(f"   Error: {str(e)}")
        print(f"{'='*60}\n")
        return None
    finally:
        if converted_path and converted_path != file_path:
            try:
                os.unlink(converted_path)
            except:
                pass

def create_placeholder_image(text):
    """Create a placeholder image with the transcribed text when no API key is available"""
    try:
        img = Image.new('RGB', (512, 512), color=(100, 120, 200))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            title_font = ImageFont.truetype("arial.ttf", 32)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Add gradient effect
        for y in range(512):
            color = (
                int(100 + (y / 512) * 100),
                int(120 + (y / 512) * 80),
                int(200 - (y / 512) * 50)
            )
            draw.line([(0, y), (512, y)], fill=color)
        
        # Add title
        title = "🎤→🖼️ Generated Image"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((512 - title_width) // 2, 50), title, fill='white', font=title_font)
        
        # Word wrap the text
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < 450:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw wrapped text
        y_start = 150
        for i, line in enumerate(lines[:8]):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (512 - line_width) // 2
            draw.text((x, y_start + i * 35), line, fill='white', font=font)
        
        # Add footer
        footer = "API key needed for AI image generation"
        footer_bbox = draw.textbbox((0, 0), footer, font=font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        draw.text(((512 - footer_width) // 2, 450), footer, fill=(200, 200, 200), font=font)
        
        # Save to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
        
    except Exception as e:
        logging.error(f"Error creating placeholder image: {e}")
        return "https://via.placeholder.com/512x512/6478EA/FFFFFF?text=Speech+to+Image"

def generate_image(prompt_text):
    try:
        api_key = os.environ.get('MONSTER_API_KEY')
        
        if not api_key or api_key == 'YOUR_API_KEY':
            print("⚠️  No API key, creating placeholder image...")
            return create_placeholder_image(prompt_text)
        
        print(f"🖼️  Generating image for: {prompt_text[:50]}...")
        
        monster_api_url = "https://api.monsterapi.ai/v1/generate/txt2img"
        payload = {
            "prompt": prompt_text,
            "width": 512,
            "height": 512,
            "samples": 1,
            "steps": 50
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(monster_api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'output' in result and len(result['output']) > 0:
            print("✅ Image generated successfully!")
            return result['output'][0]
        else:
            print("⚠️  No image in API response, creating placeholder...")
            return create_placeholder_image(prompt_text)
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Image generation API error: {e}")
        print(f"❌ API request failed: {e}")
        return create_placeholder_image(prompt_text)
    except Exception as e:
        logging.error(f"Unexpected error in image generation: {e}")
        return create_placeholder_image(prompt_text)

def translate_text(text, target_lang='en'):
    try:
        if not text or not text.strip():
            return text
        
        print(f"🌐 Translating text to {target_lang}...")
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        print(f"✅ Translation complete: {translated[:50]}...")
        return translated
            
    except Exception as e:
        logging.error(f"Translation error: {e}")
        print(f"⚠️  Translation failed, using original text")
        return text

@app.route('/upload', methods=['POST'])
def upload():
    try:
        print(f"\n{'='*60}")
        print("📤 NEW UPLOAD REQUEST")
        print(f"{'='*60}")
        
        if 'audio' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        audio = request.files['audio']
        
        if audio.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(audio.filename):
            allowed_formats = ', '.join(ALLOWED_EXTENSIONS)
            return jsonify({
                "error": f"Invalid file type. Allowed formats: {allowed_formats}"
            }), 400
        
        filename = secure_filename(audio.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio.save(filepath)
        
        file_size = os.path.getsize(filepath)
        print(f"📁 File saved: {filename} ({file_size / 1024:.2f} KB)")

        if file_size < 100:
            os.remove(filepath)
            return jsonify({"error": "Audio file appears to be empty or corrupted"}), 400

        # Transcribe audio
        try:
            text = transcribe_audio(filepath)
            if text is None or not text.strip():
                return jsonify({
                    "error": "Could not transcribe audio. Please ensure the audio is clear and contains speech.",
                    "suggestions": [
                        "Try speaking more clearly",
                        "Ensure your microphone is working",
                        "Try uploading a different audio file",
                        "Make sure the audio contains speech (not just silence)"
                    ]
                }), 500
                
        except Exception as transcription_error:
            print(f"❌ Transcription failed: {transcription_error}")
            return jsonify({
                "error": "Audio transcription failed.",
                "technical_details": str(transcription_error)
            }), 500

        # Translate text
        translated_text = translate_text(text.strip())
        
        # Enhance prompt
        enhanced_prompt = f"high quality, detailed, artistic: {translated_text}"

        # Generate image
        image_url = generate_image(enhanced_prompt)
        if image_url is None:
            return jsonify({"error": "Failed to generate image"}), 500

        # Cleanup
        try:
            os.remove(filepath)
            print(f"🗑️  Cleaned up file: {filename}")
        except Exception as cleanup_error:
            print(f"⚠️  Cleanup error: {cleanup_error}")

        print(f"{'='*60}")
        print("✅ REQUEST COMPLETED SUCCESSFULLY")
        print(f"{'='*60}\n")

        return render_template('result.html', 
                             image_url=image_url, 
                             original_text=text,
                             translated_text=translated_text,
                             enhanced_prompt=enhanced_prompt)
    
    except Exception as e:
        logging.error(f"Upload error: {e}")
        print(f"❌ Unexpected error: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "whisper_loaded": whisper_model is not None,
        "api_key_configured": bool(os.environ.get('MONSTER_API_KEY'))
    })

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 16MB"}), 413

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("🚀 STARTING SPEECH-TO-IMAGE FLASK APP")
    print("="*60)
    print(f"📁 Supported audio formats: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Check API key
    api_key = os.environ.get('MONSTER_API_KEY')
    if not api_key:
        print("\n⚠️  WARNING: No MONSTER_API_KEY found")
        print("   → Placeholder images will be generated")
        print("   → To use real AI images:")
        print("      1. Get API key from Monster API")
        print("      2. Set: export MONSTER_API_KEY='your_key_here'")
    else:
        print("\n✅ Monster API key configured")
    
    # Pre-load Whisper model
    print("\n🔄 Pre-loading Whisper model...")
    init_whisper_model()
    
    print("\n" + "="*60)
    print("✅ SERVER READY - Visit http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)