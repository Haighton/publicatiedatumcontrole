import argparse
import os
import sys
import yaml
import csv
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from tqdm import tqdm

from .utils import setup_logging
from .runner import process_batch


def load_config(config_path: str = "config.yaml") -> dict:
    """Load YAML config file if present."""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def determine_workers(num_batches: int) -> int:
    """
    Kies automatisch het aantal workers op basis van batch count en CPU cores.
    - Kleine batches: gebruik alle cores (min 2).
    - Middelgrote: gebruik min(batches, cores-1).
    - Grote hoeveelheid: cap op 8.
    """
    cores = os.cpu_count() or 2

    if num_batches <= 2:
        return max(2, cores)

    if num_batches <= cores:
        return max(2, min(num_batches, cores - 1))

    return min(8, cores)


def main():
    parser = argparse.ArgumentParser(
        description="Controleer publicatiedata in krantenbatches (ALTO/METS/MODS)."
    )
    parser.add_argument("batches", nargs="+",
                        help="Een of meerdere batchmappen")
    parser.add_argument("--log", default=None, help="Logbestand (append)")
    parser.add_argument("--verbose", action="store_true",
                        help="Toon extra debug-informatie")
    parser.add_argument("--threshold", type=float,
                        default=None, help="Score-drempel (default 0.8)")
    parser.add_argument("-o", "--output", default=None,
                        help="Hoofdmap voor rapporten")
    parser.add_argument("--xml", action="store_true",
                        help="Genereer ook XML-rapporten naast HTML")
    parser.add_argument("--date-tolerance", type=int, default=None,
                        help="Maximaal toegestaan verschil (dag+maand+jaar) tussen ALTO en METS (default 2)")

    args = parser.parse_args()

    # ------------------ CONFIG ------------------
    config = load_config("config.yaml")
    logfile = args.log or config.get("log", "logs/publicatiedatumcontrole.log")
    verbose = args.verbose or config.get("verbose", False)
    threshold = args.threshold or config.get("threshold", 0.8)
    output_dir = args.output or config.get("output", "html-reports")
    xml_output = args.xml or config.get("xml", False)
    date_tolerance = args.date_tolerance or config.get("date_tolerance", 2)

    # schrijf terug naar args zodat process_batch deze kan gebruiken
    args.log = logfile
    args.verbose = verbose
    args.threshold = threshold
    args.output = output_dir
    args.xml = xml_output
    args.date_tolerance = date_tolerance

    logger = setup_logging(logfile, verbose)
    logger.info("Start publicatiedatumcontrole (parallel mode)")
    logger.info(f"Centrale log: {logfile}")
    logger.info("Elke batch schrijft daarnaast naar eigen logfile in dezelfde map.")

    months = {
        "januari": "01", "februari": "02", "maart": "03", "april": "04",
        "mei": "05", "juni": "06", "juli": "07", "augustus": "08",
        "september": "09", "oktober": "10", "november": "11", "december": "12"
    }

    num_batches = len(args.batches)
    max_workers = determine_workers(num_batches)
    logger.info(f"Gebruik {max_workers} parallelle workers voor {num_batches} batches")

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_batch, path, args, months, logfile, verbose): path
            for path in args.batches
        }
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Processing batches"):
            try:
                results.append(fut.result())
            except Exception as e:
                logger.error(f"Batch {futures[fut]} failed: {e}")

    total_alto = sum(r[1] for r in results)
    total_mets = sum(r[2] for r in results)
    total_candidates = sum(r[3] for r in results)
    total_errors = sum(r[4] for r in results)

    logger.info("=== Run summary ===")
    logger.info(f"Processed {len(results)} batches")
    logger.info(f"Total ALTO files: {total_alto}, METS files: {total_mets}")
    logger.info(f"Total candidates (above threshold): {total_candidates}")
    logger.info(f"Total potential errors: {total_errors}")
    logger.info("Alle batches verwerkt ✅")

    # ------------------ CSV SAMENVATTING ------------------
    reports_dir = os.path.abspath("reports")
    os.makedirs(reports_dir, exist_ok=True)
    csv_name = os.path.join(reports_dir, f"run_summary_{time.strftime('%Y%m%d_%H%M')}.csv")

    with open(csv_name, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["batch_id", "alto_files", "mets_files", "candidates", "errors"])
        for r in results:
            writer.writerow(r)  # (batch_id, alto, mets, candidates, errors)
        writer.writerow([])
        writer.writerow(["TOTAL", total_alto, total_mets, total_candidates, total_errors])

    logger.info(f"Samenvattings-CSV opgeslagen: {csv_name}")

    if total_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)
