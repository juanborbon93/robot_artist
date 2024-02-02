from project_init import SharedLogger

log = SharedLogger.get_logger()

from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel,RootModel
from datetime import datetime
from numpy import zeros

DICTATIONS_DIR = Path(__file__).parent / "dictations"
DICTATIONS_DIR.mkdir(exist_ok=True)

class RecordingSetting(BaseModel):
    text:str
    voice:str = "alloy"

    @classmethod
    def parse_settings(cls):
        """Parse settings from command line arguments."""
        from argparse import ArgumentParser
        parser = ArgumentParser()
        parser.add_argument("--text", type=str, default="the quick brown fox jumped over the lazy dogs", help="Text to convert to speech")
        parser.add_argument("--voice", type=str, default="alloy", help="Voice to use for the speech")
        args = parser.parse_args()
        return cls(text=args.text, voice=args.voice)


class Recording(BaseModel):
    settings: RecordingSetting
    filename: Path

    def play(self):
        # Load the audio file
        import sounddevice as sd
        import soundfile as sf
        data, fs = sf.read(self.filename, dtype='float32')
        # play dummy audio to initialize the sound card
        sd.play(zeros(fs), samplerate=fs, blocking=True)
        # Play the audio file
        sd.play(data, fs, blocking=True)

class Recordings(RootModel):
    root: list[Recording]
    
    @classmethod
    def load(cls):
        # dirs under dictations
        Recordings = []
        for dir in [d for d in DICTATIONS_DIR.iterdir() if d.is_dir()]:
            # make sure that there is a settings.json file
            settings_file = dir / "settings.json"
            if not settings_file.exists():
                continue

            with open(settings_file, "r") as f:
                settings = RecordingSetting.model_validate_json(f.read())
            # make sure that there is a recording file
            recording_file = dir / "recording.mp3"
            if recording_file.exists():
                Recordings.append(Recording(settings=settings, filename=recording_file))

        return cls(root=Recordings)
    

    def get_or_create(self, settings: RecordingSetting):
        """Get or create a recording."""
        already_exists = [recording for recording in self.root if recording.settings == settings]
        if already_exists:
            log.info("Recording already exists")
            return already_exists[0]
        else:
            log.info("Creating new recording")
            return self.create(settings)
        
    def create(self, settings: RecordingSetting):
        """Create a new recording."""    # gets OPENAI_API_KEY from your environment variables

        save_dir = DICTATIONS_DIR / datetime.now().isoformat()
        save_dir.mkdir()
        settings_file = save_dir / "settings.json"
        with open(settings_file, "w") as f:
            f.write(settings.model_dump_json())
        filename = save_dir / "recording.mp3"
        tts(settings.text, filename)
        self.root.append(Recording(settings=settings, filename=filename))
        return self.root[-1]

def tts(text,speech_file_path) -> None:
    # Create text-to-speech audio file
    openai = OpenAI()
    with openai.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=text,
    ) as response:
        response.stream_to_file(speech_file_path)

if __name__ == "__main__":
    settings = RecordingSetting.parse_settings()
    recordings = Recordings.load()
    recording = recordings.get_or_create(settings)
    recording.play()
    