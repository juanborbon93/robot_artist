from project_init import SharedLogger

log = SharedLogger.get_logger()

from simulation.launch_rdk import load_station
from robodk import robolink
from typing import Union
from pathlib import Path
from time import sleep

def make_robot_program(gcode_file:Path, rdk:Union[robolink.Robolink,None],run=False):
    """
    Sends gcode to robot
    Args:
        gcode_file: Path
        rdk: robolink.Robolink
    """
    if rdk is None:
        rdk = load_station()

    # create machining project
    millin_project = rdk.Item("drawing", robolink.ITEM_TYPE_PROGRAM)
    if millin_project.Valid():
        millin_project.Delete()
    millin_project = rdk.AddMillingProject("drawing_project")
    prog, status = millin_project.setMillingParameters(ncfile=str(gcode_file.absolute()))
    if run:
        draw_on_canvas(rdk,prog)
    return prog

def draw_on_canvas(rdk,prog):
    """Draws on the canvas"""
    rdk.Spray_Clear()
    rdk.Command("Trace", "Reset")
    rdk.Command("Trace","Off")
    prog.RunProgram()
    tool = 0    # auto detect active tool
    obj = rdk.Item("canvas",robolink.ITEM_TYPE_OBJECT)
    robot = rdk.Item('UR10e', robolink.ITEM_TYPE_ROBOT)
    rdk.Spray_Add(tool, obj, "PROJECT PARTICLE=SPHERE(1.0,8) RAND=0")
    spray_state = robolink.SPRAY_OFF
    log.info("Drawing...")
    log.info("Press CRTL+C to stop drawing")
    try:
        while prog.Busy():
            z_pos = robot.Pose().Pos()[2]
            if z_pos < 0.05:
                if spray_state != robolink.SPRAY_ON:
                    spray_state = robolink.SPRAY_ON
                    rdk.Spray_SetState(robolink.SPRAY_ON)
            else:
                spray_state = robolink.SPRAY_OFF
                rdk.Spray_SetState(spray_state)
            sleep(0.01)
    except KeyboardInterrupt:
        log.info("Drawing stopped")
        rdk.Spray_SetState(robolink.SPRAY_OFF)
        prog.Stop()
        # retract robot
        robot.MoveL(robot.Pose()*robolink.transl(0,0,100))
