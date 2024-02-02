"""Loads fresh robodk station"""
from project_init import SharedLogger

log = SharedLogger.get_logger()

from robodk.robolink import Robolink
from pathlib import Path

STATION_PATH = Path(__file__).parent / "main_station.rdk"

assert STATION_PATH.exists(), f"Station file not found at {STATION_PATH.absolute()}"

def load_station():
    """Loads the station from the file"""
    rdk = Robolink()
    rdk.Command("API_NODELAY","1")
    active_station = rdk.ActiveStation()
    if active_station.Valid():
        log.info("Closing active station")
        rdk.CloseStation()
    log.info(f"Loading station from {STATION_PATH.absolute()}")
    rdk.AddFile(str(STATION_PATH.absolute()))
    return rdk

if __name__ == "__main__":
    load_station()

