import gradio as gr
from handlers.audio import record_audio
from handlers.stt import stt_transcribe
from handlers.route_finder import find_route
from handlers.llm import llm_generate
from handlers.tts import tts_synthesize


def process_audio(lang):
    wav_path = record_audio(duration=5)
    transcript = stt_transcribe(wav_path)
    route_data = find_route(transcript)
    reply = llm_generate(transcript, route_data, lang)
    audio_file = tts_synthesize(reply, lang)
    return reply, audio_file

with gr.Blocks() as gradio_app:
    gr.Markdown("**AI Delhi Metro Assistant**")
    lang_input = gr.Radio(['en', 'hi'], label='Language', value='en')
    btn = gr.Button('Record & Get Route')
    output_text = gr.Textbox(label='Response')
    output_audio = gr.Audio(label='Audio', interactive=False)
    btn.click(fn=process_audio, inputs=[lang_input], outputs=[output_text, output_audio])
