from flask import Flask, request, render_template
import os
from werkzeug.utils import secure_filename
import whisper
import requests
from googletrans import Translator

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

def transcribe_audio(file_path):
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

def generate_image(prompt_text):
    monster_api_url = "https://api.monsterapi.com/generate"
    api_key = "YOUR_API_KEY"
    payload = {
        "prompt": prompt_text,
        "size": "512x512"
    }
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.post(monster_api_url, json=payload, headers=headers)
    return response.json().get("image_url")

def translate_text(text, target_lang='en'):
    translator = Translator()
    translated = translator.translate(text, dest=target_lang)
    return translated.text

@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return "No file uploaded", 400
    audio = request.files['audio']
    filename = secure_filename(audio.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio.save(filepath)

    text = transcribe_audio(filepath)

    translated_text = translate_text(text)

    image_url = generate_image(translated_text)

    return render_template('result.html', image_url=image_url, text=text, translated_text=translated_text)

if __name__ == '__main__':
    app.run(debug=True)
