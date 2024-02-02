from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel

class RecordingSetting(BaseModel):
    text:str
# gets OPENAI_API_KEY from your environment variables
openai = OpenAI()

speech_file_path = Path(__file__).parent / "speech.mp3"


def tts(text = "the quick brown fox jumped over the lazy dogs") -> None:
    # Create text-to-speech audio file
    with openai.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=text,
    ) as response:
        response.stream_to_file(speech_file_path)

if __name__ == "__main__":
    tts()