import os


def get_files(path_batch, logger=None):
    """
    Haal de paden op van ALTO en METS bestanden uit een batchmap.

    Parameters
    ----------
    path_batch : str
        Pad naar batchmap
    logger : logging.Logger, optional

    Returns
    -------
    (list, list)
        Lijst met ALTO-bestanden, lijst met METS-bestanden
    """
    alto_files = []
    mets_files = []

    for dirpath, _, filenames in os.walk(path_batch):
        for filename in filenames:
            if filename.endswith("_00001_alto.xml"):
                alto_files.append(os.path.join(dirpath, filename))
            elif filename.endswith("_mets.xml"):
                mets_files.append(os.path.join(dirpath, filename))

    if logger:
        logger.info(f"Found {len(alto_files)} ALTO and {len(mets_files)} METS in {os.path.basename(path_batch)}")

    return alto_files, mets_files
