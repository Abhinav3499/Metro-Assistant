from flask import Flask, render_template, request, jsonify, session
import os, time, uuid
from handlers.audio import record_audio
from handlers.stt import stt_transcribe
from handlers.agent import process_with_agent
from handlers.rag import enhance_response_with_rag
from handlers.database import db
from handlers.tts import tts_synthesize

app = Flask(__name__)
app.secret_key = 'metro_assistant_secret_key'

@app.after_request
def add_no_cache(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    
    # Initialize session if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('index.html', lang=lang)

@app.route('/process', methods=['POST'])
def process_audio():
    start_time = time.time()
    lang = request.args.get('lang', 'en')
    
    # Record audio
    wav_path = record_audio(duration=5)
    transcript = stt_transcribe(wav_path)
    
    if not transcript:
        return jsonify({'error': 'Could not transcribe audio'}), 500
    
    # Process with agentic AI
    try:
        response = process_with_agent(transcript, lang)
        
        # Enhance with RAG
        enhanced_response = enhance_response_with_rag(transcript, response)
        
        # Generate audio
        out_mp3 = os.path.join('static', 'output.mp3')
        if os.path.exists(out_mp3): 
            os.remove(out_mp3)
        tts_synthesize(enhanced_response, lang)
        
        # Save to database
        processing_time = time.time() - start_time
        db.save_conversation(
            session_id=session.get('session_id', 'unknown'),
            user_query=transcript,
            assistant_response=enhanced_response,
            language=lang,
            processing_time=processing_time
        )
        
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
    lang = data.get('lang', 'en')
    
    if not user_query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        # Process with agentic AI
        response = process_with_agent(user_query, lang)
        
        # Enhance with RAG
        enhanced_response = enhance_response_with_rag(user_query, response)
        
        # Save to database
        processing_time = time.time() - start_time
        db.save_conversation(
            session_id=session.get('session_id', 'unknown'),
            user_query=user_query,
            assistant_response=enhanced_response,
            language=lang,
            processing_time=processing_time
        )
        
        return jsonify({
            'response': enhanced_response
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/api/history')
def get_history():
    session_id = session.get('session_id', 'unknown')
    history = db.get_conversation_history(session_id, limit=10)
    return jsonify(history)

@app.route('/api/favorites')
def get_favorites():
    session_id = session.get('session_id', 'unknown')
    favorites = db.get_station_favorites(session_id)
    return jsonify(favorites)

@app.route('/api/popular_routes')
def get_popular_routes():
    routes = db.get_popular_routes(limit=5)
    return jsonify(routes)

@app.route('/api/user_insights')
def get_user_insights():
    session_id = session.get('session_id', 'unknown')
    insights = db.get_user_insights(session_id)
    return jsonify(insights)

@app.route('/api/add_favorite', methods=['POST'])
def add_favorite():
    data = request.get_json()
    station_name = data.get('station_name', '')
    station_code = data.get('station_code', '')
    
    if not station_name:
        return jsonify({'error': 'Station name required'}), 400
    
    session_id = session.get('session_id', 'unknown')
    db.add_station_favorite(session_id, station_name, station_code)
    
    return jsonify({'success': True})

@app.route('/api/preferences', methods=['GET', 'POST'])
def handle_preferences():
    session_id = session.get('session_id', 'unknown')
    
    if request.method == 'GET':
        preferences = db.get_user_preferences(session_id)
        return jsonify(preferences)
    
    elif request.method == 'POST':
        data = request.get_json()
        db.save_user_preferences(session_id, data)
        return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)