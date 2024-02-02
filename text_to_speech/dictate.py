"""
This module provides functionality for recording and playing text-to-speech audio files.

It defines the following classes:
- RecordingSetting: Represents the settings for a recording, including the text to convert to speech and the voice to use.
- Recording: Represents a recorded audio file with its corresponding settings.
- Recordings: Represents a collection of recordings.
"""

from project_init import SharedLogger

log = SharedLogger.get_logger()

from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel, RootModel
from datetime import datetime
from numpy import zeros

DICTATIONS_DIR = Path(__file__).parent / "dictations"
DICTATIONS_DIR.mkdir(exist_ok=True)

class RecordingSetting(BaseModel):
    """
    Represents the settings for a recording.

    Attributes:
    - text: The text to convert to speech.
    - voice: The voice to use for the speech. Defaults to "alloy".
    """

    text: str
    voice: str = "alloy"

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
    """
    Represents a recorded audio file with its corresponding settings.

    Attributes:
    - settings: The settings for the recording.
    - filename: The path to the recorded audio file.
    """

    settings: RecordingSetting
    filename: Path

    def play(self):
        """
        Play the recorded audio file.
        """
        # Load the audio file
        import sounddevice as sd
        import soundfile as sf
        data, fs = sf.read(self.filename, dtype='float32')
        # play dummy audio to initialize the sound card
        sd.play(zeros(fs), samplerate=fs, blocking=True)
        # Play the audio file
        sd.play(data, fs, blocking=True)

class Recordings(RootModel):
    """
    Represents a collection of recordings.

    Attributes:
    - root: A list of Recording objects.
    """

    root: list[Recording]
    
    @classmethod
    def load(cls):
        """
        Load the recordings from the dictations directory.

        Returns:
        - An instance of Recordings containing the loaded recordings.
        """
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
        """
        Get or create a recording with the given settings.

        Parameters:
        - settings: The settings for the recording.

        Returns:
        - The existing recording if it already exists, otherwise a new recording.
        """
        already_exists = [recording for recording in self.root if recording.settings == settings]
        if already_exists:
            log.info("Recording already exists")
            return already_exists[0]
        else:
            log.info("Creating new recording")
            return self.create(settings)
        
    def create(self, settings: RecordingSetting):
        """
        Create a new recording with the given settings.

        Parameters:
        - settings: The settings for the recording.

        Returns:
        - The newly created recording.
        """
        # gets OPENAI_API_KEY from your environment variables
        save_dir = DICTATIONS_DIR / datetime.now().isoformat()
        save_dir.mkdir()
        settings_file = save_dir / "settings.json"
        with open(settings_file, "w") as f:
            f.write(settings.model_dump_json())
        filename = save_dir / "recording.mp3"
        tts(settings.text, filename)
        self.root.append(Recording(settings=settings, filename=filename))
        return self.root[-1]

def tts(text, speech_file_path) -> None:
    """
    Create a text-to-speech audio file.

    Parameters:
    - text: The text to convert to speech.
    - speech_file_path: The path to save the audio file.
    """
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
    