"""Logging utility for Hyperion"""

import logging
import sys
from ..config import config


def setup_logger(name: str = "hyperion") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if config.verbose else logging.WARNING)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger
