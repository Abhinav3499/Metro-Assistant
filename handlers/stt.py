import speech_recognition as sr

def stt_transcribe(wav_path):
    r = sr.Recognizer()
    with sr.AudioFile(wav_path) as src:
        audio = r.record(src)
    try:
        return r.recognize_google(audio, language='en-IN')
    except Exception:
        return None