import logging
import os
from pathlib import Path


def setup_logging(log_file: str = "logs/publicatiedatumcontrole.log", verbose: bool = False):
    """
    Configureer logging voor het hele project.
    Schrijft naar console én naar een logbestand (append).
    """
    # Zorg dat logmap bestaat
    Path(os.path.dirname(log_file) or ".").mkdir(parents=True, exist_ok=True)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger = logging.getLogger("publicatiedatumcontrole")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Dubbele handlers voorkomen bij herhaald aanroepen
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (append mode, altijd UTF-8)
    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG if verbose else logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger
