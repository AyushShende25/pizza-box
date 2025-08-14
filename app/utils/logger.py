import logging
import sys
import os
from logging.handlers import RotatingFileHandler


def setup_logger():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    # file_handler = logging.FileHandler(log_file)
    rotate_file_handler = RotatingFileHandler(
        log_file, maxBytes=1024 * 1024 * 5, backupCount=3
    )

    stream_handler.setFormatter(formatter)
    # file_handler.setFormatter(formatter)
    rotate_file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    # logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.addHandler(rotate_file_handler)

    return logger


logger = setup_logger()
