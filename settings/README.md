# Settings management
This module makes it easy to define and use different configurations from json files.
This is useful for definining configurations that can work with various drawing machines (3D printers, industrial robots, other CNC machines).
**You need to modify or copy the default settings to include your open_ai_api_key for the image generation step to work**
## Usage
To define a new configuration, copy the `settings_files/default.json` under the same directory. Example:
```
cp settings/settings_files/default.json settings/settings_files/ender3.json
```
You can then open the `ender3.json` file and configure it to work with the 3D printer. Example:
```json
{
    "ImageGenerationSettings": {
        "open_ai_api_key": "*****"
    },
    "CanvasScaleSettings": {
        "canvas_width_mm": 100.0,
        "canvas_height_mm": 100.0,
        "margin_mm": 10.0,
        "small_area_cutoff_sqr_mm": null
    },
    "GcodeGenerator": {
        "feedrate_mm_per_min": 30000,
        "pen_up_mm": 25,
        "pen_down_mm": 0,
        "min_step_mm": 0.2,
        "xy_offset_mm": [
            160.0,
            160.0
        ],
        "pen_down_command": "",
        "pen_up_command": "",
        "start_command": "G28\nG21\nG90",
        "end_command": ""
    },
    "OctoprintSettings": {
        "octoprint_api_key": "*****",
        "octoprint_base_url": "http://3dprinter/"
    }
}
```
Now when you call the main entrypoint, you can specify the settings name as:
```bash
python3 run_drawing_robot.py --settings-name ender3
```
## settings_base.py
Implements BaseSettingsModel, a base class for settings models.
This class can be imported into other modules to create settings models.
By calling the load method, the settings are loaded from a json file.
Multiple settings files can be used by setting the SETTINGS_NAME environment variable.
The settings files are stored in the settings_files directory.

