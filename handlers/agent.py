import os
import json
import requests
from typing import Dict, List, Any
from dotenv import load_dotenv
from datetime import datetime, timedelta
from handlers.llm import clean_text_for_tts, extract_stations, clarification_prompt

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

class MetroAgent:
    def __init__(self):
        self.conversation_history = []
        self.user_context = {}
        
    def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify user intent and extract relevant information"""
        prompt = f"""
        Analyze this Delhi Metro query and classify the intent:
        Query: "{query}"
        
        Return a JSON with:
        - intent: "route_finding", "schedule", "fare", "station_info", "general_help"
        - entities: {{"from_station": "", "to_station": "", "time": "", "line": ""}}
        - confidence: 0.0-1.0
        - requires_followup: true/false
        """
        
        response = self._call_llm(prompt)
        try:
            return json.loads(response)
        except:
            return {"intent": "route_finding", "entities": {}, "confidence": 0.5, "requires_followup": False}
    
    def plan_actions(self, intent: str, entities: Dict) -> List[Dict]:
        """Plan the sequence of actions needed"""
        actions = []
        
        if intent == "route_finding":
            if not entities.get("from_station") or not entities.get("to_station"):
                actions.append({"action": "clarify_stations", "message": "Please specify your starting and destination stations"})
            else:
                actions.append({"action": "find_route", "from": entities["from_station"], "to": entities["to_station"]})
                actions.append({"action": "calculate_fare", "from": entities["from_station"], "to": entities["to_station"]})
                actions.append({"action": "get_schedule", "from": entities["from_station"], "to": entities["to_station"]})
        
        elif intent == "schedule":
            actions.append({"action": "get_schedule", "station": entities.get("from_station", "")})
        
        elif intent == "fare":
            actions.append({"action": "calculate_fare", "from": entities.get("from_station", ""), "to": entities.get("to_station", "")})
        
        elif intent == "station_info":
            actions.append({"action": "get_station_info", "station": entities.get("from_station", "")})
        
        return actions
    
    def execute_action(self, action: Dict) -> Dict:
        """Execute a specific action"""
        action_type = action["action"]
        
        if action_type == "find_route":
            from handlers.route_finder import find_route
            return find_route(f"from {action['from']} to {action['to']}")
        
        elif action_type == "calculate_fare":
            from handlers.route_finder import calculate_fare
            return calculate_fare(action['from'], action['to'])
        
        elif action_type == "get_schedule":
            from handlers.schedule import get_schedule
            return get_schedule(action.get('from', ''), action.get('to', ''))
        
        elif action_type == "get_station_info":
            from handlers.station_info import get_station_details
            return get_station_details(action['station'])
        
        elif action_type == "clarify_stations":
            # Use improved clarification prompt
            lang = self.user_context.get('lang', 'en') if hasattr(self, 'user_context') else 'en'
            return {"type": "clarification", "message": clarification_prompt(lang, action.get('from'), action.get('to'))}
        
        return {"error": "Unknown action"}
    
    def generate_response(self, query: str, results: List[Dict], lang: str = 'en') -> str:
        """Generate natural language response from action results"""
        context = f"User query: {query}\nResults: {json.dumps(results, indent=2)}"
        
        if lang == 'hi':
            prompt = f"""
            आप दिल्ली मेट्रो सहायक हैं। उपयोगकर्ता का प्रश्न: {query}
            परिणाम: {json.dumps(results, indent=2)}
            
            इन परिणामों को आधार बनाकर एक स्पष्ट, सहायक और विस्तृत उत्तर हिंदी में दें।
            मार्ग, समय, किराया, और अन्य महत्वपूर्ण जानकारी शामिल करें।
            सादा पाठ में उत्तर दें, कोई विशेष स्वरूपण न करें।
            """
        else:
            prompt = f"""
            You are a Delhi Metro assistant. User query: {query}
            Results: {json.dumps(results, indent=2)}
            
            Based on these results, provide a clear, helpful, and detailed response in English.
            Include route information, timing, fare, and other relevant details.
            Use natural, conversational language without any formatting symbols or markdown.
            """
        
        response = self._call_llm(prompt)
        # Clean the response for TTS
        return clean_text_for_tts(response)
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.ok:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
        except:
            pass
        return "I'm sorry, I couldn't process your request at the moment."

def process_with_agent(query: str, lang: str = 'en') -> str:
    """Main function to process queries using the agentic approach"""
    agent = MetroAgent()
    agent.user_context['lang'] = lang
    # Step 1: Classify intent
    intent_data = agent.classify_intent(query)
    
    # Step 2: Plan actions
    actions = agent.plan_actions(intent_data["intent"], intent_data["entities"])
    
    # Step 3: Execute actions
    results = []
    for action in actions:
        result = agent.execute_action(action)
        results.append(result)
    
    # Step 4: Generate response
    response = agent.generate_response(query, results, lang)
    
    # Only enhance with RAG if the response is incomplete or needs additional context
    # For route queries, the base response is usually sufficient
    if intent_data["intent"] == "route_finding" and len(results) > 0:
        # For route finding, the base response is usually complete
        return response
    else:
        # For other queries, enhance with RAG if needed
        from handlers.rag import enhance_response_with_rag
        return enhance_response_with_rag(query, response) 