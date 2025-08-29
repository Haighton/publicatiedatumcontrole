import os
import logging
from typing import List, Dict, Any
from lxml import etree


def get_alto_data(alto_file: str, logger=None) -> list:
    """Extract //String/@CONTENT attributes from an ALTO XML file."""
    alto_file_content = []
    skipped = 0
    with open(alto_file, "rb") as alto:
        context = etree.iterparse(alto, events=("end",))
        for event, elem in context:
            if etree.QName(elem.tag).localname == "String":
                try:
                    alto_file_content.append([
                        elem.get("CONTENT"),
                        (int(elem.get("VPOS")), int(elem.get("HPOS")))
                    ])
                except (TypeError, ValueError):
                    skipped += 1
            elem.clear()
    if skipped and logger:
        logger.debug(f"Skipped {skipped} invalid String elements in {alto_file}")
    return alto_file_content


def extract_mets_data(mets_files: List[str], logger: logging.Logger | None = None) -> Dict[str, List[str]]:
    """
    Extract publication date, title, and edition data from a list of METS files.

    Args:
        mets_files (list[str]): List of METS XML file paths.
        logger (logging.Logger, optional): Logger for reporting.

    Returns:
        dict: Dictionary with keys 'filename', 'mets_date', 'mets_title', 'mets_edition'.
    """
    dict_mets_dates: Dict[str, List[str]] = {"filename": [], "mets_date": [], "mets_title": [], "mets_edition": []}

    for count, mets_file in enumerate(mets_files, start=1):
        try:
            with open(mets_file, "rb") as mets:
                context = etree.iterparse(mets, events=("start", "end"))
                np_titles: List[str] = []
                np_dates: List[str] = []
                np_editions: List[str] = []

                for _, elem in context:
                    if elem.tag == "{http://www.loc.gov/mods/v3}mods":
                        for elem_child in elem:
                            if elem_child.tag.endswith("titleInfo"):
                                for c in elem_child:
                                    if c.tag.endswith("title") and c.text:
                                        np_titles.append(c.text)
                            elif elem_child.tag.endswith("part"):
                                for c in elem_child:
                                    if c.tag.endswith("date") and c.text:
                                        np_dates.append(c.text)
                            elif elem_child.tag.endswith("originInfo"):
                                for c in elem_child:
                                    if c.tag.endswith("edition") and c.text:
                                        np_editions.append(c.text)

                dict_mets_dates["filename"].append(
                    os.path.basename(mets_file).strip("_mets.xml"))
                dict_mets_dates["mets_date"].append(
                    np_dates[0] if np_dates else "")
                dict_mets_dates["mets_title"].append(
                    np_titles[0] if np_titles else "")
                dict_mets_dates["mets_edition"].append(
                    np_editions[0] if np_editions else "")

        except Exception as e:
            if logger:
                logger.error(f"Could not extract data from METS file {mets_file}: {e}")

    return dict_mets_dates
