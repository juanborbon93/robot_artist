from project_init import SharedLogger

log = SharedLogger.get_logger()

import os

from third_party.octorest import OctoRest
from settings.settings_base import BaseSettingsModel
from pydantic import SecretStr

class OctoprintSettings(BaseSettingsModel):
    octoprint_api_key: SecretStr = SecretStr("YOUR_API_KEY")
    octoprint_base_url: str = "http://3dprinter/"


def upload_file(file_path):
    """Upload a file to OctoPrint."""
    SETTINGS : OctoprintSettings = OctoprintSettings.load()
    client = OctoRest(url=SETTINGS.octoprint_base_url, apikey=SETTINGS.octoprint_api_key.get_secret_value())
    response = client.upload(file_path, select=True, print=True)
    return response


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("--file", help="Path to the file to upload")
    args = parser.parse_args()
    upload_file(args.file)
