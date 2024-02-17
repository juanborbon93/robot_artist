"""
Implements BaseSettingsModel, a base class for settings models.
this class can be imported into other modules to create settings models.
by calling the load method, the settings are loaded from a json file.
multiple settings files can be used by setting the SETTINGS_NAME environment variable.
the settings files are stored in the settings_files directory.
"""
from project_init import SharedLogger, LOG_DIR

log = SharedLogger.get_logger()

from pydantic import BaseModel
from pydantic.fields import PydanticUndefined
import json
from pathlib import Path
import os

SETTINGS_DIR = Path(__file__).parent
SETTINGS_DIR.mkdir(exist_ok=True)

class BaseSettingsModel(BaseModel):

    @classmethod
    def _ensure_defaults(cls):
        """make sure that all of the model fields have a default value.
        This is to ensure that the settings file is always valid."""
        non_defualt_fields = []
        for field_name, field_info in cls.model_fields.items():
            if field_info.default == PydanticUndefined:
                non_defualt_fields.append(field_name)
        if non_defualt_fields:
            raise ValueError(f"Fields {non_defualt_fields} must have a default value")
        
    @classmethod
    def settings_file(cls)->Path:
        """return the path to the settings file"""
        name = os.environ.get("SETTINGS_NAME")
        if name is None:
            log.info("environment variable SETTINGS_NAME not set, using default settings")
            name = "default"
            os.environ["SETTINGS_NAME"] = name
        settings_file =  SETTINGS_DIR / f"settings_files/{name}.json"
        if not settings_file.exists():
            # make new settings file
            cls._ensure_defaults()
            default_settings_json = cls().model_dump_json(indent=4)
            with open(settings_file, "w") as f:
                f.write(default_settings_json)
        return settings_file

    @classmethod
    def load(cls):

        """load the settings from the settings file"""
        
        if cls.__name__ == "BaseSettingsModel":
            raise Exception("BaseSettingsModel cannot be instantiated with the load method. Use a subclass instead.")
        
        cls._ensure_defaults()
        settings_file = cls.settings_file()
        
        with open(settings_file, "r") as f:
            settings_dict = json.load(f)
        if cls.__name__ in settings_dict:
            log.info(f"loading settings for {cls.__name__} from {settings_file}")
            return cls.model_validate(settings_dict[cls.__name__])
        else:
            # add the settings to the file
            default_instance = cls()
            settings_dict[cls.__name__] = default_instance.model_dump(mode="json")
            with open(settings_file, "w") as f:
                json.dump(settings_dict, f, indent=4)
            return default_instance
        

