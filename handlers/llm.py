import os
import requests
import re
from dotenv import load_dotenv
import pandas as pd
from difflib import get_close_matches

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
MODEL = 'gemini-2.0-pro'

PLAIN_INSTRUCTION_EN = (
    "Respond in plain text only. Do not use Markdown, bullet points, numbering, or any special formatting. "
    "Provide a coherent, uninterrupted narrative. Avoid using asterisks, hashtags, or any markdown symbols."
)
PLAIN_INSTRUCTION_HI = (
    "केवल सादा पाठ में उत्तर दें। Markdown, बुलेट पॉइंट्स, नंबरिंग या किसी भी विशेष स्वरूपण का उपयोग न करें। "
    "एक सुगठित, निर्बाध वर्णनात्मक उत्तर प्रदान करें।"
)

# Load station names (English and Hindi if available)
GTFS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gtfs')
stops_path = os.path.join(GTFS_PATH, 'stops.txt')
if os.path.exists(stops_path):
    stops_df = pd.read_csv(stops_path)
    STATION_NAMES = stops_df['stop_name'].dropna().astype(str).tolist()
else:
    STATION_NAMES = []

# Optionally, add Hindi station names if you have a column for them
# For now, we use only English names, but you can extend this

# Fuzzy match station name
def fuzzy_find_station(query, lang='en'):
    matches = get_close_matches(query, STATION_NAMES, n=1, cutoff=0.7)
    return matches[0] if matches else None

def clean_text_for_tts(text: str) -> str:
    """Clean text by removing all markdown formatting and special characters"""
    if not text:
        return ""
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'#+\s*(.*)', r'\1', text)      # Headers
    text = re.sub(r'`(.*?)`', r'\1', text)        # Code
    text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
    
    # Remove bullet points and numbering
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines to single
    text = re.sub(r' +', ' ', text)         # Multiple spaces to single
    text = text.strip()
    
    # Remove any remaining special characters that might cause TTS issues
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)]', '', text)
    
    return text

def llm_generate(user_query, lang='en'):
    if lang == 'hi':
        prompt = (
            f"{PLAIN_INSTRUCTION_HI} आप एक दिल्ली मेट्रो यात्रा सहायक हैं। उपयोगकर्ता ने कहा: '{user_query}'. "
            "कृपया स्टेशनों के नाम, लाइनों का विवरण, इंटरचेंज, प्लेटफार्म जानकारी, दिशा, अनुमानित यात्रा समय और किराया सहित एक विस्तृत मार्गदर्शन हिंदी में दें।"
        )
    else:
        prompt = (
            f"{PLAIN_INSTRUCTION_EN} You are a Delhi Metro travel assistant. The user said: '{user_query}'. "
            "Please provide a detailed route including station names, line names, interchanges, platform info, direction, approximate travel time, and fare in English. "
            "Use natural, conversational language without any formatting symbols."
        )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=payload)
    if response.ok:
        try:
            text = response.json()['candidates'][0]['content']['parts'][0]['text']
            # Clean the text for TTS
            cleaned_text = clean_text_for_tts(text)
            return cleaned_text
        except Exception:
            return 'Error parsing LLM response'
    return 'LLM API error'

def extract_stations(user_query, lang='en'):
    """Extract station names from user query using fuzzy matching"""
    # Try to find two station names in the query
    found = []
    for name in STATION_NAMES:
        if name.lower() in user_query.lower():
            found.append(name)
    # If not found, try fuzzy matching on each word
    if len(found) < 2:
        words = user_query.split()
        for word in words:
            match = fuzzy_find_station(word, lang=lang)
            if match and match not in found:
                found.append(match)
            if len(found) == 2:
                break
    return (found[0], found[1]) if len(found) >= 2 else (None, None)

def clarification_prompt(lang='en', from_station=None, to_station=None):
    if lang == 'hi':
        msg = "माफ़ कीजिए, कृपया पुष्टि करें:\n"
        if not from_station:
            msg += "- आप यात्रा की शुरुआत किस स्टेशन से कर रहे हैं?\n"
        if not to_station:
            msg += "- आप किस स्टेशन जाना चाहते हैं?\n"
        msg += "\nपुष्टि मिलते ही मैं आपको सबसे अच्छा मार्ग, अनुमानित समय और किराया बता दूंगा।"
        return msg
    else:
        msg = "Sorry, please confirm:\n"
        if not from_station:
            msg += "- Which station are you starting from?\n"
        if not to_station:
            msg += "- Which station are you going to?\n"
        msg += "\nOnce you confirm, I can provide the best route, estimated time, and fare."
        return msg
