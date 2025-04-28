# ai_travel_assistant/app.py
from flask import Flask, render_template, request, jsonify
import os, time
from handlers.audio import record_audio
from handlers.stt import stt_transcribe
from handlers.llm import llm_generate
from handlers.tts import tts_synthesize

app = Flask(__name__)

@app.after_request
def add_no_cache(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    return render_template('index.html', lang=lang)

@app.route('/process', methods=['POST'])
def process_audio():
    lang = request.args.get('lang', 'en')
    wav_path = record_audio(duration=5)
    transcript = stt_transcribe(wav_path)
    if not transcript:
        return jsonify({'error': 'Could not transcribe audio'}), 500
    reply = llm_generate(transcript, lang)

    out_mp3 = os.path.join('static', 'output.mp3')
    if os.path.exists(out_mp3): os.remove(out_mp3)
    tts_synthesize(reply, lang)
    timestamp = int(time.time())
    return jsonify({
        'transcript': transcript,
        'response': reply,
        'audio_url': f"/static/output.mp3?ts={timestamp}"
    })

if __name__ == '__main__':
    app.run(debug=True)