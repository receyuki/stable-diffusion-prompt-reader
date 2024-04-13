__author__ = "receyuki"
__filename__ = "logger.py"
__copyright__ = "Copyright 2024"
__email__ = "receyuki@gmail.com"

import logging


class Logger:
    _loggers = {}

    def __new__(cls, name, level=None):
        # Check if logger with given name already exists and return it
        if cls._loggers.get(name):
            return cls._loggers[name]
        logger = logging.getLogger(name)
        if level:
            logger.setLevel(cls.get_log_level(level))
        # cls._configure_logger(logger)
        cls._loggers[name] = logger
        return logger

    @staticmethod
    def _configure_logger(logger):
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        # Create a stream handler for console output
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # Create a file handler for file output
        # file_handler = logging.FileHandler(f"{logger.name}.log")
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

    @staticmethod
    def get_log_level(level_name):
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARN": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        return levels.get(level_name.upper(), logging.INFO)

    @classmethod
    def configure_global_logger(cls, level="INFO"):
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        level_value = cls.get_log_level(level)

        # Configure the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level_value)

        # Add a stream handler to the root logger
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

        # Remove any other handlers from root_logger to prevent duplication
        for handler in root_logger.handlers[:]:
            if not isinstance(handler, logging.StreamHandler):
                root_logger.removeHandler(handler)

        # Add a file handler to the root logger
        # file_handler = logging.FileHandler('app.log')
        # file_handler.setFormatter(formatter)
        # root_logger.addHandler(file_handler)
