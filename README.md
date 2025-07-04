# �� AI Metro Assistant

A comprehensive Delhi Metro assistant with **Agentic AI**, **RAG (Retrieval-Augmented Generation)**, and **modern UI**.

## ✨ **Features**

### 🤖 **Agentic AI**
- **Intent Classification**: Automatically detects user intent (route finding, schedule, fare, station info)
- **Multi-step Planning**: Breaks complex queries into actionable steps
- **Context Awareness**: Maintains conversation context and user preferences
- **Intelligent Routing**: Provides multiple route options with detailed analysis

### 🔍 **RAG (Retrieval-Augmented Generation)**
- **Knowledge Base**: Built from GTFS data with 264+ stations and 8 metro lines
- **Semantic Search**: Uses TF-IDF and cosine similarity for relevant information retrieval
- **Enhanced Responses**: Combines LLM responses with real metro data
- **Dynamic Updates**: Can be updated with new GTFS data

### 🎨 **Modern UI**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Chat Interface**: Real-time conversation with voice and text input
- **Sidebar Panels**: History, favorites, and popular routes (static data)
- **Settings Modal**: User preferences and accessibility options
- **Toast Notifications**: Real-time feedback and error messages

### 📊 **Enhanced Features**
- **Real-time Schedules**: Live train timings and frequency
- **Detailed Station Info**: Facilities, accessibility, nearby stations
- **Multiple Route Options**: Direct and interchange routes
- **Smart Fare Calculation**: Distance-based pricing with smart card discounts
- **Accessibility Support**: Wheelchair access, audio signals, tactile paths

## 🚀 **Quick Start**

### Prerequisites
- Python 3.8+
- Microphone access (for voice input)
- Internet connection (for LLM API)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Metro-Assistant
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
```

4. **Run the application**
```bash
python app.py
```

5. **Open in browser**
```
http://localhost:5000
```

## 📁 **Project Structure**

```
Metro-Assistant/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── handlers/
│   ├── agent.py          # Agentic AI implementation
│   ├── rag.py            # RAG system
│   ├── route_finder.py   # Enhanced route finding
│   ├── schedule.py       # Real-time schedules
│   ├── station_info.py   # Station details
│   ├── audio.py          # Audio recording
│   ├── stt.py           # Speech-to-text
│   ├── tts.py           # Text-to-speech
│   └── llm.py           # LLM integration
├── gtfs/                 # GTFS data files
│   ├── agency.txt
│   ├── calendar.txt
│   ├── routes.txt
│   ├── shapes.txt
│   ├── stops.txt
│   ├── stop_times.txt
│   └── trips.txt
├── static/               # Static assets
│   ├── style.css         # Modern CSS
│   ├── mic.png
│   └── output.mp3
├── templates/            # HTML templates
│   └── index.html        # Main UI
└── recordings/           # Temporary audio files
```

## 🔧 **Configuration**

### Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### GTFS Data
The application includes GTFS data for Delhi Metro. To update with newer data:
1. Download latest GTFS data from Delhi Metro
2. Replace files in the `gtfs/` directory
3. Restart the application

## 🎯 **Usage Examples**

### Voice Commands
- "How do I get from Rajiv Chowk to Connaught Place?"
- "What's the fare from Airport to Central Secretariat?"
- "Show me the schedule for Kashmere Gate station"
- "Tell me about the facilities at Rajiv Chowk"

### Text Queries
- Route planning with multiple options
- Real-time schedule information
- Station facilities and accessibility
- Fare calculation with smart card discounts

## 🛠 **API Endpoints**

### Core Endpoints
- `GET /` - Main application interface
- `POST /process` - Process voice input
- `POST /process_text` - Process text input

### Static Data Endpoints
- `GET /api/history` - Get conversation history (empty)
- `GET /api/favorites` - Get favorite stations (empty)
- `GET /api/popular_routes` - Get popular routes (empty)
- `GET /api/user_insights` - Get user analytics (empty)
- `POST /api/add_favorite` - Add station to favorites (no-op)
- `GET/POST /api/preferences` - User preferences (empty)

## 🔍 **Features in Detail**

### Agentic AI System
```python
# Intent classification
intent = agent.classify_intent("How do I get to Connaught Place?")

# Multi-step planning
actions = agent.plan_actions(intent, entities)

# Execute actions
results = agent.execute_action(action)
```

### RAG System
```python
# Search knowledge base
relevant_info = rag.search("Rajiv Chowk station facilities")

# Enhance response
enhanced_response = enhance_response_with_rag(query, base_response)
```

## 🎨 **UI Components**

### Chat Interface
- Real-time message display
- Voice and text input
- Audio playback
- Message timestamps

### Sidebar Panels
- **Recent Queries**: Empty state (no database)
- **Favorite Stations**: Empty state (no database)
- **Popular Routes**: Empty state (no database)

### Info Sidebar
- **Quick Info**: Operating hours, fare range, metro lines
- **Tips**: Smart card usage, peak hours, platform info

## 🔧 **Development**

### Adding New Features
1. Create handler in `handlers/` directory
2. Add route in `app.py`
3. Update UI in `templates/index.html`
4. Add styles in `static/style.css`

## 🚀 **Deployment**

### Local Development
```bash
python app.py
```

### Production Deployment
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using Docker
docker build -t metro-assistant .
docker run -p 5000:5000 metro-assistant
```

## 📊 **Performance**

### Optimization Features
- **Caching**: GTFS data loaded once at startup
- **Async Processing**: Non-blocking audio processing
- **Memory Efficient**: No database overhead

### Monitoring
- Processing time tracking
- Error logging

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgments**

- Delhi Metro Rail Corporation for GTFS data
- Google Gemini API for LLM capabilities
- Flask community for web framework
- Font Awesome for icons

## 📞 **Support**

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code comments

---

**Made with ❤️ for Delhi Metro commuters** 