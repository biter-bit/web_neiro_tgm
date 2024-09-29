import logging
from logging import Logger


def create_logger(level_logger: str) -> Logger:
    """Создай логер"""
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] [%(threadName)s] [%(filename)s:%(lineno)d] - %(message)s"

    logging.basicConfig(level=getattr(logging, level_logger.upper()), format=log_format)

    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.DEBUG)

    return logger