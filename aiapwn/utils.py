import logging
import sys
import json

def setup_logger(name="aiapwn", log_level="INFO", log_file=None):
    """
    Configures and returns a logger with both console and optional file handlers.

    Args:
        name (str): The name of the logger.
        log_level (str): The logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        log_file (str, optional): If provided, logs will also be written to this file.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (%(module)s:%(lineno)d) - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def pretty_format(data):
    """
    Returns a pretty-printed JSON string from a dictionary or list.
    If JSON formatting fails, returns the string representation of the data.

    Args:
        data (dict or list): The data to format.
    
    Returns:
        str: A neatly formatted JSON string.
    """
    try:
        return json.dumps(data, indent=4, sort_keys=True)
    except Exception:
        return str(data)