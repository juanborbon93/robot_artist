# Lenardo (robot artist)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

![demo animation](demo.gif)

## Description

The project aims to bring together art and technology by creating a drawing robot that can generate and execute drawings based on natural language input. The goal is to explore the exciting combination of creativity and automation, allowing users to witness their ideas come to life through the precision and elegance of robotics.

From a technical standpoint, the project does a couple of things:
- It utilizes audio prompts and speech-to-text transcription for user interaction, enabling an interaction that feels more natural (compared to a command line interface). 
- The script generates drawings (using OpenAI Dall-E) based on user input and traces the edges of the generated image. 
- It also scales the contours to fit a canvas and generates G-code instructions for the robot. 
- The project incorporates a robot simulation environment and executes the drawing using the generated G-code.

**WARNING: This project is intended for simulation purposes only. Operating real robot arms can be dangerous and should only be done by trained professionals in a controlled environment.**
**Please do not attempt to use this code to operate real robot arms without proper training and precautions.**

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)


### Installation

To install the required Python packages, follow these steps:

1. Open a terminal or command prompt.
2. Navigate to the project directory: `cd /path/to/project`.
3. Create a virtual environment: `python -m venv .venv`.
4. Activate the virtual environment:
    - On Windows: `venv\Scripts\activate`.
    - On macOS and Linux: `source .venv/bin/activate`.
5. Install the required packages: `pip3 install -r requirements.txt`.

To install the RoboDK simulation software, follow these steps:

1. Go to the [RoboDK website](https://robodk.com/).
2. Download the appropriate version for your operating system.
3. Run the installer and follow the on-screen instructions.

## Usage
- copy `.env.template` into `.env` and fill in the blank variables on the file
- Launch Robodk (`~/RoboDK/RoboDK-Start.sh`). No need to open the station as it is loaded automatically later.
- `cd` into the repository directory and run `source setup.sh` (this sets up your PYTHONPATH environment variable)
- run `python3 run_drawing_robot.py`

```
usage: run_drawing_robot.py [-h] [--human-prompt HUMAN_PROMPT]

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
7. Loading the robot simulation environment.
8. Creating a robot program using the generated G-code and executing it.

options:
  -h, --help            show this help message and exit
  --human-prompt HUMAN_PROMPT
                        Prompt for the drawing (will use audio prompt if not provided)
```

## License

This project is licensed under the [MIT License](LICENSE.txt).

