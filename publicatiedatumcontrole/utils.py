import logging
import os
import sys


def setup_logging(logfile: str, verbose: bool = False, batch_id: str | None = None) -> logging.Logger:
    """
    Configure logging with file + console handler.
    - Central log: logs/publicatiedatumcontrole.log
    - Optional per-batch log: logs/<batch_id>.log
    - Console logging gaat naar stderr om tqdm progressbars niet te verstoren.
    """
    logger_name = f"publicatiedatumcontrole{'.' + batch_id if batch_id else ''}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        # Zorg dat logmap bestaat
        os.makedirs(os.path.dirname(logfile), exist_ok=True)

        # Centrale logfile
        fh = logging.FileHandler(logfile, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)

        # Console → stderr i.p.v. stdout
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.DEBUG if verbose else logging.INFO)

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        # Extra: batch-specifiek logfile
        if batch_id:
            batch_logfile = os.path.join(os.path.dirname(logfile), f"{batch_id}.log")
            bf = logging.FileHandler(batch_logfile, mode="a", encoding="utf-8")
            bf.setLevel(logging.DEBUG)
            bf.setFormatter(formatter)
            logger.addHandler(bf)

    return logger


def clean_ocr_number(text: str) -> str:
    """
    Corrigeer veelvoorkomende OCR fouten in cijfers.
    Voorbeelden:
    - 'i984' -> '1984'
    - 'l2'   -> '12'
    - 'O7'   -> '07'
    """
    return (text.replace("i", "1")
                .replace("I", "1")
                .replace("l", "1")
                .replace("o", "0")
                .replace("O", "0"))
