"""records a video stream from a simulated camera"""
from project_init import SharedLogger
from threading import Thread, Lock
from time import sleep, monotonic
log = SharedLogger.get_logger()

from robodk import robolink
import numpy as np
import cv2
from datetime import datetime
from pathlib import Path

RECORDINGS_DIR = Path(__file__).parent / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True, parents=True)


class RDKCameraRecorder:

    default_fps = 20

    def __init__(
            self,
            camera_name:str,
            rdk:robolink.Robolink,
            timelapse_multiplier:float = 1.0):
        self.camera = rdk.Item(camera_name,robolink.ITEM_TYPE_CAMERA)
        self.rdk = rdk
        # Optimal settings: undocked, minimized, fixed sensor size
        rdk.Cam2D_SetParams("SIZE=640x480 WINDOWFIXED", self.camera)
        assert self.camera.Valid(),"Camera not found"
        self._recording_thread = None
        self._recording_state = False
        self._recording_state_lock = Lock()
        self.frame_delay = timelapse_multiplier / self.default_fps
        log.info("frame delay: %s", self.frame_delay)
        self.camera.setParam('Open', 1)
        sleep(0.25)
    

    def start(self):
        self._recording_thread = Thread(target=self.record)
        self._recording_thread.start()

    def stop(self):
        with self._recording_state_lock:
            self._recording_state = False

    def _get_frame(self):
        img_socket = None
        t0 = monotonic()
        bytes_img = self.rdk.Cam2D_Snapshot('', self.camera)
        if isinstance(bytes_img, bytes) and bytes_img != b'':
            log.info(f"received frame in {monotonic() - t0} seconds")
            nparr = np.frombuffer(bytes_img, np.uint8)
            img_socket = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img_socket

    def _make_video_writer(self):
        # get the frame size
        frame = self._get_frame()
        if frame is None:
            raise Exception("Could not get frame from camera")
        
        height, width, layers = frame.shape
        # create a video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' for MP4 format
        save_file = RECORDINGS_DIR / (datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".mp4")
        writer =  cv2.VideoWriter(str(save_file.absolute()), fourcc, 20.0, (width, height))
        log.info(f"Video writer created. video size: {width}x{height}")
        return writer, save_file
    
    def record(self):
        with self._recording_state_lock:
            self._recording_state = True

        video_writer, save_file = self._make_video_writer()

        log.info("Recording started")
        while True:
            with self._recording_state_lock:
                if not self._recording_state:
                    break
            new_frame = self._get_frame()
            if new_frame is not None:
                video_writer.write(new_frame)
                log.info("Frame written")
                sleep(self.frame_delay)
            else:
                log.warning("Frame not written")
        video_writer.release()
        log.info("Recording stopped")
        log.info("Video saved at %s", save_file.absolute())

if __name__ == "__main__":
    rdk = robolink.Robolink()
    rdk.Command("API_NODELAY","1")
    camera_recorder = RDKCameraRecorder("Camera", rdk, timelapse_multiplier=5.0)
    camera_recorder.start()
    input("Press enter to stop recording")
    camera_recorder.stop()
