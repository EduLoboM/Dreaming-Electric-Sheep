import logging


def get_logger():
    """
    Returns a "dreaming_electric_sheep.sessions" logger.
    """
    logger = logging.getLogger("dreaming_electric_sheep.sessions")
    logger.setLevel(logging.INFO)
    return logger
