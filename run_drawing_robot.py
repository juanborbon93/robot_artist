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
OPTIONAL:
  7. Loading the robot simulation environment.
  8. Creating a robot program using the generated G-code and executing it.
"""

from project_init import SharedLogger, ArgParser

log = SharedLogger.get_logger()

from text_to_speech.dictate import RecordingSetting, Recordings
from speech_to_text.transcribe import record_and_transcribe
from drawing.generate_img import generate_drawing
from drawing.trace_edges import trace_image
from drawing.canvas_scale import scale_contours_to_canvas
from drawing.gcode import GcodeGenerator
from enum import Enum


class MODE(Enum):
    ROBODK = "robodk"
    OCTOPRINT = "octoprint"
    NO_ROBOT = "no_robot"


recordings = Recordings.load()


def play_audio_promp(text):
    log.info("Playing audio prompt...")
    settings = RecordingSetting(text=text)
    recording = recordings.get_or_create(settings)
    recording.play()


if __name__ == "__main__":
    from argparse import ArgumentParser, RawDescriptionHelpFormatter

    parser = ArgParser(description=__doc__)
    parser.add_argument(
        "--mode",
        type=MODE,
        choices=list(MODE),
        default=MODE.NO_ROBOT,
        help="Mode to run the drawing robot in",
    )
    parser.add_argument(
        "--human-prompt",
        type=str,
        default=None,
        help="Prompt for the drawing (will use audio prompt if not provided)",
    )
    parser.add_argument(
        "--img-path", help="Use existing image instead of generating one", type=str
    )
    parser.add_argument(
        "--record-robodk-video",
        action="store_true",
        help="Record the drawing process (only works with ROBODK mode)",
    )

    

    args = parser.parse_args()
    if not args.img_path:
        play_audio = args.human_prompt is None
        if args.human_prompt:
            human_prompt = args.human_prompt
        else:
            play_audio_promp(
                text="Hello! I am a drawing robot. What would you like me to draw?"
            )
            human_prompt = record_and_transcribe(10, "response.wav")
            log.info(f"Transcription:\n{human_prompt}")
            play_audio_promp(
                text="Great! I will draw that for you. Please wait a moment."
            )

        img = generate_drawing(human_prompt)
        img.show()
        continue_drawing = input("Would you like to continue drawing? (y/n)")
        if continue_drawing.lower() != "y":
            log.info("User chose not to continue drawing. Exiting...")
            exit()
    else:
        from PIL import Image

        img = Image.open(args.img_path)

    contours = trace_image(img)
    canvas_contours = scale_contours_to_canvas(contours)
    gcode_generator = GcodeGenerator.load()
    gcode_file = gcode_generator.make_gcode_from_countours(canvas_contours)

    if args.mode == MODE.NO_ROBOT:
        log.info(f"Skipping execution on robot as mode is set to NO_ROBOT")

    elif args.mode == MODE.OCTOPRINT:
        from octoprint import upload_file

        upload_file(str(gcode_file.absolute()))

    elif args.mode == MODE.ROBODK:
        from simulation.launch_rdk import load_station
        from simulation.robot_program import make_robot_program, draw_on_canvas

        rdk = load_station()
        if play_audio:
            play_audio_promp(text="Drawing is ready. I will start drawing now.")
        recorder = None

        prog = make_robot_program(gcode_file, rdk)
        if args.record_robodk_video:
            from recorder import RDKCameraRecorder

            recorder = RDKCameraRecorder("Camera", rdk, 5.0)
            input("Press Enter to start recording")
            recorder.start()
        draw_on_canvas(rdk, prog)
        if recorder:
            recorder.stop()
