"""
This module provides a custom logger class for handling logging operations.

Classes:
    MyLogger: A custom logger class with methods for logging different severity levels.

Usage:
    To use this module, import the MyLogger class and create an instance with
    desired configurations. Then, use its methods (info, warning, error, debug) to log
    messages at different severity levels.

Example:
    # Import the module
    import my_logger

    # Create a logger instance
    logger = my_logger.MyLogger(
        name='example_logger', level=logging.INFO,
        log_format='%(asctime)s - %(name)s:%(lineno)d - [%(levelname)s] %(message)s',
        log_file='example.log'
    )

    # Log messages
    logger.info('This is an informational message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.debug('This is a debug message')
"""
import logging


class MyLogger:
    """
    Custom logger class for handling logging operations.
    """

    def __init__(
            self, name, level=logging.INFO,
            log_format='%(asctime)s - %(name)s:%(lineno)d - [%(levelname)s] %(message)s',
            log_file=None
        ):
        """
        Initialize the MyLogger instance.

        Parameters:
        name (str): The name of the logger.
        level (int): The logging level (default is logging.INFO).
        log_format (str): The format of log messages
            (default is '%(asctime)s - %(name)s:%(lineno)d - [%(levelname)s] %(message)s').
        log_file (str): The file path for logging (default is 'my_log.log').
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        formatter = logging.Formatter(log_format)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        if log_file is None:
            log_file = 'my_log.log'

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def info(self, message):
        """
        Log an informational message.

        Parameters:
        message (str): The message to log.
        """
        self.logger.info(message)

    def warning(self, message):
        """
        Log a warning message.

        Parameters:
        message (str): The message to log.
        """
        self.logger.warning(message)

    def error(self, message):
        """
        Log an error message.

        Parameters:
        message (str): The message to log.
        """
        self.logger.error(message)

    def debug(self, message):
        """
        Log a debug message.

        Parameters:
        message (str): The message to log.
        """
        self.logger.debug(message)
