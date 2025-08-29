import os
import re
import pandas as pd
import numpy as np
from rapidfuzz import fuzz
from tqdm import tqdm

from .utils import setup_logging, clean_ocr_number
from .getfiles import get_files
from .extract import get_alto_data, extract_mets_data
from .scores import vpos_score, kde_gaussian
from .compare import compare_dates
from .report import plot_fig, generate_html_log, generate_xml_log


def process_batch(path_batch: str, args, months: dict, logfile: str, verbose: bool) -> tuple:
    """
    Process a single batch: extract dates, compare with METS,
    score candidates, and generate reports.

    Returns tuple:
        (batch_id, num_alto, num_mets, num_candidates, num_errors)
    """
    batch_id = os.path.basename(path_batch)
    logger = setup_logging(logfile, verbose, batch_id=batch_id)
    logger.info(f"=== Start batch: {batch_id} ===")

    # ------------------ GET FILES ------------------
    from .getfiles import get_files
    alto_files, mets_files = get_files(path_batch, logger=logger)

    filenames, alto_dates, content_x, content_y = [], [], [], []

    # ------------------ PROCESS ALTO FILES ------------------
    logger.info(f"Verwerken van {len(alto_files)} ALTO-bestanden...")
    for alto_file in tqdm(alto_files, desc=f"Processing ALTO ({batch_id})", unit="file", leave=False):
        alto_content = get_alto_data(alto_file, logger=logger)

        for word_count, alto_word in enumerate(alto_content, start=1):
            if not alto_word or not alto_word[0]:
                continue

            if alto_word[0].lower() in ["maar"]:  # ignore problematic words
                continue

            for month in months.keys():
                fuzz_score = fuzz.ratio(alto_word[0].lower(), month)
                if fuzz_score > 80:
                    try:
                        prev_content = clean_ocr_number(
                            re.sub(r"[^\w\s]", "",
                                   alto_content[word_count - 2][0])
                        )
                        next_content = clean_ocr_number(
                            re.sub(r"[^\w\s]", "", alto_content[word_count][0])
                        )

                        if (prev_content.isdigit() and len(prev_content) < 3 and
                                next_content.isdigit() and len(next_content) < 5):

                            filenames.append(os.path.basename(
                                alto_file).rstrip("_alto_00001.xml"))
                            alto_dates.append(f"{next_content}-{months[month]}-{prev_content.zfill(2)}")
                            content_x.append(alto_word[1][0])
                            content_y.append(alto_word[1][1])
                    except (ValueError, IndexError):
                        continue

    df = pd.DataFrame({
        "filename": filenames,
        "alto_date": alto_dates,
        "VPOS": content_x,
        "HPOS": content_y,
    })

    # ------------------ METS DATA ------------------
    dict_mets_dates = extract_mets_data(mets_files, logger=logger)
    df_mets = pd.DataFrame(dict_mets_dates)
    df_mets["title_edition"] = df_mets["mets_title"] + \
        "_" + df_mets["mets_edition"]
    newspaper_titles = df_mets["title_edition"].unique().tolist()

    total_candidates = 0
    total_errors = 0

    for current_title in newspaper_titles:
        logger.info(f"Analyse voor krant: {current_title}")

        df_current = pd.merge(df, df_mets, on="filename")
        df_current = df_current[df_current["title_edition"] == current_title]

        if len(df_current) == 0:
            logger.warning(f"Geen data gevonden voor {current_title}")
            continue

        # ------------------ SCORES ------------------
        df_current = kde_gaussian(df_current)
        df_current = vpos_score(df_current)
        col = df_current.loc[:, "kde_score":"vpos_score"]
        df_current["score"] = np.round(col.mean(axis=1), 2)

        df_filtered = df_current[df_current["score"] >= args.threshold]
        logger.info(f"Pagina's met mogelijke datum: {len(df_filtered)} (threshold={args.threshold})")

        alto_fnames = [os.path.basename(p).rstrip(
            "_00001_alto.xml") for p in alto_files]
        no_pd = set(alto_fnames) - set(df_filtered["filename"])
        if no_pd:
            perc = np.round(len(no_pd) / len(alto_files) * 100.0, 1)
            logger.warning(f"Geen publicatiedatum gevonden voor {len(no_pd)} bestanden ({perc}%)")

        # ------------------ COMPARE ------------------
        df_compared = compare_dates(df_filtered)
        df_errors = df_compared[(df_compared["distance_score"] > 0) &
                                (df_compared["distance_score"] <= args.date_tolerance)]

        total_candidates += len(df_filtered)
        total_errors += len(df_errors)

        if len(df_errors) > 0:
            log_folder = os.path.join(args.output, batch_id)
            os.makedirs(os.path.join(log_folder, "images"), exist_ok=True)

            plot_fig(df_errors, path_batch, current_title,
                     log_folder, df_current, logger=logger)
            generate_html_log(
                df_errors,
                path_batch,
                current_title,
                log_folder,
                logger=logger,
                threshold=args.threshold
            )

            logger.error(f"{len(df_errors)} mogelijke fouten gevonden in {current_title}")
        else:
            logger.info(f"Geen fouten gevonden voor {current_title}")

    return (batch_id, len(alto_files), len(mets_files), total_candidates, total_errors)
