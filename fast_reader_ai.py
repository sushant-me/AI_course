import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import ollama
import numpy as np
import warnings

# Suppress warnings to keep the terminal clean
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
AUDIO_FILE = "reading_session.wav"
SAMPLE_RATE = 16000
LLM_MODEL = "phi3" # Or "llama3.2" if you downloaded that one

def record_audio():
    print("\n🎤 Recording... Read your 3 pages! (Press Ctrl+C to stop)")
    audio_data = []
    try:
        # Stream audio chunks until interrupted
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
            while True:
                chunk, _ = stream.read(SAMPLE_RATE)
                audio_data.extend(chunk)
    except KeyboardInterrupt:
        print("\n⏹️ Recording stopped. Processing...")
        
    # Save to file
    write(AUDIO_FILE, SAMPLE_RATE, np.array(audio_data))

def transcribe_fast():
    print("⚡ Transcribing audio...")
    # Using the fast, lightweight English model
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    
    # beam_size=5 helps accuracy without sacrificing too much speed
    segments, _ = model.transcribe(AUDIO_FILE, beam_size=5)
    
    transcript = ""
    for segment in segments:
        transcript += segment.text + " "
    
    return transcript.strip()

def summarize_stream(text):
    print("\n🧠 Generating Formal Summary:\n" + "="*50)
    
    # The strict, highly-engineered prompt
    prompt = f"""You are an expert English teacher. Read the text below and provide a structured summary.

CRITICAL RULES:
1. Do NOT just repeat the text. Synthesize the core meaning.
2. Use simple, plain English that is easy for a learner to understand.
3. Do NOT add any extra conversational text, follow-up questions, or greetings.
4. You MUST use the exact headings provided below.

Format your response EXACTLY like this:

**Formal Summary:**
(Write 2 to 3 sentences summarizing the main idea in simple words.)

**Key Points:**
* (Bullet point 1)
* (Bullet point 2)
* (Bullet point 3)

**What You Can Learn From This:**
(Write 1 to 2 sentences explaining the main lesson or practical takeaway from this text.)

Text to summarize: {text}"""
    
    # temperature: 0.0 is the most important part. It stops the AI from hallucinating.
    stream = ollama.chat(
        model=LLM_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
        options={
            'temperature': 0.0, 
            'top_p': 0.9
        }
    )
    
    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)
    print("\n" + "="*50)

# --- EXECUTION PIPELINE ---
if __name__ == "__main__":
    record_audio()
    
    transcript = transcribe_fast()
    
    # Only print a snippet of the transcript so it doesn't flood your screen
    print(f"\n📝 Rough Transcript Captured: {len(transcript)} characters.")
    
    if transcript and len(transcript) > 10:
        summarize_stream(transcript)
    else:
        print("No speech detected or audio was too short. Please try again.")