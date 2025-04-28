# handlers/audio.py
import sounddevice as sd
from scipy.io.wavfile import write
import os

def record_audio(filename='temp.wav', duration=5, sample_rate=44100):
    os.makedirs('recordings', exist_ok=True)
    path = os.path.join('recordings', filename)
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    write(path, sample_rate, audio)
    return path