""" make gcode from contours """

from pathlib import Path
from datetime import datetime

def make_gcode(contours, feedrate = 30000, pen_up = 50, pen_down = 0, min_step_mm = 0.5):
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
        commands.append(f"G0 Z{pen_up}")
        commands.append(f"G0 X{round(contour[0][0][0],3)} Y{round(contour[0][0][1],3)}")
        commands.append(f"G0 Z{pen_down}")
        last_pos = None
        for point in contour:
            if last_pos is None:
                last_pos = point[0]
            if ((point[0][0] - last_pos[0])**2 + (point[0][1] - last_pos[1])**2)**0.5 > min_step_mm:
                commands.append(f"G1 X{round(point[0][0],3)} Y{-round(point[0][1],3)}")
                last_pos = point[0]            
        commands.append(f"G0 Z{pen_up}")

    save_dir = Path(__file__).parent / "gcode"
    save_dir.mkdir(exist_ok=True)
    filepath = save_dir / f"{datetime.now().isoformat()}.nc"
    with open(filepath, "w") as f:
        f.write("\n".join(commands))
    return filepath