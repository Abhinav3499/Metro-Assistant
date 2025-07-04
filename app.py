from flask import Flask, render_template, request, jsonify
import os, time
from handlers.audio import record_audio
from handlers.stt import stt_transcribe
from handlers.agent import process_with_agent
from handlers.rag import enhance_response_with_rag
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
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_audio():
    start_time = time.time()
    
    # Record audio
    wav_path = record_audio(duration=5)
    transcript = stt_transcribe(wav_path)
    
    if not transcript:
        return jsonify({'error': 'Could not transcribe audio'}), 500
    
    # Process with agentic AI
    try:
        response = process_with_agent(transcript, 'en')
        
        # Enhance with RAG
        enhanced_response = enhance_response_with_rag(transcript, response)
        
        # Generate audio
        out_mp3 = os.path.join('static', 'output.mp3')
        if os.path.exists(out_mp3): 
            os.remove(out_mp3)
        tts_synthesize(enhanced_response, 'en')
        
        timestamp = int(time.time())
        return jsonify({
            'transcript': transcript,
            'response': enhanced_response,
            'audio_url': f"/static/output.mp3?ts={timestamp}"
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/process_text', methods=['POST'])
def process_text():
    start_time = time.time()
    data = request.get_json()
    user_query = data.get('query', '')
    
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        # Process with agentic AI
        response = process_with_agent(user_query, 'en')
        
        # Enhance with RAG
        enhanced_response = enhance_response_with_rag(user_query, response)
        
        return jsonify({
            'response': enhanced_response
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/api/history')
def get_history():
    return jsonify([])

@app.route('/api/favorites')
def get_favorites():
    return jsonify([])

@app.route('/api/popular_routes')
def get_popular_routes():
    return jsonify([])

@app.route('/api/user_insights')
def get_user_insights():
    return jsonify({})

@app.route('/api/add_favorite', methods=['POST'])
def add_favorite():
    return jsonify({'success': True})

@app.route('/api/preferences', methods=['GET', 'POST'])
def handle_preferences():
    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True)