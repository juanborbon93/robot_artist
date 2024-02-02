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
    play_audio_promp(text = "Hello! I am a drawing robot. What would you like me to draw?")
    transcription = record_and_transcribe(10, "response.wav")
    log.info(f"Transcription:\n{transcription}")
    play_audio_promp(text = "Great! I will draw that for you. Please wait a moment.")
    img = generate_drawing(transcription)
    img.show()
    contours = trace_image(img)
    canvas_contours = scale_contours_to_canvas(contours)
    gcode_file = make_gcode(canvas_contours)
    rdk = load_station()
    play_audio_promp(text = "Drawing is ready. I will start drawing now.")
    make_robot_program(gcode_file, rdk, run = True)




