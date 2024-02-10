""" make gcode from contours """
from project_init import SharedLogger, LOG_DIR

log = SharedLogger.get_logger()

from argparse import ArgumentParser
from enum import Enum, auto
from scipy.ndimage import gaussian_filter1d


class MachineType(Enum):
    """Machine types"""
    PEN_PLOTTER_3D = auto()
    # PRINTER_3D = auto() # not implemented yet

def add_motion_arguments(parser: ArgumentParser)->None:
    """Add motion arguments to the parser."""
    parser.add_argument("--feedrate", type=int, default=30000, help="Feedrate in mm/min")
    parser.add_argument("--pen-up", type=int, default=50, help="Pen up position in mm")
    parser.add_argument("--pen-down", type=int, default=0, help="Pen down position in mm")
    parser.add_argument("--min-step-mm", type=float, default=0.2, help="Minimum step in mm")
    parser.add_argument("--machine-type", type=MachineType, default=MachineType.PEN_PLOTTER_3D, help="Machine type")


    

def make_gcode(
        contours, 
        feedrate = 30000, 
        pen_up = 50, 
        pen_down = 0, 
        min_step_mm = 0.2,
        machine_type = MachineType.PEN_PLOTTER_3D):
    """
    Makes gcode from a list of contours and writes it to a file.
    Args:
        contours: list of lists of points
        filename: str
        feedrate: int (mm/min)
        pen_up: int (mm)
        pen_down: int (mm)
        min_step_mm: float (mm)
    """
    commands = [
        f"G21 ; Set units to mm",
        f"G90 ; Absolute positioning",
        f"G0 F{feedrate}",
    ]
    for contour in contours:
        last_pos_x,last_pos_y = None, None
        first_contact_command = None
        first_approach_command = None
        # apply a 1D gaussian filter to the contour
        y_points = [point[0][1] for point in contour]
        x_points = [point[0][0] for point in contour]
        x_points = gaussian_filter1d(x_points,1,radius=3)
        y_points = gaussian_filter1d(y_points,1,radius=3)
        # draw on canvas
        for idx,(point_x, point_y) in enumerate(zip(x_points,y_points)):
            if idx == 0:
                # start contour
                first_approach_command = f"G0 X{round(point_x,3)} Y{-round(point_y,3)} Z{pen_up}"
                commands.append(first_approach_command)
                first_contact_command = f"G1 X{round(point_x,3)} Y{-round(point_y,3)} Z{pen_down}"
                commands.append(first_contact_command)

            if last_pos_x is None and last_pos_y is None:
                last_pos_x,last_pos_y = point_x, point_y
                
            if ((point_x - last_pos_x)**2 + (point_y - last_pos_y)**2)**0.5 > min_step_mm:
                commands.append(f"G1 X{round(point_x,3)} Y{-round(point_y,3)} Z{pen_down}")
                last_pos_x,last_pos_y = point_x, point_y
            
            if idx == len(contour) - 1:
                commands.append(first_contact_command)
                commands.append(first_approach_command)
                


    filepath = LOG_DIR / "drawing_toolpath.nc"
    with open(filepath, "w") as f:
        f.write("\n".join(commands))
    log.info(f"Saved gcode to {filepath}")
    return filepath