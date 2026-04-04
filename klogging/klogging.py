from __future__ import annotations

import logging
from typing import Optional

from kira.core.kobject import KObject
from kira.kdata.karray import KArray
from kira.kdata.kdata import KDataValue, KData
from kira.kdata.kliteral import KLiteral
from kira.kdata.ktable import KTable


def setup_logging(level=logging.INFO, log_file: Optional[str] = None):
    """Configure logging for the Kira application."""
    logger = logging.getLogger("kira")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def log_kdata_value(value: KDataValue, logger: Optional[logging.Logger] = None):
    logger = logger if logger else logging.getLogger("kira")
    match value:
        case KLiteral():
            logger.info(f"KData value: {value}")
        case KArray():
            logger.info(f"KData value: {value}")
            # logger.info(f"- Array: {value.value}")
        case KTable():
            logger.info(f"KData value: {value}")
            logger.info(f"- Table: {value.value}")
        case _:
            logger.info(f"KData value: {value}")


def log_kobject(obj: KObject, logger: Optional[logging.Logger] = None):
    logger = logger if logger else logging.getLogger("kira")
    if isinstance(obj, KData):
        msg = f"KData( name: {obj.name}, type: {obj.type}, value: {obj.value}"
        if obj.error:
            msg += f", error: {obj.error}"
        msg += ")"
        logger.info(msg)
    else:
        logger.info(f"{obj}")
