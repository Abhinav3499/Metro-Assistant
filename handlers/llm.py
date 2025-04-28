import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
MODEL = 'gemini-2.0-pro'

PLAIN_INSTRUCTION_EN = (
    "Respond in plain text only. Do not use Markdown, bullet points, numbering, or any special formatting. "
    "Provide a coherent, uninterrupted narrative."
)
PLAIN_INSTRUCTION_HI = (
    "केवल सादा पाठ में उत्तर दें। Markdown, बुलेट पॉइंट्स, नंबरिंग या किसी भी विशेष स्वरूपण का उपयोग न करें। "
    "एक सुगठित, निर्बाध वर्णनात्मक उत्तर प्रदान करें।"
)

def llm_generate(user_query, lang='en'):
    if lang == 'hi':
        prompt = (
            f"{PLAIN_INSTRUCTION_HI} आप एक दिल्ली मेट्रो यात्रा सहायक हैं। उपयोगकर्ता ने कहा: '{user_query}'. "
            "कृपया स्टेशनों के नाम, लाइनों का विवरण, इंटरचेंज, प्लेटफार्म जानकारी, दिशा, अनुमानित यात्रा समय और किराया सहित एक विस्तृत मार्गदर्शन हिंदी में दें।"
        )
    else:
        prompt = (
            f"{PLAIN_INSTRUCTION_EN} You are a Delhi Metro travel assistant. The user said: '{user_query}'. "
            "Please provide a detailed route including station names, line names, interchanges, platform info, direction, approximate travel time, and fare in English."
        )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=payload)
    if response.ok:
        try:
            text = response.json()['candidates'][0]['content']['parts'][0]['text']

            return text.replace('#', '').replace('*', '').strip()
        except Exception:
            return 'Error parsing LLM response'
    return 'LLM API error'
