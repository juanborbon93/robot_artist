"""
This script provides functions to record audio, save it as a WAV file, 
and transcribe the audio using the OpenAI Whisper library.
"""

from project_init import SharedLogger
log = SharedLogger.get_logger()
import sounddevice as sd
import scipy.io.wavfile as wav
import whisper
from pathlib import Path

SAVE_DIR = Path(__file__).parent / "recordings"
SAVE_DIR.mkdir(exist_ok=True)

def record_audio(duration, fs = 44100):
    """
    Records audio for a specified duration.

    Parameters:
    - duration (int): The duration of the recording in seconds.
    - fs (int): The sample rate of the audio (default: 44100).

    Returns:
    - audio (ndarray): The recorded audio as a NumPy array.
    """
    log.info("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    return audio

def save_audio(audio, fs = 44100, filename='recording.wav'):
    """
    Saves the audio as a WAV file.

    Parameters:
    - audio (ndarray): The audio to be saved.
    - fs (int): The sample rate of the audio (default: 44100).
    - filename (str): The name of the file to save the audio (default: 'recording.wav').
    """
    wav.write(filename, fs, audio)
    log.info(f"Audio saved as {filename}")

def transcribe_audio(filename):
    """
    Transcribes the audio using the Whisper library.

    Parameters:
    - filename (str or Path): The path to the audio file.

    Returns:
    - transcription (str): The transcribed text.
    """
    model = whisper.load_model("tiny.en")
    result = model.transcribe(str(filename))
    return result['text']

def record_and_transcribe(duration, filename, keep_file = False):
    """
    Records audio, saves it as a WAV file, and transcribes the audio.

    Parameters:
    - duration (int): The duration of the recording in seconds.
    - filename (str or Path): The name or path of the file to save the recording.
    - keep_file (bool): Whether to keep the recording file after transcription (default: False).

    Returns:
    - transcription (str): The transcribed text.
    """
    if not isinstance(filename, Path):
        filename = SAVE_DIR / filename
    audio = record_audio(duration)
    save_audio(audio, filename=filename)
    transcription = transcribe_audio(filename)
    if not keep_file:
        filename.unlink()
    return transcription

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
