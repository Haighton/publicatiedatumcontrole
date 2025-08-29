import argparse
import os
import re
import numpy as np
import pandas as pd
from rapidfuzz import fuzz

from .utils import setup_logging
from .getfiles import get_files
from .extract import get_alto_data, extract_mets_data
from .scores import vpos_score, kde_gaussian
from .compare import compare_dates
from .report import plot_fig, generate_html_log


def main():
    parser = argparse.ArgumentParser(
        description="Controleer publicatiedata in krantenbatches (ALTO/METS/MODS)."
    )
    parser.add_argument("batches", nargs="+",
                        help="Een of meerdere batchmappen")
    parser.add_argument(
        "--log", default="logs/publicatiedatumcontrole.log",
        help="Logbestand (append)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Toon extra debug-informatie"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Score-drempel voor selectie van kandidaten (default: 0.8)"
    )
    parser.add_argument(
        "-o", "--output",
        default="html-reports",
        help="Hoofdmap voor rapporten (default: ./html-reports)"
    )

    args = parser.parse_args()

    logger = setup_logging(args.log, args.verbose)
    logger.info("Start publicatiedatumcontrole")

    months = {
        "januari": "01", "februari": "02", "maart": "03", "april": "04",
        "mei": "05", "juni": "06", "juli": "07", "augustus": "08",
        "september": "09", "oktober": "10", "november": "11", "december": "12"
    }

    for batch_count, path_batch in enumerate(args.batches, start=1):
        batch_id = os.path.basename(path_batch)
        logger.info(f"=== Start batch {batch_count}/{len(args.batches)}: {batch_id} ===")

        # ------------------ GET FILES ------------------
        alto_files, mets_files = get_files(path_batch, logger=logger)
        logger.info(f"Gevonden {len(alto_files)} ALTO en {len(mets_files)} METS bestanden")

        # ------------------ ALTO DATES ------------------
        filenames, alto_dates, content_x, content_y = [], [], [], []
        for idx, alto_file in enumerate(alto_files, start=1):
            logger.debug(f"Processing {os.path.basename(alto_file)} ({idx}/{len(alto_files)})")

            alto_content = get_alto_data(alto_file, logger=logger)
            for word_count, alto_word in enumerate(alto_content, start=1):
                if not alto_word or not alto_word[0]:
                    continue

                # negeer problematische woorden
                if alto_word[0].lower() in ["maar"]:
                    continue

                for month in months.keys():
                    fuzz_score = fuzz.ratio(alto_word[0].lower(), month)
                    if fuzz_score > 80:
                        try:
                            prev_content = re.sub(
                                r"[^\w\s]", "", alto_content[word_count - 2][0])
                            next_content = re.sub(
                                r"[^\w\s]", "", alto_content[word_count][0])

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

        # ------------------ METS DATES ------------------
        dict_mets_dates = extract_mets_data(mets_files, logger=logger)
        df_mets = pd.DataFrame(dict_mets_dates)
        df_mets["title_edition"] = df_mets["mets_title"] + \
            "_" + df_mets["mets_edition"]
        newspaper_titles = df_mets["title_edition"].unique().tolist()

        for current_title in newspaper_titles:
            logger.info(f"Analyse voor krant: {current_title}")

            df_current = pd.merge(df, df_mets, on="filename")
            df_current = df_current[df_current["title_edition"]
                                    == current_title]

            if len(df_current) == 0:
                logger.warning(f"Geen data gevonden voor {current_title}")
                continue

            # ------------------ SCORES ------------------
            df_current = kde_gaussian(df_current)
            df_current = vpos_score(df_current)
            col = df_current.loc[:, "kde_score":"vpos_score"]
            df_current["score"] = np.round(col.mean(axis=1), 2)

            df_filtered = df_current[df_current["score"] >= args.threshold]
            logger.info(
                f"Pagina's met mogelijke datum: {len(df_filtered)} "
                f"(threshold={args.threshold})"
            )

            alto_fnames = [os.path.basename(p).rstrip(
                "_00001_alto.xml") for p in alto_files]
            no_pd = set(alto_fnames) - set(df_filtered["filename"])
            if no_pd:
                perc = np.round(len(no_pd) / len(alto_files) * 100.0, 1)
                logger.warning(f"Geen publicatiedatum gevonden voor {len(no_pd)} bestanden ({perc}%)")

            # ------------------ COMPARE ------------------
            df_compared = compare_dates(df_filtered)
            df_errors = df_compared[(df_compared["distance_score"] > 0) &
                                    (df_compared["distance_score"] < 5)]

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

            logger.debug(f"df_compared sample:\n{df_compared[['filename','alto_date','mets_date','score','distance_score']].head(20)}")

    logger.info("Alle batches verwerkt.")
