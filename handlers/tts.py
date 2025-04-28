import os
import asyncio
from edge_tts import Communicate

def tts_synthesize(text, lang='en'):
    voice = 'en-IN-PrabhatNeural' if lang == 'en' else 'hi-IN-MadhurNeural'
    output = os.path.join('static', 'output.mp3')
    asyncio.run(Communicate(text=text, voice=voice).save(output))
    return output