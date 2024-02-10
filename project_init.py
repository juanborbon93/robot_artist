"""Reads settings from env file and implements a shared logger class"""

import logging
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
try:
    from __main__ import __file__ as module_name
except ImportError:
    module_name = "unknown_module"
import inspect

module_name = Path(module_name).stem
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

LOG_DIR = Path(__file__).parent / f"logs/{module_name}/{timestamp}/"
LOG_DIR.mkdir(exist_ok=True, parents=True)

load_dotenv()

def get_log_level():
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    assert log_level in log_level_map, f"Invalid log level: {log_level}"
    return log_level_map[log_level]

assert "OPENAI_API_KEY" in os.environ, "API key not found in environment variables"

class SharedLogger:
    _file_handler = None
    _stream_handler = None

    @classmethod
    def get_logger(cls):
        """Returns a shared logger instance. If it doesn't exist, creates one."""
        calling_module_name = Path(inspect.stack()[1].filename).name
        logger = logging.getLogger(calling_module_name)
        logger.setLevel(get_log_level())
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
    

if __name__ == "__main__":
    logger = SharedLogger.get_logger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    print("Log file created at", f'{module_name}.log')