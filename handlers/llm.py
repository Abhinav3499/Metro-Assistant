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

# Load station names (English only)
GTFS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gtfs')
stops_path = os.path.join(GTFS_PATH, 'stops.txt')
if os.path.exists(stops_path):
    stops_df = pd.read_csv(stops_path)
    STATION_NAMES = stops_df['stop_name'].dropna().astype(str).tolist()
else:
    STATION_NAMES = []

def fuzzy_find_station(query):
    matches = get_close_matches(query, STATION_NAMES, n=1, cutoff=0.7)
    return matches[0] if matches else None

def clean_text_for_tts(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#+\s*(.*)', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r' +', ' ', text)
    text = text.strip()
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)]', '', text)
    return text

def llm_generate(user_query, lang='en'):
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
            cleaned_text = clean_text_for_tts(text)
            return cleaned_text
        except Exception:
            return 'Error parsing LLM response'
    return 'LLM API error'

def extract_stations(user_query, lang='en'):
    found = []
    for name in STATION_NAMES:
        if name.lower() in user_query.lower():
            found.append(name)
    if len(found) < 2:
        words = user_query.split()
        for word in words:
            match = fuzzy_find_station(word)
            if match and match not in found:
                found.append(match)
            if len(found) == 2:
                break
    return (found[0], found[1]) if len(found) >= 2 else (None, None)

def clarification_prompt(lang='en', from_station=None, to_station=None):
    msg = "Sorry, please confirm:\n"
    if not from_station:
        msg += "- Which station are you starting from?\n"
    if not to_station:
        msg += "- Which station are you going to?\n"
    msg += "\nOnce you confirm, I can provide the best route, estimated time, and fare."
    return msg
