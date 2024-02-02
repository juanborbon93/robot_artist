from project_init import SharedLogger
log = SharedLogger.get_logger()
import sounddevice as sd
import scipy.io.wavfile as wav
import whisper
from pathlib import Path

SAVE_DIR = Path(__file__).parent / "recordings"
SAVE_DIR.mkdir(exist_ok=True)

# Function to record audio
def record_audio(duration, fs = 44100):
    log.info("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    return audio

# Function to save audio as WAV
def save_audio(audio, fs = 44100, filename='recording.wav'):
    wav.write(filename, fs, audio)
    log.info(f"Audio saved as {filename}")

# Function to transcribe audio using Whisper
def transcribe_audio(filename):
    model = whisper.load_model("tiny.en")
    result = model.transcribe(str(filename))
    return result['text']

def record_and_transcribe(duration, filename, keep_file = False):
    if not isinstance(filename, Path):
        filename = SAVE_DIR / filename
    audio = record_audio(duration)
    save_audio(audio, filename=filename)
    transcription = transcribe_audio(filename)
    if not keep_file:
        filename.unlink()
    return transcription

# Main process
if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--duration", type=int, default=10, help="Duration of recording in seconds")
    parser.add_argument("--filename", type=str, default="recording.wav", help="Filename to save the recording")
    parser.add_argument("--keep_file", action="store_true", help="Keep the recording file after transcription")
    args = parser.parse_args()

 
    audio_file = SAVE_DIR / args.filename
    
    trancription = record_and_transcribe(args.duration, audio_file, keep_file = args.keep_file)
    log.info("Transcription:\n",trancription)
