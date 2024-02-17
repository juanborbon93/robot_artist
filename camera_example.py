# Connect to the running instance of RoboDK (make sure it's already running)
from project_init import SharedLogger

logging = SharedLogger.get_logger()
import time
from robolink import Robolink

logging.info("Connecting...")
RDK = Robolink()
RDK.Command("API_NODELAY", "1")
RDK.Connect()
logging.info("Connected...")

CAM_NAME = "Camera"
static_camera = RDK.Item(CAM_NAME)

# Optimal settings: undocked, minimized, fixed sensor size
RDK.Cam2D_SetParams("SIZE=640x480 WINDOWFIXED MINIMIZED", static_camera)
static_camera.setParam("Open", 1)

for i in range(1, 20):
    start_time = time.time()
    logging.info("Taking snapshot...")
    bytes_img = RDK.Cam2D_Snapshot("test.png", static_camera)
    end_time = time.time()
    logging.info("Snapshot took %.6f seconds", (end_time - start_time))
