""" make gcode from contours """

from project_init import SharedLogger, LOG_DIR

log = SharedLogger.get_logger()

from scipy.ndimage import gaussian_filter1d
from settings.settings_base import BaseSettingsModel
from typing import Union

class GcodeGenerator(BaseSettingsModel):
    """Gcode settings:
    
    feedrate_mm_per_min: int = 30000
        - The feedrate in millimeters per minute. It determines the speed at which the robot moves.

    pen_up_mm: int = 25
        - The height in millimeters at which the pen is lifted when not drawing.

    pen_down_mm: int = 0
        - The height in millimeters at which the pen is lowered when drawing.

    min_step_mm: float = 0.2
        - The minimum distance in millimeters between two consecutive points on the contour. If the distance is greater than this value, the robot will move to the next point.

    xy_offset_mm: tuple[float,float] = (0.0, 0.0)
        - The offset in millimeters in the X and Y directions. It allows you to adjust the position of the drawing on the canvas.

    pen_down_command: str = None
        - The Gcode command to execute when the pen is lowered. It can be a string representing a valid Gcode command or an empty string if no command is needed.

    pen_up_command: str = None
        - The Gcode command to execute when the pen is lifted. It can be a string representing a valid Gcode command or an empty string if no command is needed.

    start_command: str = None
        - The Gcode command to execute at the start of the program. It can be a string representing a valid Gcode command or an empty string if no command is needed.

    end_command: str = None
        - The Gcode command to execute at the end of the program. It can be a string representing a valid Gcode command or an empty string if no command is needed.
    """

    feedrate_mm_per_min: int = 30000
    pen_up_mm: int = 25
    pen_down_mm: int = 0
    min_step_mm: float = 0.2
    xy_offset_mm: tuple[float,float] = (0.0, 0.0)
    pen_down_command: str = ""
    pen_up_command: str = "" 
    start_command: str = "G28\nG21\nG90"
    end_command: str = ""

    def make_gcode_from_countours(self,contours):
        """Makes gcode from a list of contours and writes it to a file."""
        commands = [
            f"G0 F{self.feedrate_mm_per_min}",
        ]

        # cluster based on the starting point coordinate of each contour

        for contour in contours:
            last_pos_x, last_pos_y = None, None
            first_contact_command = None
            first_approach_command = None
            # apply a 1D gaussian filter to the contour
            y_points = [-point[0][1] + self.xy_offset_mm[1] for point in contour]
            x_points = [point[0][0] + self.xy_offset_mm[0] for point in contour]
            x_points = gaussian_filter1d(x_points, 1, radius=3)
            y_points = gaussian_filter1d(y_points, 1, radius=3)
            # draw on canvas
            for idx, (point_x, point_y) in enumerate(zip(x_points, y_points)):
                if idx == 0:
                    # start contour
                    first_approach_command = (
                        f"G0 X{round(point_x,3)} Y{round(point_y,3)} Z{self.pen_up_mm}"
                    )
                    commands.append(first_approach_command)
                    first_contact_command = (
                        f"G1 X{round(point_x,3)} Y{round(point_y,3)} Z{self.pen_down_mm}"
                    )
                    commands.append(first_contact_command)
                    if self.pen_down_command:
                        commands.append(self.pen_down_command)

                if last_pos_x is None and last_pos_y is None:
                    last_pos_x, last_pos_y = point_x, point_y

                if (
                    (point_x - last_pos_x) ** 2 + (point_y - last_pos_y) ** 2
                ) ** 0.5 > self.min_step_mm:
                    commands.append(
                        f"G1 X{round(point_x,3)} Y{round(point_y,3)} Z{self.pen_down_mm}"
                    )
                    last_pos_x, last_pos_y = point_x, point_y

                if idx == len(contour) - 1:
                    commands.append(first_contact_command)
                    commands.append(first_approach_command)
                    if self.pen_up_command:
                        commands.append(self.pen_up_command)

        filepath = LOG_DIR / "drawing_toolpath.gcode"
        gcode_str = self.start_command + "\n" + "\n".join(commands) + "\n" + self.end_command
        with open(filepath, "w") as f:
            f.write(gcode_str)
        log.info(f"Saved gcode to {filepath}")
        return filepath
