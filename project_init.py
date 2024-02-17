"""Reads settings from env file and implements a shared logger class"""

import logging
import os
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser, RawDescriptionHelpFormatter
try:
    from __main__ import __file__ as module_name
except ImportError:
    module_name = "unknown_module"
import inspect

module_name = Path(module_name).stem
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

LOG_DIR = Path(__file__).parent / f"logs/{module_name}/{timestamp}/"
LOG_DIR.mkdir(exist_ok=True, parents=True)

class SharedLogger:
    _file_handler = None
    _stream_handler = None

    @classmethod
    def get_logger(cls):
        """Returns a shared logger instance. If it doesn't exist, creates one."""
        calling_module_name = Path(inspect.stack()[1].filename).name
        logger = logging.getLogger(calling_module_name)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        if cls._file_handler is None:
            # file handler
            log_file = LOG_DIR / "log.txt"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            cls._file_handler = file_handler
        if cls._stream_handler is None:
            # stream handler
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            cls._stream_handler = stream_handler

        # add handlers
        logger.addHandler(cls._file_handler)
        logger.addHandler(cls._stream_handler)
        return logger
    
def get_log_level(log_level:str="INFO"):
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    assert log_level in log_level_map, f"Invalid log level: {log_level}"
    return log_level_map[log_level]

class ArgParser:
    """A class to parse command line arguments"""
    def __init__(self, description=""):
        self.parser = ArgumentParser(description=description, formatter_class=RawDescriptionHelpFormatter)
        # set default parameters for all scripts
        self.parser.add_argument("--settings-name", default=os.environ.get("SETTINGS_NAME","default"), help="Set the settings name")
        self.parser.add_argument("--log-level", default="INFO", help="Set the log level")
        
    def add_argument(self, *args, **kwargs):
        self.parser.add_argument(*args, **kwargs)
    
    def parse_args(self):
        args =  self.parser.parse_args()
        # set log level for all loggers
        all_loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for logger in all_loggers:
            logger.setLevel(get_log_level(args.log_level))
        # set the settings name environment variable
        os.environ["SETTINGS_NAME"] = args.settings_name
        return args

if __name__ == "__main__":
    logger = SharedLogger.get_logger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    print("Log file created at", f"{module_name}.log")
