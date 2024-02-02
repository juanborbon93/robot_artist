"""Reads settings from env file and implements a shared logger class"""

import logging
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
from __main__ import __file__ as module_name

module_name = Path(module_name).stem
LOG_DIR = Path(__file__).parent / f"logs/{module_name}/"
LOG_DIR.mkdir(exist_ok=True, parents=True)

load_dotenv()

assert "OPENAI_API_KEY" in os.environ, "API key not found in environment variables"

class SharedLogger:
    _logger = None

    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            cls._logger = logging.getLogger(module_name)  # Use module_name as the logger name
            cls._logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            # file handler
            log_file = LOG_DIR / (datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            # stream handler
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            # add handlers
            cls._logger.addHandler(file_handler)
            cls._logger.addHandler(stream_handler)
        return cls._logger
    

if __name__ == "__main__":
    logger = SharedLogger.get_logger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    print("Log file created at", f'{module_name}.log')