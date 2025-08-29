import os
import logging
from typing import List, Tuple


def get_files(path_batch: str, logger: logging.Logger | None = None) -> Tuple[List[str], List[str]]:
    """
    Get ALTO and METS files from a batch folder.

    Args:
        path_batch (str): Path to the batch directory.
        logger (logging.Logger, optional): Logger for reporting.

    Returns:
        tuple: (list of ALTO file paths, list of METS file paths)
    """
    alto_files: List[str] = []
    mets_files: List[str] = []
    try:
        for dirpath, _, filenames in os.walk(path_batch):
            for filename in filenames:
                if filename.endswith("_00001_alto.xml"):
                    alto_files.append(os.path.join(dirpath, filename))
                elif filename.endswith("_mets.xml"):
                    mets_files.append(os.path.join(dirpath, filename))

        if logger:
            logger.info(f"Found {len(alto_files)} ALTO and {len(mets_files)} METS in {os.path.basename(path_batch)}")

    except Exception as e:
        if logger:
            logger.error(f"Error scanning batch folder {path_batch}: {e}")
        return [], []

    return alto_files, mets_files
