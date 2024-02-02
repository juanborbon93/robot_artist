"""
This script runs a drawing robot that takes user input, generates a drawing based on the input,
and then uses a robot to draw the generated image. The script uses audio prompts for user interaction,
speech-to-text transcription for input, and various drawing and simulation modules for generating and
executing the drawing.

The main steps of the script include:
1. Playing an audio prompt to ask the user what they would like the robot to draw.
2. Recording and transcribing the user's response (or using a provided prompt).
3. Generating a drawing based on the transcription.
4. Tracing the edges of the generated image.
5. Scaling the contours of the traced image to fit a canvas.
6. Generating G-code instructions for the robot based on the scaled contours.
7. Loading the robot simulation environment.
8. Creating a robot program using the generated G-code and executing it.
"""

from project_init import SharedLogger

log = SharedLogger.get_logger()

from text_to_speech.dictate import RecordingSetting, Recordings
from speech_to_text.transcribe import record_and_transcribe
from drawing.generate_img import generate_drawing
from drawing.trace_edges import trace_image
from drawing.canvas_scale import scale_contours_to_canvas
from drawing.gcode import make_gcode
from simulation.launch_rdk import load_station
from simulation.robot_program import make_robot_program

recordings = Recordings.load()

def play_audio_promp(text):
    log.info("Playing audio prompt...")
    settings = RecordingSetting(text=text)
    recording = recordings.get_or_create(settings)
    recording.play()

if __name__ == "__main__":
    from argparse import ArgumentParser, RawDescriptionHelpFormatter
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("--human-prompt", type=str, default=None, help="Prompt for the drawing (will use audio prompt if not provided)")
    args = parser.parse_args()

    
    if args.human_prompt:
        human_prompt = args.human_prompt
    else:
        play_audio_promp(text = "Hello! I am a drawing robot. What would you like me to draw?")
        human_prompt = record_and_transcribe(10, "response.wav")
        log.info(f"Transcription:\n{human_prompt}")
        play_audio_promp(text = "Great! I will draw that for you. Please wait a moment.")
    
    img = generate_drawing(human_prompt)
    img.show()
    contours = trace_image(img)
    canvas_contours = scale_contours_to_canvas(contours)
    gcode_file = make_gcode(canvas_contours)
    rdk = load_station()
    play_audio_promp(text = "Drawing is ready. I will start drawing now.")
    make_robot_program(gcode_file, rdk, run = True)




